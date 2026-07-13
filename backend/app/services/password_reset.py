"""Password reset service: issue single-use tokens and apply new passwords.

The plaintext token is only ever put in the reset link (e-mail); the database
stores just its SHA-256 hash. Resetting a password stamps
``password_changed_at``, which invalidates every access token issued before it.
"""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import send_email
from app.core.exceptions import ValidationAppError
from app.core.security import hash_password
from app.models.enums import AuditAction
from app.models.security import PasswordResetToken
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.audit import AuditService, RequestContext


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class PasswordResetService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.users = UserRepository(db)
        self.audit = AuditService(db, self.ctx)

    def request_reset(self, email: str) -> str | None:
        """Create a reset token and deliver the link. Returns the plaintext
        token (for non-production surfacing) or ``None`` if no active user."""
        user = self.users.get_by(email=email)
        if not user or not user.is_active:
            return None

        # Invalidate any previous unused tokens so only the newest link works.
        self.db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )

        token = secrets.token_urlsafe(32)
        self.db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=_hash_token(token),
                expires_at=datetime.now(UTC)
                + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
            )
        )
        self.audit.log(
            AuditAction.UPDATE,
            entity="User",
            entity_id=user.id,
            field="password_reset_requested",
        )
        self.db.commit()
        self._deliver(user, token)
        return token

    def _deliver(self, user: User, token: str) -> None:
        reset_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/reset-password?token={token}"
        minutes = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        body = (
            f"Ola {user.full_name},\n\n"
            "Recebemos uma solicitacao para redefinir a senha da sua conta.\n"
            f"Use o link abaixo (valido por {minutes} minutos):\n\n"
            f"{reset_url}\n\n"
            "Se voce nao fez esta solicitacao, ignore este e-mail; "
            "sua senha permanece inalterada."
        )
        send_email(user.email, "Redefinicao de senha - Sistema de Estoque", body)

    def reset(self, token: str, new_password: str) -> None:
        record = self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == _hash_token(token)
            )
        ).scalar_one_or_none()

        now = datetime.now(UTC)
        if not record or record.used_at is not None:
            raise ValidationAppError("Token invalido ou ja utilizado")
        if _as_utc(record.expires_at) < now:
            raise ValidationAppError("Token expirado. Solicite um novo.")

        user = self.users.get(record.user_id)
        if not user or not user.is_active:
            raise ValidationAppError("Usuario invalido")

        user.hashed_password = hash_password(new_password)
        user.password_changed_at = now
        # A successful reset also frees a locked-out account.
        user.failed_login_attempts = 0
        user.locked_until = None
        record.used_at = now
        self.audit.log(
            AuditAction.UPDATE, entity="User", entity_id=user.id, field="password_reset"
        )
        self.db.commit()

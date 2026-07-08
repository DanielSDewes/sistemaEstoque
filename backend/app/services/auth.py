"""Authentication service: credential verification, lockout and token issuance."""
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.enums import AuditAction
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginResponse
from app.schemas.user import UserRead
from app.services.audit import AuditService, RequestContext
from app.services.token_revocation import is_revoked, revoke


class AuthService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.users = UserRepository(db)

    def authenticate(self, login: str, password: str) -> User:
        user = self.users.get_by_login(login)
        if not user:
            raise AuthenticationError("Usuario ou senha invalidos")

        now = datetime.now(UTC)
        locked_until = user.locked_until
        if locked_until is not None:
            # Compare timezone-aware; treat naive DB values as UTC.
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=UTC)
            if locked_until > now:
                raise AuthenticationError(
                    "Conta temporariamente bloqueada por excesso de tentativas. "
                    "Tente novamente mais tarde."
                )

        if not verify_password(password, user.hashed_password):
            self._register_failure(user)
            raise AuthenticationError("Usuario ou senha invalidos")

        if not user.is_active:
            raise AuthenticationError("Usuario inativo")

        # Success: clear any failure state.
        if user.failed_login_attempts or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            self.db.commit()
        return user

    def _register_failure(self, user: User) -> None:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
            user.locked_until = datetime.now(UTC) + timedelta(
                minutes=settings.LOGIN_LOCKOUT_MINUTES
            )
            AuditService(self.db, RequestContext(user=user, **self._meta())).log(
                AuditAction.UPDATE,
                entity="User",
                entity_id=user.id,
                field="locked_until",
                new_value="conta bloqueada",
            )
        self.db.commit()

    def login(self, login: str, password: str) -> LoginResponse:
        user = self.authenticate(login, password)
        AuditService(self.db, RequestContext(user=user, **self._meta())).log(
            AuditAction.LOGIN, entity="User", entity_id=user.id
        )
        self.db.commit()
        return LoginResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            user=UserRead.model_validate(user),
        )

    def refresh(self, refresh_token: str) -> dict[str, str]:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Refresh token invalido")
        if is_revoked(self.db, payload.get("jti")):
            raise AuthenticationError("Refresh token expirado ou ja utilizado")
        user = self.users.get(int(payload["sub"]))
        if not user or not user.is_active:
            raise AuthenticationError("Usuario invalido")

        # Rotation: invalidate the presented refresh token so it cannot be reused.
        revoke(self.db, payload, user.id)
        self.db.commit()
        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }

    def logout(self, user: User, access_claims: dict | None = None) -> None:
        if access_claims:
            revoke(self.db, access_claims, user.id)
        AuditService(self.db, self.ctx).log(
            AuditAction.LOGOUT, entity="User", entity_id=user.id
        )
        self.db.commit()

    def _meta(self) -> dict[str, str | None]:
        return {"ip_address": self.ctx.ip_address, "user_agent": self.ctx.user_agent}

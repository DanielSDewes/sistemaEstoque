"""Shared FastAPI dependencies: auth, current user, permission guards, context."""
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.net import client_ip
from app.core.pagination import PageParams
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.audit import RequestContext
from app.services.token_revocation import is_revoked

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


def get_access_claims(token: str | None = Depends(oauth2_scheme)) -> dict:
    """Decode the bearer access token, validating type but not the denylist."""
    if not token:
        raise AuthenticationError("Credenciais nao fornecidas")
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise AuthenticationError("Token invalido ou expirado")
    return payload


def get_current_user(
    payload: dict = Depends(get_access_claims), db: Session = Depends(get_db)
) -> User:
    if is_revoked(db, payload.get("jti")):
        raise AuthenticationError("Sessao encerrada. Faca login novamente.")
    user = UserRepository(db).get(int(payload["sub"]))
    if not user or not user.is_active:
        raise AuthenticationError("Usuario invalido ou inativo")
    # Tokens issued before the last password change are no longer valid (a
    # 1s leeway absorbs the JWT `iat` truncation to whole seconds).
    if user.password_changed_at is not None:
        iat = payload.get("iat")
        if iat is not None:
            issued_at = datetime.fromtimestamp(int(iat), tz=UTC)
            changed = user.password_changed_at
            if changed.tzinfo is None:
                changed = changed.replace(tzinfo=UTC)
            if issued_at + timedelta(seconds=1) < changed:
                raise AuthenticationError(
                    "Sessao encerrada apos alteracao de senha. Faca login novamente."
                )
    return user


def get_request_context(
    request: Request, user: User = Depends(get_current_user)
) -> RequestContext:
    return RequestContext(
        user=user,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


def require_permission(code: str) -> Callable[..., User]:
    """Dependency factory guarding an endpoint behind a permission code."""

    def guard(user: User = Depends(get_current_user)) -> User:
        if not user.has_permission(code):
            raise PermissionDeniedError(f"Permissao necessaria: {code}")
        return user

    return guard


def get_page_params(
    page: int = 1, size: int = 20, sort_by: str | None = None, sort_dir: str = "asc"
) -> PageParams:
    return PageParams(page=page, size=size, sort_by=sort_by, sort_dir=sort_dir)

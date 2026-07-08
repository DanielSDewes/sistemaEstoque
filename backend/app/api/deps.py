"""Shared FastAPI dependencies: auth, current user, permission guards, context."""
from collections.abc import Callable

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, PermissionDeniedError
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
    return user


def get_request_context(
    request: Request, user: User = Depends(get_current_user)
) -> RequestContext:
    client_ip = request.client.host if request.client else None
    forwarded = request.headers.get("x-forwarded-for")
    return RequestContext(
        user=user,
        ip_address=forwarded.split(",")[0].strip() if forwarded else client_ip,
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

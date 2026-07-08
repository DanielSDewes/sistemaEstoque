"""Authentication endpoints."""
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_access_claims, get_current_user, get_request_context
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.ratelimit import is_rate_limited
from app.models.user import User
from app.schemas.auth import LoginResponse, RefreshRequest, Token
from app.schemas.common import Message
from app.schemas.user import UserRead
from app.services.audit import RequestContext
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


class TooManyRequestsError(AppError):
    status_code = 429
    default_message = "Muitas tentativas. Aguarde e tente novamente."


def _ctx(request: Request) -> RequestContext:
    client_ip = request.client.host if request.client else None
    forwarded = request.headers.get("x-forwarded-for")
    return RequestContext(
        ip_address=forwarded.split(",")[0].strip() if forwarded else client_ip,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/login", response_model=LoginResponse, summary="Autenticar e obter tokens")
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> LoginResponse:
    """OAuth2 password flow. ``username`` accepts username or email."""
    ctx = _ctx(request)
    key = f"login:{ctx.ip_address}:{form.username.lower()}"
    if is_rate_limited(
        key, settings.LOGIN_RATE_LIMIT_MAX, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    ):
        raise TooManyRequestsError()
    return AuthService(db, ctx).login(form.username, form.password)


@router.post("/refresh", response_model=Token, summary="Renovar access token")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    return Token(**AuthService(db).refresh(payload.refresh_token))


@router.post("/logout", response_model=Message, summary="Encerrar sessao (revoga o token)")
def logout(
    claims: dict = Depends(get_access_claims),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> Message:
    AuthService(db, ctx).logout(ctx.user, access_claims=claims)
    return Message(detail="Logout registrado e token revogado")


@router.get("/me", response_model=UserRead, summary="Dados do usuario autenticado")
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)

"""User, Role and Permission management endpoints."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_page_params,
    get_request_context,
    require_permission,
)
from app.core.database import get_db
from app.core.pagination import Page, PageParams
from app.models.user import User
from app.repositories.user import PermissionRepository
from app.schemas.common import Message
from app.schemas.user import (
    PasswordChange,
    PermissionRead,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services.audit import RequestContext
from app.services.user import RoleService, UserService

router = APIRouter(tags=["Usuarios e Perfis"])


# --- Permissions catalog ---
@router.get("/permissions", response_model=list[PermissionRead], summary="Listar permissoes")
def list_permissions(
    db: Session = Depends(get_db),
    _=Depends(require_permission("role:view")),
) -> list[PermissionRead]:
    perms = PermissionRepository(db).list()
    return [PermissionRead.model_validate(p) for p in perms]


# --- Roles ---
@router.get("/roles", response_model=Page[RoleRead], summary="Listar perfis")
def list_roles(
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("role:view")),
) -> Page[RoleRead]:
    return RoleService(db).list(params)


@router.post(
    "/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED, summary="Criar perfil"
)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("role:create")),
) -> RoleRead:
    return RoleService(db, ctx).create(payload)


@router.put("/roles/{role_id}", response_model=RoleRead, summary="Atualizar perfil")
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("role:update")),
) -> RoleRead:
    return RoleService(db, ctx).update(role_id, payload)


# --- Users ---
@router.get("/users", response_model=Page[UserRead], summary="Listar usuarios")
def list_users(
    q: str | None = Query(None),
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("user:view")),
) -> Page[UserRead]:
    return UserService(db).list(params, term=q)


@router.post(
    "/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Criar usuario"
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("user:create")),
) -> UserRead:
    return UserService(db, ctx).create(payload)


@router.put("/users/{user_id}", response_model=UserRead, summary="Atualizar usuario")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("user:update")),
) -> UserRead:
    return UserService(db, ctx).update(user_id, payload)


@router.delete("/users/{user_id}", response_model=Message, summary="Inativar usuario")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("user:delete")),
) -> Message:
    UserService(db, ctx).deactivate(user_id)
    return Message(detail="Usuario inativado")


@router.post("/users/me/change-password", response_model=Message, summary="Alterar propria senha")
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    current_user: User = Depends(get_current_user),
) -> Message:
    UserService(db, ctx).change_password(current_user, payload)
    return Message(detail="Senha alterada com sucesso")

"""User and Role management services."""
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.core.pagination import Page, PageParams
from app.core.security import hash_password, verify_password
from app.models.enums import AuditAction
from app.models.user import Role, User
from app.repositories.user import PermissionRepository, RoleRepository, UserRepository
from app.schemas.user import (
    PasswordChange,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services.audit import AuditService, RequestContext


class UserService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = UserRepository(db)
        self.roles = RoleRepository(db)
        self.audit = AuditService(db, self.ctx)

    def list(self, params: PageParams, term: str | None = None) -> Page[UserRead]:
        items, total = self.repo.paginate(params, self.repo.search(term))
        return Page.create([UserRead.model_validate(u) for u in items], total, params)

    def get(self, user_id: int) -> UserRead:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError("Usuario nao encontrado")
        return UserRead.model_validate(user)

    def create(self, data: UserCreate) -> UserRead:
        if self.repo.get_by(email=data.email):
            raise ConflictError("Email ja cadastrado")
        if self.repo.get_by(username=data.username):
            raise ConflictError("Nome de usuario ja cadastrado")
        if not self.roles.get(data.role_id):
            raise NotFoundError("Perfil (role) nao encontrado")

        user = User(
            full_name=data.full_name,
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            is_active=data.is_active,
            notes=data.notes,
            role_id=data.role_id,
        )
        self.repo.add(user)
        self.audit.log(AuditAction.CREATE, entity="User", entity_id=user.id, new_value=user.email)
        self.db.commit()
        self.db.refresh(user)
        return UserRead.model_validate(user)

    def update(self, user_id: int, data: UserUpdate) -> UserRead:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError("Usuario nao encontrado")
        changes = data.model_dump(exclude_unset=True)
        before = {k: getattr(user, k) for k in changes}
        for key, value in changes.items():
            setattr(user, key, value)
        self.db.flush()
        self.audit.log_diff(AuditAction.UPDATE, "User", user.id, before, changes)
        self.db.commit()
        self.db.refresh(user)
        return UserRead.model_validate(user)

    def change_password(self, user: User, data: PasswordChange) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise ValidationAppError("Senha atual incorreta")
        user.hashed_password = hash_password(data.new_password)
        self.db.flush()
        self.audit.log(AuditAction.UPDATE, entity="User", entity_id=user.id, field="password")
        self.db.commit()

    def deactivate(self, user_id: int) -> None:
        user = self.repo.get(user_id)
        if not user:
            raise NotFoundError("Usuario nao encontrado")
        user.is_active = False
        self.audit.log(
            AuditAction.UPDATE, entity="User", entity_id=user.id, field="is_active", new_value=False
        )
        self.db.commit()


class RoleService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = RoleRepository(db)
        self.perms = PermissionRepository(db)
        self.audit = AuditService(db, self.ctx)

    def list(self, params: PageParams) -> Page[RoleRead]:
        items, total = self.repo.paginate(params)
        return Page.create([RoleRead.model_validate(r) for r in items], total, params)

    def get(self, role_id: int) -> RoleRead:
        role = self.repo.get(role_id)
        if not role:
            raise NotFoundError("Perfil nao encontrado")
        return RoleRead.model_validate(role)

    def create(self, data: RoleCreate) -> RoleRead:
        if self.repo.get_by_name(data.name):
            raise ConflictError("Ja existe um perfil com este nome")
        role = Role(name=data.name, description=data.description)
        role.permissions = self.perms.get_by_codes(data.permission_ids)
        self.repo.add(role)
        self.audit.log(AuditAction.CREATE, entity="Role", entity_id=role.id, new_value=role.name)
        self.db.commit()
        self.db.refresh(role)
        return RoleRead.model_validate(role)

    def update(self, role_id: int, data: RoleUpdate) -> RoleRead:
        role = self.repo.get(role_id)
        if not role:
            raise NotFoundError("Perfil nao encontrado")
        if role.is_system and data.name and data.name != role.name:
            raise ConflictError("Perfis de sistema nao podem ser renomeados")
        if data.name is not None:
            role.name = data.name
        if data.description is not None:
            role.description = data.description
        if data.permission_ids is not None:
            role.permissions = self.perms.get_by_codes(data.permission_ids)
        self.db.flush()
        self.audit.log(AuditAction.UPDATE, entity="Role", entity_id=role.id)
        self.db.commit()
        self.db.refresh(role)
        return RoleRead.model_validate(role)

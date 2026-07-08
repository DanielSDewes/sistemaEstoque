"""User, Role and Permission schemas."""
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.validators import validate_password_strength
from app.schemas.common import ORMModel


class PermissionRead(ORMModel):
    id: int
    code: str
    description: str


class RoleBase(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    description: str | None = None


class RoleCreate(RoleBase):
    permission_ids: list[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=60)
    description: str | None = None
    permission_ids: list[int] | None = None


class RoleRead(ORMModel):
    id: int
    name: str
    description: str | None
    is_system: bool
    permissions: list[PermissionRead] = Field(default_factory=list)


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    username: str = Field(min_length=3, max_length=80)
    is_active: bool = True
    notes: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role_id: int

    @field_validator("password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    is_active: bool | None = None
    role_id: int | None = None
    notes: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserRead(ORMModel):
    id: int
    full_name: str
    email: EmailStr
    username: str
    is_active: bool
    is_superuser: bool
    role: RoleRead

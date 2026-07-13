"""Authentication-related schemas."""
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.validators import validate_password_strength
from app.schemas.user import UserRead


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    type: str | None = None


class LoginRequest(BaseModel):
    username: str  # accepts username or email
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginResponse(Token):
    user: UserRead


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    detail: str
    # Only populated outside production, to make local/demo flows testable
    # without a mail server. Never returned when ENVIRONMENT=production.
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=255)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        return validate_password_strength(v)

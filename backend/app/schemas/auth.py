"""Authentication-related schemas."""
from pydantic import BaseModel

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

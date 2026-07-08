"""Security primitives: password hashing and JWT token handling."""
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def _create_token(subject: str | int, token_type: TokenType, expires_minutes: int) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "jti": uuid.uuid4().hex,  # unique id enabling revocation/rotation
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str | int) -> str:
    """Create a short-lived access token for the given user id."""
    return _create_token(subject, "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(subject: str | int) -> str:
    """Create a long-lived refresh token for the given user id."""
    return _create_token(subject, "refresh", settings.REFRESH_TOKEN_EXPIRE_MINUTES)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT, returning its claims or None if invalid."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

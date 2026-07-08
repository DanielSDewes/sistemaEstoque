"""Unit tests for security primitives (no DB required)."""
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("Secret@123")
    assert hashed != "Secret@123"
    assert verify_password("Secret@123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_roundtrip():
    token = create_access_token(42)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_decode_invalid_token_returns_none():
    assert decode_token("not-a-real-token") is None

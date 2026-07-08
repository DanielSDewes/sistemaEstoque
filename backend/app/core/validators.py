"""Reusable value validators shared across schemas."""
import re

from app.core.config import settings

_UPPER = re.compile(r"[A-Z]")
_LOWER = re.compile(r"[a-z]")
_DIGIT = re.compile(r"\d")
_SYMBOL = re.compile(r"[^A-Za-z0-9]")


def validate_password_strength(value: str) -> str:
    """Enforce length + character-class requirements on a password."""
    errors = []
    if len(value) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"minimo de {settings.PASSWORD_MIN_LENGTH} caracteres")
    if not _UPPER.search(value):
        errors.append("uma letra maiuscula")
    if not _LOWER.search(value):
        errors.append("uma letra minuscula")
    if not _DIGIT.search(value):
        errors.append("um numero")
    if not _SYMBOL.search(value):
        errors.append("um simbolo")
    if errors:
        raise ValueError("A senha deve conter: " + ", ".join(errors) + ".")
    return value

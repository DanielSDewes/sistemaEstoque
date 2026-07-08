"""Unit tests for the in-memory rate limiter and password policy."""
import pytest

from app.core.ratelimit import is_rate_limited, reset
from app.core.validators import validate_password_strength


def test_rate_limiter_blocks_after_max():
    key = "unit-test-key"
    reset(key)
    assert not is_rate_limited(key, max_events=3, window_seconds=60)
    assert not is_rate_limited(key, max_events=3, window_seconds=60)
    assert not is_rate_limited(key, max_events=3, window_seconds=60)
    # 4th within window is blocked.
    assert is_rate_limited(key, max_events=3, window_seconds=60)
    reset(key)
    assert not is_rate_limited(key, max_events=3, window_seconds=60)


@pytest.mark.parametrize(
    "password,ok",
    [
        ("Strong@123", True),
        ("short1!A", True),
        ("weak", False),
        ("nouppercase1!", False),
        ("NOLOWERCASE1!", False),
        ("NoDigits!!", False),
        ("NoSymbol123", False),
    ],
)
def test_password_strength(password, ok):
    if ok:
        assert validate_password_strength(password) == password
    else:
        with pytest.raises(ValueError):
            validate_password_strength(password)

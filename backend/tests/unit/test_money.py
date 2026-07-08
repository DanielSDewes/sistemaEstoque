"""Unit tests for Decimal money/quantity helpers."""
from decimal import Decimal

from app.core.money import q_cost, q_money, q_qty, to_decimal


def test_to_decimal_avoids_float_artifacts():
    assert to_decimal(0.1) + to_decimal(0.2) == Decimal("0.3")


def test_quantize_scales():
    assert q_qty("1.23456") == Decimal("1.235")
    assert q_money("1.239") == Decimal("1.24")
    assert q_cost("1.234567") == Decimal("1.2346")


def test_none_is_zero():
    assert to_decimal(None) == Decimal("0")

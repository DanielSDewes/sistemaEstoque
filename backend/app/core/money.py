"""Decimal helpers for exact quantity and monetary arithmetic.

Balances and valuations are accumulated as ``Decimal`` (never binary floats)
and quantized at well-defined scales. Values are converted to ``float`` only at
the API/DTO boundary so the JSON contract stays numeric.
"""
from decimal import ROUND_HALF_UP, Decimal

QTY_SCALE = Decimal("0.001")   # 3 casas (quantidades)
MONEY_SCALE = Decimal("0.01")  # 2 casas (valores)
COST_SCALE = Decimal("0.0001")  # 4 casas (custos unitários)


def to_decimal(value: object) -> Decimal:
    """Coerce any numeric-ish value to Decimal without float artifacts."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def q_qty(value: object) -> Decimal:
    return to_decimal(value).quantize(QTY_SCALE, rounding=ROUND_HALF_UP)


def q_money(value: object) -> Decimal:
    return to_decimal(value).quantize(MONEY_SCALE, rounding=ROUND_HALF_UP)


def q_cost(value: object) -> Decimal:
    return to_decimal(value).quantize(COST_SCALE, rounding=ROUND_HALF_UP)

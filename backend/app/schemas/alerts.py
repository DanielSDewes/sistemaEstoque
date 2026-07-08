"""Schemas for the alerts center."""
from datetime import date

from pydantic import BaseModel


class BelowMinimumItem(BaseModel):
    product_id: int
    internal_code: str
    name: str
    current: float
    min_stock: float
    reorder_point: float
    deficit: float


class NearExpiryItem(BaseModel):
    product_id: int
    internal_code: str
    name: str
    lot_number: str
    expiry_date: date
    days_remaining: int


class AlertsSummary(BaseModel):
    below_minimum_count: int
    near_expiry_count: int
    expired_count: int
    out_of_stock_count: int

"""Inventory schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import InventoryScope, InventoryStatus
from app.schemas.common import ORMModel


class InventoryCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    description: str | None = None
    scope: InventoryScope
    scope_ref_id: int | None = None


class InventoryItemCount(BaseModel):
    counted_quantity: float = Field(ge=0)
    notes: str | None = None


class InventoryItemRead(ORMModel):
    id: int
    product_id: int
    system_quantity: float
    counted_quantity: float | None
    difference: float | None
    divergence_pct: float | None
    counted_at: datetime | None
    notes: str | None


class InventoryRead(ORMModel):
    id: int
    code: str
    description: str | None
    scope: InventoryScope
    scope_ref_id: int | None
    status: InventoryStatus
    created_by_id: int | None
    approved_by_id: int | None
    approved_at: datetime | None


class InventoryDetail(InventoryRead):
    items: list[InventoryItemRead] = []


class InventorySummary(BaseModel):
    total_items: int
    counted_items: int
    surplus_qty: float
    shortage_qty: float
    net_difference: float

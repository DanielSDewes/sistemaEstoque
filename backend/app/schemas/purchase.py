"""Purchase order (Pedido de Compra) schemas."""
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import PurchaseOrderStatus
from app.schemas.common import ORMModel


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit_cost: float = Field(ge=0)


class PurchaseOrderItemRead(ORMModel):
    id: int
    product_id: int
    product_name: str
    product_code: str
    quantity: float
    unit_cost: float
    received_quantity: float
    pending_quantity: float
    line_total: float


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    order_date: datetime | None = None
    expected_date: date | None = None
    notes: str | None = None
    extra_cost: float = Field(default=0, ge=0)
    items: list[PurchaseOrderItemCreate] = Field(min_length=1)


class PurchaseOrderUpdate(BaseModel):
    supplier_id: int | None = None
    order_date: datetime | None = None
    expected_date: date | None = None
    notes: str | None = None
    extra_cost: float | None = Field(default=None, ge=0)
    items: list[PurchaseOrderItemCreate] | None = None


class PurchaseOrderRead(ORMModel):
    id: int
    number: str | None
    supplier_id: int
    supplier_name: str
    status: PurchaseOrderStatus
    order_date: datetime
    expected_date: date | None
    notes: str | None
    total_amount: float
    extra_cost: float
    items: list[PurchaseOrderItemRead]
    placed_at: datetime | None
    received_at: datetime | None
    cancelled_at: datetime | None


class ReceiveItem(BaseModel):
    item_id: int
    quantity: float = Field(gt=0)


class PurchaseOrderReceive(BaseModel):
    # When omitted/empty, every item's remaining quantity is received in full.
    items: list[ReceiveItem] | None = None


class PurchaseOrderCancel(BaseModel):
    reason: str = Field(min_length=3, max_length=200)

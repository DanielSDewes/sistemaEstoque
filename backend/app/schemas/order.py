"""Sales order schemas."""
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import OrderStatus
from app.schemas.common import ORMModel
from app.schemas.customer import CustomerSummary


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)


class OrderItemRead(ORMModel):
    id: int
    product_id: int
    product_name: str
    product_code: str
    quantity: float
    unit_price: float
    unit_cost: float
    line_total: float


class OrderCreate(BaseModel):
    customer_id: int
    order_date: datetime | None = None
    notes: str | None = None
    extra_cost: float = Field(default=0, ge=0)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderUpdate(BaseModel):
    customer_id: int | None = None
    order_date: datetime | None = None
    notes: str | None = None
    extra_cost: float | None = Field(default=None, ge=0)
    items: list[OrderItemCreate] | None = None


class OrderRead(ORMModel):
    id: int
    number: str | None
    customer_id: int
    customer: CustomerSummary
    status: OrderStatus
    order_date: datetime
    notes: str | None
    total_amount: float
    extra_cost: float
    total_cost: float
    profit: float
    items: list[OrderItemRead]
    confirmed_at: datetime | None
    cancelled_at: datetime | None


class OrderCancel(BaseModel):
    reason: str = Field(min_length=3, max_length=200)


# --- Profit report ---
class ProfitPeriod(BaseModel):
    period: str
    orders: int
    revenue: float
    cost: float
    extra_cost: float
    profit: float


class ProfitReport(BaseModel):
    start: date
    end: date
    group_by: str
    totals: ProfitPeriod
    periods: list[ProfitPeriod]

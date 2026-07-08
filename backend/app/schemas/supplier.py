"""Supplier and Product<->Supplier schemas."""
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import StatusEnum
from app.schemas.common import ORMModel


class SupplierBase(BaseModel):
    legal_name: str = Field(min_length=2, max_length=200)
    trade_name: str | None = None
    cnpj: str = Field(min_length=14, max_length=18)
    state_registration: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = Field(default=None, max_length=2)
    zip_code: str | None = None
    contact: str | None = None
    email: str | None = None
    phone: str | None = None
    responsible: str | None = None
    notes: str | None = None
    status: StatusEnum = StatusEnum.ACTIVE


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    legal_name: str | None = None
    trade_name: str | None = None
    cnpj: str | None = None
    state_registration: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    contact: str | None = None
    email: str | None = None
    phone: str | None = None
    responsible: str | None = None
    notes: str | None = None
    status: StatusEnum | None = None


class SupplierRead(ORMModel):
    id: int
    legal_name: str
    trade_name: str | None
    cnpj: str
    state_registration: str | None
    address: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    contact: str | None
    email: str | None
    phone: str | None
    responsible: str | None
    notes: str | None
    status: StatusEnum


class ProductSupplierBase(BaseModel):
    supplier_id: int
    supplier_product_code: str | None = None
    current_price: float | None = None
    last_purchase_date: date | None = None
    lead_time_days: int | None = None
    is_primary: bool = False


class ProductSupplierCreate(ProductSupplierBase):
    product_id: int


class ProductSupplierUpdate(BaseModel):
    supplier_product_code: str | None = None
    current_price: float | None = None
    last_purchase_date: date | None = None
    lead_time_days: int | None = None
    is_primary: bool | None = None


class PriceHistoryRead(ORMModel):
    id: int
    old_price: float | None
    new_price: float | None
    changed_at: datetime


class ProductSupplierRead(ORMModel):
    id: int
    product_id: int
    supplier_id: int
    supplier: SupplierRead
    supplier_product_code: str | None
    last_price: float | None
    current_price: float | None
    average_price: float | None
    last_purchase_date: date | None
    lead_time_days: int | None
    is_primary: bool

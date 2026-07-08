"""Product and Batch schemas."""
from datetime import date

from pydantic import BaseModel, Field

from app.models.enums import StatusEnum
from app.schemas.catalog import CatalogRead
from app.schemas.common import ORMModel


# --- Batch ---
class BatchBase(BaseModel):
    lot_number: str = Field(min_length=1, max_length=60)
    serial_number: str | None = None
    manufacture_date: date | None = None
    expiry_date: date | None = None
    status: StatusEnum = StatusEnum.ACTIVE


class BatchCreate(BatchBase):
    product_id: int


class BatchRead(ORMModel):
    id: int
    product_id: int
    lot_number: str
    serial_number: str | None
    manufacture_date: date | None
    expiry_date: date | None
    status: StatusEnum


# --- Product ---
class ProductBase(BaseModel):
    internal_code: str = Field(min_length=1, max_length=40)
    barcode: str | None = None
    sku: str | None = None
    name: str = Field(min_length=1, max_length=200)
    short_name: str | None = None
    description: str | None = None
    category_id: int | None = None
    group_id: int | None = None
    subgroup_id: int | None = None
    brand_id: int | None = None
    unit: str = "UN"
    weight: float | None = None
    volume: float | None = None
    dimensions: str | None = None
    color: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    ncm: str | None = None
    fiscal_code: str | None = None
    photo_url: str | None = None
    is_active: bool = True
    min_stock: float = Field(default=0, ge=0)
    max_stock: float = Field(default=0, ge=0)
    reorder_point: float = Field(default=0, ge=0)
    reserved_stock: float = Field(default=0, ge=0)
    track_serial: bool = False
    sale_price: float = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    internal_code: str | None = None
    barcode: str | None = None
    sku: str | None = None
    name: str | None = None
    short_name: str | None = None
    description: str | None = None
    category_id: int | None = None
    group_id: int | None = None
    subgroup_id: int | None = None
    brand_id: int | None = None
    unit: str | None = None
    weight: float | None = None
    volume: float | None = None
    dimensions: str | None = None
    color: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    ncm: str | None = None
    fiscal_code: str | None = None
    photo_url: str | None = None
    is_active: bool | None = None
    min_stock: float | None = Field(default=None, ge=0)
    max_stock: float | None = Field(default=None, ge=0)
    reorder_point: float | None = Field(default=None, ge=0)
    reserved_stock: float | None = Field(default=None, ge=0)
    track_serial: bool | None = None
    sale_price: float | None = Field(default=None, ge=0)


class ImportResult(BaseModel):
    created: int = 0
    updated: int = 0
    errors: list[dict] = Field(default_factory=list)


class ProductStock(BaseModel):
    """Computed stock figures derived exclusively from movements."""

    current: float = 0
    reserved: float = 0
    available: float = 0
    min_stock: float = 0
    max_stock: float = 0
    reorder_point: float = 0
    below_minimum: bool = False


class ProductRead(ORMModel):
    id: int
    internal_code: str
    barcode: str | None
    sku: str | None
    name: str
    short_name: str | None
    description: str | None
    unit: str
    weight: float | None
    volume: float | None
    dimensions: str | None
    color: str | None
    model: str | None
    manufacturer: str | None
    ncm: str | None
    fiscal_code: str | None
    photo_url: str | None
    is_active: bool
    min_stock: float
    max_stock: float
    reorder_point: float
    reserved_stock: float
    track_serial: bool
    average_cost: float = 0
    sale_price: float = 0
    category: CatalogRead | None = None
    group: CatalogRead | None = None
    subgroup: CatalogRead | None = None
    brand: CatalogRead | None = None
    # Attached by the service layer (not stored on the row):
    stock: ProductStock | None = None

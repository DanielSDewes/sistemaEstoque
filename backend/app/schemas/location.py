"""Location schemas: Corridor, Shelf, ProductLocation."""
from pydantic import BaseModel, Field

from app.models.enums import StatusEnum
from app.schemas.common import ORMModel


# --- Corridor ---
class CorridorBase(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    status: StatusEnum = StatusEnum.ACTIVE


class CorridorCreate(CorridorBase):
    pass


class CorridorUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    status: StatusEnum | None = None


class CorridorRead(ORMModel):
    id: int
    code: str
    name: str
    description: str | None
    status: StatusEnum


# --- Shelf ---
class ShelfBase(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    corridor_id: int
    capacity: float | None = None
    observations: str | None = None
    status: StatusEnum = StatusEnum.ACTIVE


class ShelfCreate(ShelfBase):
    pass


class ShelfUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    corridor_id: int | None = None
    capacity: float | None = None
    observations: str | None = None
    status: StatusEnum | None = None


class ShelfRead(ORMModel):
    id: int
    code: str
    name: str
    corridor_id: int
    corridor: CorridorRead
    capacity: float | None
    observations: str | None
    status: StatusEnum


# --- ProductLocation ---
class ProductLocationBase(BaseModel):
    corridor_id: int
    shelf_id: int
    quantity: float = 0
    is_primary: bool = False


class ProductLocationCreate(ProductLocationBase):
    product_id: int


class ProductLocationRead(ORMModel):
    id: int
    product_id: int
    corridor_id: int
    shelf_id: int
    quantity: float
    corridor: CorridorRead
    shelf: ShelfRead
    # Movement-derived balance for this shelf (attached by the service layer).
    stock_balance: float = 0

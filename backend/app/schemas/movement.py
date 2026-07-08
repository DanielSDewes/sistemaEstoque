"""Stock movement schemas."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import MovementDirection, MovementType
from app.schemas.common import ORMModel


class MovementCreate(BaseModel):
    product_id: int
    movement_type: MovementType
    quantity: float = Field(gt=0)
    unit_cost: float | None = None
    batch_id: int | None = None
    reason: str | None = None
    document: str | None = None
    notes: str | None = None
    origin_location_id: int | None = None
    destination_location_id: int | None = None
    moved_at: datetime | None = None


class MovementRead(ORMModel):
    id: int
    product_id: int
    movement_type: MovementType
    direction: MovementDirection
    quantity: float
    unit_cost: float | None
    batch_id: int | None
    moved_at: datetime
    reason: str | None
    document: str | None
    notes: str | None
    origin_location_id: int | None
    destination_location_id: int | None
    user_id: int | None
    is_cancelled: bool


class MovementCancel(BaseModel):
    reason: str = Field(min_length=3, max_length=200)

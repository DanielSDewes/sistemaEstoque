"""StockMovement model - the single source of truth for stock balances."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import MovementDirection, MovementType
from app.models.types import str_enum


class StockMovement(Base):
    """An immutable stock movement. Balances are derived by summing these.

    Movements are never physically deleted; they are cancelled via
    ``is_cancelled`` while preserving the full history.
    """

    __tablename__ = "stock_movements"
    __table_args__ = (
        Index("ix_movement_product_date", "product_id", "moved_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), index=True, nullable=False
    )
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("batches.id"))

    movement_type: Mapped[MovementType] = mapped_column(
        str_enum(MovementType, "movement_type_enum"), nullable=False
    )
    direction: Mapped[MovementDirection] = mapped_column(
        str_enum(MovementDirection, "movement_direction_enum"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(14, 4))

    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(String(200))
    document: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)

    origin_location_id: Mapped[int | None] = mapped_column(ForeignKey("shelves.id"))
    destination_location_id: Mapped[int | None] = mapped_column(ForeignKey("shelves.id"))

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    cancelled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inventory_id: Mapped[int | None] = mapped_column(ForeignKey("inventories.id"))

    product = relationship("Product", lazy="joined")
    batch = relationship("Batch")
    user = relationship("User", foreign_keys=[user_id])

    @property
    def signed_quantity(self) -> float:
        """Quantity with sign applied by direction (0 when cancelled)."""
        if self.is_cancelled:
            return 0.0
        q = float(self.quantity)
        return q if self.direction == MovementDirection.IN else -q

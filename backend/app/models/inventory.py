"""Inventory (physical count) and InventoryItem models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import InventoryScope, InventoryStatus
from app.models.mixins import TimestampMixin
from app.models.types import str_enum


class Inventory(Base, TimestampMixin):
    """A stock-count session covering a configurable scope."""

    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    scope: Mapped[InventoryScope] = mapped_column(
        str_enum(InventoryScope, "inventory_scope_enum"), nullable=False
    )
    scope_ref_id: Mapped[int | None] = mapped_column(Integer)  # category/group/corridor/shelf id
    status: Mapped[InventoryStatus] = mapped_column(
        str_enum(InventoryStatus, "inventory_status_enum"),
        default=InventoryStatus.OPEN,
        nullable=False,
        index=True,
    )

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items: Mapped[list[InventoryItem]] = relationship(
        back_populates="inventory", cascade="all, delete-orphan"
    )


class InventoryItem(Base):
    """A single product line within an inventory, with counted vs system qty."""

    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    system_quantity: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    counted_quantity: Mapped[float | None] = mapped_column(Numeric(14, 3))
    counted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    counted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(Text)

    inventory: Mapped[Inventory] = relationship(back_populates="items")
    product = relationship("Product", lazy="joined")

    @property
    def difference(self) -> float | None:
        """counted - system; positive = surplus (sobra), negative = shortage (falta)."""
        if self.counted_quantity is None:
            return None
        return float(self.counted_quantity) - float(self.system_quantity)

    @property
    def divergence_pct(self) -> float | None:
        diff = self.difference
        if diff is None:
            return None
        base = float(self.system_quantity)
        if base == 0:
            return 100.0 if diff != 0 else 0.0
        return round(diff / base * 100, 2)

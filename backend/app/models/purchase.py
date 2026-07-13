"""Purchase order (Pedido de Compra) and its line items.

A purchase order starts as a draft, is *placed* with a supplier, then *received*
(fully or partially). Receiving generates one inbound ``compra`` movement per
received quantity, which feeds the weighted moving-average cost and the balance.
Stock is only ever affected at receiving time.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PurchaseOrderStatus
from app.models.mixins import TimestampMixin
from app.models.types import str_enum


class PurchaseOrder(Base, TimestampMixin):
    """A purchase order header linked to a supplier."""

    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str | None] = mapped_column(String(40), unique=True, index=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id"), index=True, nullable=False
    )
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        str_enum(PurchaseOrderStatus, "purchase_order_status_enum"),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
        index=True,
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expected_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    total_amount: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, server_default="0", nullable=False
    )
    # Freight/other costs tied to the order itself (not to a single item).
    extra_cost: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, server_default="0", nullable=False
    )

    placed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    supplier = relationship("Supplier", lazy="joined")
    items: Mapped[list[PurchaseOrderItem]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )


class PurchaseOrderItem(Base):
    """A single product line within a purchase order."""

    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), index=True, nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    # How much of ``quantity`` has already been received into stock.
    received_quantity: Mapped[float] = mapped_column(
        Numeric(14, 3), default=0, server_default="0", nullable=False
    )

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="items")
    product = relationship("Product", lazy="joined")

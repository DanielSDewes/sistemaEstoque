"""Sales order (Pedido) and its line items.

An order starts as a draft. Confirming it deducts stock by generating one
``StockMovement`` of type ``venda`` per item; cancelling reverses them.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import OrderStatus
from app.models.mixins import TimestampMixin
from app.models.types import str_enum


class Order(Base, TimestampMixin):
    """A sales order header linked to a customer."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str | None] = mapped_column(String(40), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), index=True, nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        str_enum(OrderStatus, "order_status_enum"),
        default=OrderStatus.DRAFT,
        nullable=False,
        index=True,
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    total_amount: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, server_default="0", nullable=False
    )
    # Extra costs tied to the order itself (e.g. delivery fuel), not to any item.
    extra_cost: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, server_default="0", nullable=False
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    customer = relationship("Customer", back_populates="orders", lazy="joined")
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    """A single product line within an order."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), index=True, nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    # Snapshot of the product's average cost (COGS) at the time of the sale.
    unit_cost: Mapped[float] = mapped_column(
        Numeric(14, 4), default=0, server_default="0", nullable=False
    )
    # Movement generated when the order is confirmed (used to reverse on cancel).
    movement_id: Mapped[int | None] = mapped_column(ForeignKey("stock_movements.id"))

    order: Mapped[Order] = relationship(back_populates="items")
    product = relationship("Product", lazy="joined")

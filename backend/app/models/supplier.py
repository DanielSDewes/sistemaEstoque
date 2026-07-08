"""Supplier, Product<->Supplier link and supplier price history models."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusEnum
from app.models.mixins import TimestampMixin
from app.models.types import str_enum


class Supplier(Base, TimestampMixin):
    """A supplier (Fornecedor) with full registration data."""

    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)  # Razao social
    trade_name: Mapped[str | None] = mapped_column(String(200))  # Nome fantasia
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, index=True, nullable=False)
    state_registration: Mapped[str | None] = mapped_column(String(30))  # Inscricao Estadual
    address: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(2))
    zip_code: Mapped[str | None] = mapped_column(String(9))
    contact: Mapped[str | None] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(30))
    responsible: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )

    products: Mapped[list[ProductSupplier]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )


class ProductSupplier(Base, TimestampMixin):
    """Association carrying supplier-specific pricing for a product."""

    __tablename__ = "product_suppliers"
    __table_args__ = (
        UniqueConstraint("product_id", "supplier_id", name="uq_product_supplier"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    supplier_product_code: Mapped[str | None] = mapped_column(String(60))
    last_price: Mapped[float | None] = mapped_column(Numeric(14, 4))
    current_price: Mapped[float | None] = mapped_column(Numeric(14, 4))
    average_price: Mapped[float | None] = mapped_column(Numeric(14, 4))
    last_purchase_date: Mapped[date | None] = mapped_column(Date)
    lead_time_days: Mapped[int | None] = mapped_column(Integer)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped[Product] = relationship(back_populates="suppliers")  # noqa: F821
    supplier: Mapped[Supplier] = relationship(back_populates="products", lazy="joined")
    price_history: Mapped[list[SupplierPriceHistory]] = relationship(
        back_populates="product_supplier", cascade="all, delete-orphan"
    )


class SupplierPriceHistory(Base):
    """Immutable log of price changes for a product/supplier pair."""

    __tablename__ = "supplier_price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_supplier_id: Mapped[int] = mapped_column(
        ForeignKey("product_suppliers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    old_price: Mapped[float | None] = mapped_column(Numeric(14, 4))
    new_price: Mapped[float | None] = mapped_column(Numeric(14, 4))
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product_supplier: Mapped[ProductSupplier] = relationship(back_populates="price_history")

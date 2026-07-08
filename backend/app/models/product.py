"""Product and Batch (Lote) models."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusEnum
from app.models.mixins import TimestampMixin
from app.models.types import str_enum


class Product(Base, TimestampMixin):
    """A stock-keeping product with full descriptive and stock-config fields."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- Identification ---
    internal_code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(60), index=True)
    sku: Mapped[str | None] = mapped_column(String(60), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)

    # --- Classification (independent taxonomies) ---
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), index=True)
    subgroup_id: Mapped[int | None] = mapped_column(ForeignKey("subgroups.id"), index=True)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brands.id"), index=True)

    # --- Physical attributes ---
    unit: Mapped[str] = mapped_column(String(20), default="UN", nullable=False)
    weight: Mapped[float | None] = mapped_column(Numeric(14, 3))
    volume: Mapped[float | None] = mapped_column(Numeric(14, 3))
    dimensions: Mapped[str | None] = mapped_column(String(60))  # e.g. "10x20x30 cm"
    color: Mapped[str | None] = mapped_column(String(40))
    model: Mapped[str | None] = mapped_column(String(60))
    manufacturer: Mapped[str | None] = mapped_column(String(120))

    # --- Fiscal ---
    ncm: Mapped[str | None] = mapped_column(String(20))
    fiscal_code: Mapped[str | None] = mapped_column(String(20))

    # --- Media / status ---
    photo_url: Mapped[str | None] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # --- Stock configuration (limits, never the live balance) ---
    min_stock: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    max_stock: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    reorder_point: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    reserved_stock: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    track_serial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Weighted moving-average cost, maintained on each inbound movement.
    average_cost: Mapped[float] = mapped_column(
        Numeric(14, 4), default=0, server_default="0", nullable=False
    )
    # Manually maintained sale price (used as the default price on order items).
    sale_price: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, server_default="0", nullable=False
    )

    # --- Relationships ---
    category = relationship("Category", lazy="joined")
    group = relationship("Group", lazy="joined")
    subgroup = relationship("Subgroup", lazy="joined")
    brand = relationship("Brand", lazy="joined")
    locations: Mapped[list[ProductLocation]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )
    batches: Mapped[list[Batch]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    suppliers: Mapped[list[ProductSupplier]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )


class Batch(Base, TimestampMixin):
    """A product batch/lot carrying manufacture, expiry and serial data."""

    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lot_number: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    serial_number: Mapped[str | None] = mapped_column(String(80))
    manufacture_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )

    product: Mapped[Product] = relationship(back_populates="batches")

"""Physical location models: Corridor, Shelf and Product<->location links."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusEnum
from app.models.mixins import TimestampMixin
from app.models.types import str_enum


class Corridor(Base, TimestampMixin):
    """A warehouse corridor (Corredor)."""

    __tablename__ = "corridors"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )

    shelves: Mapped[list[Shelf]] = relationship(
        back_populates="corridor", cascade="all, delete-orphan"
    )


class Shelf(Base, TimestampMixin):
    """A shelf (Prateleira) belonging to a corridor."""

    __tablename__ = "shelves"
    __table_args__ = (UniqueConstraint("corridor_id", "code", name="uq_shelf_corridor_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    capacity: Mapped[float | None] = mapped_column(Numeric(14, 3))
    observations: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )

    corridor_id: Mapped[int] = mapped_column(
        ForeignKey("corridors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    corridor: Mapped[Corridor] = relationship(back_populates="shelves", lazy="joined")


class ProductLocation(Base, TimestampMixin):
    """Associates a product with a physical location (many-to-many capable)."""

    __tablename__ = "product_locations"
    __table_args__ = (
        UniqueConstraint("product_id", "shelf_id", name="uq_product_shelf"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    corridor_id: Mapped[int] = mapped_column(
        ForeignKey("corridors.id"), index=True, nullable=False
    )
    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id"), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped[Product] = relationship(back_populates="locations")  # noqa: F821
    corridor: Mapped[Corridor] = relationship(lazy="joined")
    shelf: Mapped[Shelf] = relationship(lazy="joined")

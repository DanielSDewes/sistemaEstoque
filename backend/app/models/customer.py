"""Customer (Cliente) and its addresses - the CRM core entity."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusEnum
from app.models.mixins import TimestampMixin
from app.models.types import str_enum


class Customer(Base, TimestampMixin):
    """A customer (Cliente). Only name and phone are required."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    document: Mapped[str | None] = mapped_column(String(20), index=True)  # CPF/CNPJ
    email: Mapped[str | None] = mapped_column(String(150))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )

    addresses: Mapped[list[CustomerAddress]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    orders: Mapped[list[Order]] = relationship(back_populates="customer")  # noqa: F821


class CustomerAddress(Base, TimestampMixin):
    """One of possibly many addresses for a customer."""

    __tablename__ = "customer_addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str | None] = mapped_column(String(60))  # e.g. "Casa", "Entrega"
    street: Mapped[str | None] = mapped_column(String(255))
    number: Mapped[str | None] = mapped_column(String(20))
    complement: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(120))  # Bairro
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(2))
    zip_code: Mapped[str | None] = mapped_column(String(9))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="addresses")

"""Independent catalog taxonomies: Category, Group, Subgroup, Brand."""
from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import StatusEnum
from app.models.mixins import TimestampMixin
from app.models.types import str_enum


class _NamedCatalog(Base, TimestampMixin):
    """Abstract base for simple code/name/description catalog tables."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )


class Category(_NamedCatalog):
    __tablename__ = "categories"


class Group(_NamedCatalog):
    __tablename__ = "groups"


class Subgroup(_NamedCatalog):
    __tablename__ = "subgroups"


class Brand(_NamedCatalog):
    __tablename__ = "brands"

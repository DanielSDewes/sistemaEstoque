"""Reusable pagination helpers and generic paginated response schema."""
from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    """Common query params for pagination and sorting."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=200)
    sort_by: str | None = None
    sort_dir: str = Field(default="asc", pattern="^(asc|desc)$")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class Page(BaseModel, Generic[T]):
    """Envelope returned by list endpoints."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=ceil(total / params.size) if params.size else 0,
        )

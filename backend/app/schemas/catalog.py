"""Catalog schemas: Category, Group, Subgroup, Brand (shared shape)."""
from pydantic import BaseModel, Field

from app.models.enums import StatusEnum
from app.schemas.common import ORMModel


class CatalogBase(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    status: StatusEnum = StatusEnum.ACTIVE


class CatalogCreate(CatalogBase):
    pass


class CatalogUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=30)
    name: str | None = Field(default=None, max_length=120)
    description: str | None = None
    status: StatusEnum | None = None


class CatalogRead(ORMModel):
    id: int
    code: str
    name: str
    description: str | None
    status: StatusEnum

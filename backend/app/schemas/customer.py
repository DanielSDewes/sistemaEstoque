"""Customer and customer-address schemas."""
from pydantic import BaseModel, Field

from app.models.enums import StatusEnum
from app.schemas.common import ORMModel


class CustomerAddressBase(BaseModel):
    label: str | None = Field(default=None, max_length=60)
    street: str | None = Field(default=None, max_length=255)
    number: str | None = Field(default=None, max_length=20)
    complement: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=2)
    zip_code: str | None = Field(default=None, max_length=9)
    is_primary: bool = False


class CustomerAddressCreate(CustomerAddressBase):
    pass


class CustomerAddressRead(ORMModel):
    id: int
    label: str | None
    street: str | None
    number: str | None
    complement: str | None
    district: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    is_primary: bool


class CustomerBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=8, max_length=30)
    document: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=150)
    notes: str | None = None
    status: StatusEnum = StatusEnum.ACTIVE


class CustomerCreate(CustomerBase):
    addresses: list[CustomerAddressCreate] = []


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, min_length=8, max_length=30)
    document: str | None = None
    email: str | None = None
    notes: str | None = None
    status: StatusEnum | None = None
    # When provided, replaces the whole address collection.
    addresses: list[CustomerAddressCreate] | None = None


class CustomerRead(ORMModel):
    id: int
    name: str
    phone: str
    document: str | None
    email: str | None
    notes: str | None
    status: StatusEnum
    addresses: list[CustomerAddressRead] = []


class CustomerSummary(ORMModel):
    """Lightweight customer reference embedded in orders."""

    id: int
    name: str
    phone: str

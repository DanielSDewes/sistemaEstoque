"""Shared schema base classes and generic responses."""
from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for schemas read from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    """Generic message response."""

    detail: str

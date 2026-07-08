"""Shared SQLAlchemy type helpers."""
from enum import Enum

from sqlalchemy import Enum as SAEnum


def str_enum(enum_cls: type[Enum], name: str) -> SAEnum:
    """Build a SQLAlchemy Enum that persists the member *values* (e.g. "ativo").

    Without ``values_callable`` SQLAlchemy stores member *names* (``ACTIVE``),
    which diverges from the lowercase values exposed by the API. Persisting the
    values keeps the database and the API contract identical.
    """
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda enum: [member.value for member in enum],
        native_enum=True,
    )

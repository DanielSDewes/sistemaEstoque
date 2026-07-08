"""Append-only audit log. Records are never updated or deleted."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AuditAction
from app.models.types import str_enum


class AuditLog(Base):
    """Immutable audit trail entry capturing who changed what, when and from where."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    username: Mapped[str | None] = mapped_column(String(120))  # denormalized snapshot
    action: Mapped[AuditAction] = mapped_column(
        str_enum(AuditAction, "audit_action_enum"), nullable=False, index=True
    )
    entity: Mapped[str | None] = mapped_column(String(80), index=True)  # "Tela"/tabela
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)
    field: Mapped[str | None] = mapped_column(String(80))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user = relationship("User", lazy="joined")

"""Audit log repository (append-only)."""
from datetime import datetime

from sqlalchemy import Select, and_, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(AuditLog, db)

    def build_filter(
        self,
        user_id: int | None = None,
        action: str | None = None,
        entity: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> Select:
        stmt = select(AuditLog)
        conditions = []
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if entity:
            conditions.append(AuditLog.entity == entity)
        if date_from:
            conditions.append(AuditLog.created_at >= date_from)
        if date_to:
            conditions.append(AuditLog.created_at <= date_to)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        return stmt.order_by(AuditLog.created_at.desc())

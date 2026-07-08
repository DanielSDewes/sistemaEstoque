"""Audit log schemas."""
from datetime import datetime

from app.models.enums import AuditAction
from app.schemas.common import ORMModel


class AuditLogRead(ORMModel):
    id: int
    user_id: int | None
    username: str | None
    action: AuditAction
    entity: str | None
    entity_id: int | None
    field: str | None
    old_value: str | None
    new_value: str | None
    ip_address: str | None
    created_at: datetime

"""Audit service - centralized, append-only change logging."""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.models.user import User


@dataclass
class RequestContext:
    """Carries the acting user and request metadata for audit entries."""

    user: User | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AuditService:
    """Writes immutable audit records. Never updates or deletes."""

    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()

    def log(
        self,
        action: AuditAction,
        *,
        entity: str | None = None,
        entity_id: int | None = None,
        field: str | None = None,
        old_value: object | None = None,
        new_value: object | None = None,
    ) -> AuditLog:
        user = self.ctx.user
        entry = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else None,
            action=action,
            entity=entity,
            entity_id=entity_id,
            field=field,
            old_value=None if old_value is None else str(old_value),
            new_value=None if new_value is None else str(new_value),
            ip_address=self.ctx.ip_address,
            user_agent=self.ctx.user_agent,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def log_diff(
        self,
        action: AuditAction,
        entity: str,
        entity_id: int,
        before: dict[str, object],
        after: dict[str, object],
    ) -> None:
        """Emit one audit row per changed field."""
        for key, new in after.items():
            old = before.get(key)
            if old != new:
                self.log(
                    action,
                    entity=entity,
                    entity_id=entity_id,
                    field=key,
                    old_value=old,
                    new_value=new,
                )

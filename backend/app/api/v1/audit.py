"""Audit log endpoints (read-only; records are immutable)."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_page_params, require_permission
from app.core.database import get_db
from app.core.pagination import Page, PageParams
from app.models.enums import AuditAction
from app.repositories.audit import AuditRepository
from app.schemas.audit import AuditLogRead

router = APIRouter(prefix="/audit", tags=["Auditoria"])


@router.get("", response_model=Page[AuditLogRead], summary="Consultar trilha de auditoria")
def list_audit(
    user_id: int | None = None,
    action: AuditAction | None = None,
    entity: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("audit:view")),
) -> Page[AuditLogRead]:
    repo = AuditRepository(db)
    stmt = repo.build_filter(
        user_id=user_id,
        action=action.value if action else None,
        entity=entity,
        date_from=date_from,
        date_to=date_to,
    )
    items, total = repo.paginate(params, stmt)
    return Page.create([AuditLogRead.model_validate(a) for a in items], total, params)

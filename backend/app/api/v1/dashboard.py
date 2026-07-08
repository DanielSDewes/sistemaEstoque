"""Dashboard endpoint."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse, summary="Indicadores e graficos")
def get_dashboard(
    days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db),
    _=Depends(require_permission("dashboard:view")),
) -> DashboardResponse:
    return DashboardService(db).build(days=days)

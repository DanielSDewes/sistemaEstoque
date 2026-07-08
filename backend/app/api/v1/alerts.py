"""Alerts center endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.schemas.alerts import AlertsSummary, BelowMinimumItem, NearExpiryItem
from app.services.alerts import AlertsService

router = APIRouter(prefix="/alerts", tags=["Alertas"])


@router.get("/summary", response_model=AlertsSummary, summary="Resumo de alertas")
def alerts_summary(
    db: Session = Depends(get_db),
    _=Depends(require_permission("dashboard:view")),
) -> AlertsSummary:
    return AlertsService(db).summary()


@router.get(
    "/below-minimum",
    response_model=list[BelowMinimumItem],
    summary="Produtos abaixo do estoque minimo",
)
def below_minimum(
    db: Session = Depends(get_db),
    _=Depends(require_permission("product:view")),
) -> list[BelowMinimumItem]:
    return AlertsService(db).below_minimum()


@router.get(
    "/near-expiry",
    response_model=list[NearExpiryItem],
    summary="Produtos proximos do vencimento",
)
def near_expiry(
    within_days: int | None = Query(None, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_permission("product:view")),
) -> list[NearExpiryItem]:
    return AlertsService(db).near_expiry(within_days)

"""Stock movement endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_page_params, get_request_context, require_permission
from app.core.database import get_db
from app.core.pagination import Page, PageParams
from app.models.enums import MovementType
from app.repositories.movement import MovementRepository
from app.schemas.movement import MovementCancel, MovementCreate, MovementRead
from app.services.audit import RequestContext
from app.services.movement import MovementService

router = APIRouter(prefix="/movements", tags=["Movimentacoes"])


@router.get("", response_model=Page[MovementRead], summary="Listar/filtrar movimentacoes")
def list_movements(
    product_id: int | None = None,
    movement_type: MovementType | None = None,
    include_cancelled: bool = True,
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("product:view")),
) -> Page[MovementRead]:
    items, total = MovementRepository(db).paginate_filtered(
        params,
        product_id=product_id,
        movement_type=movement_type.value if movement_type else None,
        include_cancelled=include_cancelled,
    )
    return Page.create([MovementRead.model_validate(m) for m in items], total, params)


@router.post(
    "", response_model=MovementRead, status_code=status.HTTP_201_CREATED,
    summary="Registrar movimentacao",
)
def create_movement(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("movement:create")),
) -> MovementRead:
    movement = MovementService(db, ctx).create(payload)
    return MovementRead.model_validate(movement)


@router.post("/transfer", response_model=list[MovementRead], summary="Transferencia entre locais")
def transfer(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("movement:create")),
) -> list[MovementRead]:
    out, inbound = MovementService(db, ctx).create_transfer(payload)
    return [MovementRead.model_validate(out), MovementRead.model_validate(inbound)]


@router.post(
    "/{movement_id}/cancel", response_model=MovementRead,
    summary="Cancelar movimentacao (mantem historico)",
)
def cancel_movement(
    movement_id: int,
    payload: MovementCancel,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("movement:cancel")),
) -> MovementRead:
    movement = MovementService(db, ctx).cancel(movement_id, payload.reason)
    return MovementRead.model_validate(movement)


@router.get("/product/{product_id}/balance", summary="Saldo atual (derivado de movimentacoes)")
def product_balance(
    product_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("product:view")),
) -> dict[str, float]:
    return {"product_id": product_id, "balance": MovementService(db).current_balance(product_id)}

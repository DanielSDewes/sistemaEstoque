"""Sales order endpoints: CRUD plus confirm/cancel with stock effects."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_page_params, get_request_context, require_permission
from app.core.database import get_db
from app.core.pagination import Page, PageParams
from app.models.enums import OrderStatus
from app.schemas.common import Message
from app.schemas.order import (
    OrderCancel,
    OrderCreate,
    OrderRead,
    OrderUpdate,
    ProfitReport,
)
from app.services.audit import RequestContext
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["Pedidos"])


@router.get(
    "/reports/profit",
    response_model=ProfitReport,
    summary="Relatorio de lucro por periodo",
)
def profit_report(
    start: date | None = None,
    end: date | None = None,
    group_by: str = Query("month", pattern="^(day|month)$"),
    db: Session = Depends(get_db),
    _=Depends(require_permission("report:view")),
) -> ProfitReport:
    today = date.today()
    end = end or today
    start = start or (end - timedelta(days=365))
    return OrderService(db).profit_report(start, end, group_by)


@router.get("", response_model=Page[OrderRead], summary="Listar pedidos")
def list_orders(
    q: str | None = Query(None, description="Termo: numero do pedido ou nome do cliente"),
    customer_id: int | None = None,
    order_status: OrderStatus | None = Query(None, alias="status"),
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("order:view")),
) -> Page[OrderRead]:
    return OrderService(db).list(
        params, term=q, customer_id=customer_id, status=order_status
    )


@router.get("/{order_id}", response_model=OrderRead, summary="Detalhe do pedido")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("order:view")),
) -> OrderRead:
    return OrderService(db).get(order_id)


@router.post(
    "", response_model=OrderRead, status_code=status.HTTP_201_CREATED,
    summary="Criar pedido (rascunho)",
)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("order:create")),
) -> OrderRead:
    return OrderService(db, ctx).create(payload)


@router.put("/{order_id}", response_model=OrderRead, summary="Atualizar pedido (rascunho)")
def update_order(
    order_id: int,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("order:update")),
) -> OrderRead:
    return OrderService(db, ctx).update(order_id, payload)


@router.post(
    "/{order_id}/confirm",
    response_model=OrderRead,
    summary="Confirmar pedido (baixa estoque)",
)
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("order:confirm")),
) -> OrderRead:
    return OrderService(db, ctx).confirm(order_id)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderRead,
    summary="Cancelar pedido (estorna estoque)",
)
def cancel_order(
    order_id: int,
    payload: OrderCancel,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("order:cancel")),
) -> OrderRead:
    return OrderService(db, ctx).cancel(order_id, payload.reason)


@router.delete("/{order_id}", response_model=Message, summary="Excluir pedido (rascunho)")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("order:delete")),
) -> Message:
    OrderService(db, ctx).delete(order_id)
    return Message(detail="Pedido excluido")

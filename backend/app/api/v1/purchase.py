"""Purchase order endpoints: CRUD plus place/receive/cancel with stock effects."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_page_params, get_request_context, require_permission
from app.core.database import get_db
from app.core.pagination import Page, PageParams
from app.models.enums import PurchaseOrderStatus
from app.schemas.common import Message
from app.schemas.purchase import (
    PurchaseOrderCancel,
    PurchaseOrderCreate,
    PurchaseOrderRead,
    PurchaseOrderReceive,
    PurchaseOrderUpdate,
)
from app.services.audit import RequestContext
from app.services.purchase import PurchaseOrderService

router = APIRouter(prefix="/purchase-orders", tags=["Compras"])


@router.get("", response_model=Page[PurchaseOrderRead], summary="Listar pedidos de compra")
def list_purchase_orders(
    q: str | None = Query(None, description="Termo: numero da OC ou fornecedor"),
    supplier_id: int | None = None,
    po_status: PurchaseOrderStatus | None = Query(None, alias="status"),
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("purchase:view")),
) -> Page[PurchaseOrderRead]:
    return PurchaseOrderService(db).list(
        params, term=q, supplier_id=supplier_id, status=po_status
    )


@router.get("/{po_id}", response_model=PurchaseOrderRead, summary="Detalhe do pedido de compra")
def get_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("purchase:view")),
) -> PurchaseOrderRead:
    return PurchaseOrderService(db).get(po_id)


@router.post(
    "", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED,
    summary="Criar pedido de compra (rascunho)",
)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("purchase:create")),
) -> PurchaseOrderRead:
    return PurchaseOrderService(db, ctx).create(payload)


@router.put("/{po_id}", response_model=PurchaseOrderRead, summary="Atualizar pedido (rascunho)")
def update_purchase_order(
    po_id: int,
    payload: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("purchase:update")),
) -> PurchaseOrderRead:
    return PurchaseOrderService(db, ctx).update(po_id, payload)


@router.post(
    "/{po_id}/place",
    response_model=PurchaseOrderRead,
    summary="Emitir pedido de compra",
)
def place_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("purchase:place")),
) -> PurchaseOrderRead:
    return PurchaseOrderService(db, ctx).place(po_id)


@router.post(
    "/{po_id}/receive",
    response_model=PurchaseOrderRead,
    summary="Receber pedido de compra (entrada em estoque)",
)
def receive_purchase_order(
    po_id: int,
    payload: PurchaseOrderReceive,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("purchase:receive")),
) -> PurchaseOrderRead:
    return PurchaseOrderService(db, ctx).receive(po_id, payload)


@router.post(
    "/{po_id}/cancel",
    response_model=PurchaseOrderRead,
    summary="Cancelar pedido de compra",
)
def cancel_purchase_order(
    po_id: int,
    payload: PurchaseOrderCancel,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("purchase:cancel")),
) -> PurchaseOrderRead:
    return PurchaseOrderService(db, ctx).cancel(po_id, payload.reason)


@router.delete("/{po_id}", response_model=Message, summary="Excluir pedido de compra (rascunho)")
def delete_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("purchase:delete")),
) -> Message:
    PurchaseOrderService(db, ctx).delete(po_id)
    return Message(detail="Pedido de compra excluido")

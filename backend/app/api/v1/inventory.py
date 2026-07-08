"""Inventory (physical count) endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_page_params, get_request_context, require_permission
from app.core.database import get_db
from app.core.pagination import PageParams
from app.schemas.inventory import (
    InventoryCreate,
    InventoryDetail,
    InventoryItemCount,
    InventoryRead,
    InventorySummary,
)
from app.services.audit import RequestContext
from app.services.inventory import InventoryService

router = APIRouter(prefix="/inventories", tags=["Inventario"])


@router.get("", response_model=list[InventoryRead], summary="Listar inventarios")
def list_inventories(
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("inventory:count")),
) -> list[InventoryRead]:
    return InventoryService(db).list(params)


@router.post(
    "", response_model=InventoryDetail, status_code=status.HTTP_201_CREATED,
    summary="Criar inventario (gera itens conforme escopo)",
)
def create_inventory(
    payload: InventoryCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("inventory:create")),
) -> InventoryDetail:
    return InventoryService(db, ctx).create(payload)


@router.get("/{inventory_id}", response_model=InventoryDetail, summary="Detalhe do inventario")
def get_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("inventory:count")),
) -> InventoryDetail:
    return InventoryService(db).get_detail(inventory_id)


@router.get(
    "/{inventory_id}/summary", response_model=InventorySummary, summary="Resumo de divergencias"
)
def inventory_summary(
    inventory_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("inventory:count")),
) -> InventorySummary:
    return InventoryService(db).summary(inventory_id)


@router.patch(
    "/{inventory_id}/items/{item_id}",
    response_model=InventoryDetail,
    summary="Registrar contagem fisica de um item",
)
def register_count(
    inventory_id: int,
    item_id: int,
    payload: InventoryItemCount,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("inventory:count")),
) -> InventoryDetail:
    return InventoryService(db, ctx).register_count(inventory_id, item_id, payload)


@router.post("/{inventory_id}/finish", response_model=InventoryDetail, summary="Finalizar contagem")
def finish_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("inventory:count")),
) -> InventoryDetail:
    return InventoryService(db, ctx).finish(inventory_id)


@router.post(
    "/{inventory_id}/approve",
    response_model=InventoryDetail,
    summary="Aprovar e gerar ajustes automaticos de estoque",
)
def approve_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("inventory:approve")),
) -> InventoryDetail:
    return InventoryService(db, ctx).approve(inventory_id)

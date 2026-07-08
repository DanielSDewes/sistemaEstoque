"""Endpoints for product batches (lotes) and product locations."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_permission
from app.core.database import get_db
from app.schemas.common import Message
from app.schemas.location import ProductLocationCreate, ProductLocationRead
from app.schemas.product import BatchCreate, BatchRead
from app.services.audit import RequestContext
from app.services.stock_items import BatchService, ProductLocationService

router = APIRouter(tags=["Lotes e Localizacoes"])


# --- Batches (lotes) ---
@router.get(
    "/products/{product_id}/batches",
    response_model=list[BatchRead],
    summary="Lotes do produto",
)
def list_batches(
    product_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("product:view")),
) -> list[BatchRead]:
    return BatchService(db).list_for_product(product_id)


@router.post(
    "/batches", response_model=BatchRead, status_code=status.HTTP_201_CREATED, summary="Criar lote"
)
def create_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("product:update")),
) -> BatchRead:
    return BatchService(db, ctx).create(payload)


@router.delete("/batches/{batch_id}", response_model=Message, summary="Excluir lote")
def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("product:update")),
) -> Message:
    BatchService(db, ctx).delete(batch_id)
    return Message(detail="Lote excluido")


# --- Product locations ---
@router.get(
    "/products/{product_id}/locations",
    response_model=list[ProductLocationRead],
    summary="Localizacoes do produto",
)
def list_locations(
    product_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("product:view")),
) -> list[ProductLocationRead]:
    return ProductLocationService(db).list_for_product(product_id)


@router.post(
    "/product-locations",
    response_model=ProductLocationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Alocar produto em prateleira",
)
def assign_location(
    payload: ProductLocationCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("product:update")),
) -> ProductLocationRead:
    return ProductLocationService(db, ctx).assign(payload)


@router.delete(
    "/product-locations/{location_id}", response_model=Message, summary="Remover alocacao"
)
def remove_location(
    location_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("product:update")),
) -> Message:
    ProductLocationService(db, ctx).remove(location_id)
    return Message(detail="Alocacao removida")

"""Supplier router plus product<->supplier link endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_permission
from app.api.v1._crud_factory import build_crud_router
from app.core.database import get_db
from app.schemas.common import Message
from app.schemas.supplier import (
    ProductSupplierCreate,
    ProductSupplierRead,
    ProductSupplierUpdate,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
)
from app.services.audit import RequestContext
from app.services.supplier import ProductSupplierService, SupplierService

suppliers_router = build_crud_router(
    prefix="/suppliers", tag="Fornecedores", permission="supplier",
    service_cls=SupplierService,
    create_schema=SupplierCreate, update_schema=SupplierUpdate, read_schema=SupplierRead,
)

# --- Product <-> Supplier links ---
product_suppliers_router = APIRouter(prefix="/product-suppliers", tags=["Fornecedores"])


@product_suppliers_router.get(
    "/product/{product_id}",
    response_model=list[ProductSupplierRead],
    summary="Fornecedores de um produto",
)
def list_for_product(
    product_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("supplier:view")),
) -> list[ProductSupplierRead]:
    return ProductSupplierService(db).list_for_product(product_id)


@product_suppliers_router.post(
    "", response_model=ProductSupplierRead, status_code=status.HTTP_201_CREATED,
    summary="Vincular fornecedor a produto",
)
def link_supplier(
    payload: ProductSupplierCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("supplier:update")),
) -> ProductSupplierRead:
    return ProductSupplierService(db, ctx).link(payload)


@product_suppliers_router.put(
    "/{link_id}",
    response_model=ProductSupplierRead,
    summary="Atualizar vinculo (com historico de preco)",
)
def update_link(
    link_id: int,
    payload: ProductSupplierUpdate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("supplier:update")),
) -> ProductSupplierRead:
    return ProductSupplierService(db, ctx).update(link_id, payload)


@product_suppliers_router.delete(
    "/{link_id}", response_model=Message, summary="Remover vinculo"
)
def unlink(
    link_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("supplier:update")),
) -> Message:
    ProductSupplierService(db, ctx).unlink(link_id)
    return Message(detail="Vinculo removido")

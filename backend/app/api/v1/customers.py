"""Customer endpoints: CRUD, search and per-customer sales history."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_page_params, get_request_context, require_permission
from app.core.database import get_db
from app.core.pagination import Page, PageParams
from app.schemas.common import Message
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.schemas.order import OrderRead
from app.services.audit import RequestContext
from app.services.customer import CustomerService
from app.services.order import OrderService

router = APIRouter(prefix="/customers", tags=["Clientes"])


@router.get("", response_model=Page[CustomerRead], summary="Buscar clientes")
def list_customers(
    q: str | None = Query(None, description="Termo: nome, telefone ou documento"),
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("customer:view")),
) -> Page[CustomerRead]:
    return CustomerService(db).search(params, q)


@router.get("/{customer_id}", response_model=CustomerRead, summary="Detalhe do cliente")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("customer:view")),
) -> CustomerRead:
    return CustomerService(db).get(customer_id)


@router.get(
    "/{customer_id}/orders",
    response_model=Page[OrderRead],
    summary="Historico de vendas do cliente",
)
def customer_orders(
    customer_id: int,
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("order:view")),
) -> Page[OrderRead]:
    return OrderService(db).list_for_customer(customer_id, params)


@router.post(
    "", response_model=CustomerRead, status_code=status.HTTP_201_CREATED,
    summary="Criar cliente",
)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("customer:create")),
) -> CustomerRead:
    return CustomerService(db, ctx).create(payload)


@router.put("/{customer_id}", response_model=CustomerRead, summary="Atualizar cliente")
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("customer:update")),
) -> CustomerRead:
    return CustomerService(db, ctx).update(customer_id, payload)


@router.delete("/{customer_id}", response_model=Message, summary="Excluir cliente")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("customer:delete")),
) -> Message:
    CustomerService(db, ctx).delete(customer_id)
    return Message(detail="Cliente excluido")

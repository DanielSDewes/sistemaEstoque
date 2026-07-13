"""Product endpoints: CRUD, smart search, history, photo upload and import."""
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_page_params, get_request_context, require_permission
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ValidationAppError
from app.core.pagination import Page, PageParams
from app.core.storage import ALLOWED_IMAGE_TYPES, save_product_photo, sniff_image_type
from app.repositories.movement import MovementRepository
from app.schemas.common import Message
from app.schemas.movement import MovementRead
from app.schemas.product import ImportResult, ProductCreate, ProductRead, ProductUpdate
from app.services.audit import RequestContext
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["Produtos"])


def _reject_if_too_large(file: UploadFile) -> None:
    """Reject oversized uploads up front, before buffering the body in memory."""
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if file.size is not None and file.size > max_bytes:
        raise ValidationAppError(f"Arquivo excede {settings.MAX_UPLOAD_MB} MB")


@router.get("", response_model=Page[ProductRead], summary="Busca inteligente de produtos")
def search_products(
    q: str | None = Query(None, description="Termo: codigo, barras, SKU, nome, categoria..."),
    category_id: int | None = None,
    group_id: int | None = None,
    brand_id: int | None = None,
    supplier_id: int | None = None,
    corridor_id: int | None = None,
    shelf_id: int | None = None,
    is_active: bool | None = None,
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("product:view")),
) -> Page[ProductRead]:
    return ProductService(db).search(
        params,
        term=q,
        category_id=category_id,
        group_id=group_id,
        brand_id=brand_id,
        supplier_id=supplier_id,
        corridor_id=corridor_id,
        shelf_id=shelf_id,
        is_active=is_active,
    )


@router.get("/{product_id}", response_model=ProductRead, summary="Detalhe do produto")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("product:view")),
) -> ProductRead:
    return ProductService(db).get(product_id)


@router.get(
    "/{product_id}/history",
    response_model=Page[MovementRead],
    summary="Historico de movimentacoes do produto",
)
def product_history(
    product_id: int,
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("product:view")),
) -> Page[MovementRead]:
    repo = MovementRepository(db)
    items, total = repo.paginate_filtered(params, product_id=product_id)
    return Page.create([MovementRead.model_validate(m) for m in items], total, params)


@router.post(
    "", response_model=ProductRead, status_code=status.HTTP_201_CREATED, summary="Criar produto"
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("product:create")),
) -> ProductRead:
    return ProductService(db, ctx).create(payload)


@router.put("/{product_id}", response_model=ProductRead, summary="Atualizar produto")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("product:update")),
) -> ProductRead:
    return ProductService(db, ctx).update(product_id, payload)


@router.delete("/{product_id}", response_model=Message, summary="Excluir produto")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("product:delete")),
) -> Message:
    ProductService(db, ctx).delete(product_id)
    return Message(detail="Produto excluido")


@router.post(
    "/{product_id}/photo", response_model=ProductRead, summary="Enviar foto do produto"
)
async def upload_photo(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("product:update")),
) -> ProductRead:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationAppError("Formato de imagem nao suportado (use JPG, PNG, WEBP ou GIF)")
    _reject_if_too_large(file)
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationAppError(f"Arquivo excede {settings.MAX_UPLOAD_MB} MB")
    # Trust the file's magic bytes, not the client-supplied Content-Type.
    real_type = sniff_image_type(content)
    if real_type is None:
        raise ValidationAppError("Arquivo nao e uma imagem valida (JPG, PNG, WEBP ou GIF)")
    url = save_product_photo(content, real_type)
    return ProductService(db, ctx).set_photo(product_id, url)


@router.post(
    "/import", response_model=ImportResult, summary="Importar produtos via CSV (upsert)"
)
async def import_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("product:create")),
) -> ImportResult:
    _reject_if_too_large(file)
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationAppError(f"Arquivo excede {settings.MAX_UPLOAD_MB} MB")
    return ProductService(db, ctx).import_csv(content)

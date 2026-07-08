"""Product service - CRUD, smart search and movement-derived stock figures."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.money import to_decimal
from app.core.pagination import Page, PageParams
from app.models.enums import AuditAction
from app.models.movement import StockMovement
from app.models.product import Product
from app.repositories.movement import MovementRepository
from app.repositories.product import ProductRepository
from app.schemas.product import (
    ImportResult,
    ProductCreate,
    ProductRead,
    ProductStock,
    ProductUpdate,
)
from app.services.audit import AuditService, RequestContext


class ProductService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = ProductRepository(db)
        self.movements = MovementRepository(db)
        self.audit = AuditService(db, self.ctx)

    # --- read helpers ---
    def _build_stock(self, product: Product, balance: Decimal | None = None) -> ProductStock:
        current = (
            self.movements.current_balance(product.id) if balance is None else to_decimal(balance)
        )
        reserved = to_decimal(product.reserved_stock)
        min_stock = to_decimal(product.min_stock)
        return ProductStock(
            current=current,
            reserved=reserved,
            available=current - reserved,
            min_stock=min_stock,
            max_stock=to_decimal(product.max_stock),
            reorder_point=to_decimal(product.reorder_point),
            below_minimum=current < min_stock,
        )

    def to_read(self, product: Product, balance: Decimal | None = None) -> ProductRead:
        dto = ProductRead.model_validate(product)
        dto.stock = self._build_stock(product, balance)
        return dto

    def get(self, product_id: int) -> ProductRead:
        product = self.repo.get(product_id)
        if not product:
            raise NotFoundError("Produto nao encontrado")
        return self.to_read(product)

    def search(self, params: PageParams, **filters) -> Page[ProductRead]:
        stmt = self.repo.build_search(**filters)
        items, total = self.repo.paginate(params, stmt)
        balances = self.movements.balances_for([p.id for p in items])
        reads = [self.to_read(p, balances.get(p.id, 0.0)) for p in items]
        return Page.create(reads, total, params)

    # --- write ---
    def create(self, data: ProductCreate) -> ProductRead:
        if self.repo.get_by_internal_code(data.internal_code):
            raise ConflictError("Ja existe um produto com este codigo interno")
        product = self.repo.create(**data.model_dump())
        self.audit.log(
            AuditAction.CREATE, entity="Product", entity_id=product.id, new_value=product.name
        )
        self.db.commit()
        self.db.refresh(product)
        return self.to_read(product)

    def update(self, product_id: int, data: ProductUpdate) -> ProductRead:
        product = self.repo.get(product_id)
        if not product:
            raise NotFoundError("Produto nao encontrado")

        changes = data.model_dump(exclude_unset=True)
        before = {k: getattr(product, k) for k in changes}
        self.repo.update(product, changes)
        self.audit.log_diff(AuditAction.UPDATE, "Product", product.id, before, changes)
        self.db.commit()
        self.db.refresh(product)
        return self.to_read(product)

    def delete(self, product_id: int) -> None:
        product = self.repo.get(product_id)
        if not product:
            raise NotFoundError("Produto nao encontrado")
        has_movements = self.db.execute(
            select(StockMovement.id).where(StockMovement.product_id == product_id).limit(1)
        ).first()
        if has_movements:
            raise BusinessRuleError(
                "Nao e possivel excluir produtos com movimentacoes. Inative o produto."
            )
        self.audit.log(
            AuditAction.DELETE, entity="Product", entity_id=product.id, old_value=product.name
        )
        self.repo.delete(product)
        self.db.commit()

    def set_photo(self, product_id: int, url: str) -> ProductRead:
        product = self.repo.get(product_id)
        if not product:
            raise NotFoundError("Produto nao encontrado")
        old = product.photo_url
        product.photo_url = url
        self.db.flush()
        self.audit.log(
            AuditAction.UPDATE, entity="Product", entity_id=product.id,
            field="photo_url", old_value=old, new_value=url,
        )
        self.db.commit()
        self.db.refresh(product)
        return self.to_read(product)

    def import_csv(self, content: bytes) -> ImportResult:
        """Bulk create/update products from a CSV (upsert by internal_code)."""
        import csv
        import io

        result = ImportResult()
        text = content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        num_fields = {"min_stock", "max_stock", "reorder_point", "reserved_stock", "sale_price"}
        for line_no, raw in enumerate(reader, start=2):
            row = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
            code = row.get("internal_code")
            name = row.get("name")
            if not code or not name:
                result.errors.append(
                    {"line": line_no, "error": "internal_code e name obrigatorios"}
                )
                continue
            try:
                fields: dict[str, object] = {"internal_code": code, "name": name}
                for key in ("barcode", "sku", "unit", "short_name", "ncm"):
                    if row.get(key):
                        fields[key] = row[key]
                for key in num_fields:
                    if row.get(key):
                        fields[key] = float(row[key])
                existing = self.repo.get_by_internal_code(code)
                if existing:
                    self.repo.update(existing, {k: v for k, v in fields.items()
                                                if k != "internal_code"})
                    result.updated += 1
                else:
                    self.repo.create(**fields)
                    result.created += 1
            except (ValueError, TypeError) as exc:
                result.errors.append({"line": line_no, "error": str(exc)})
        self.audit.log(
            AuditAction.CREATE, entity="Product", field="import",
            new_value=f"import CSV: {result.created} criados, {result.updated} atualizados",
        )
        self.db.commit()
        return result

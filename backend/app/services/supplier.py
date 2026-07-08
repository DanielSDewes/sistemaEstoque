"""Supplier and product-supplier services, with price-change history."""
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import AuditAction
from app.models.supplier import ProductSupplier, Supplier, SupplierPriceHistory
from app.repositories.supplier import ProductSupplierRepository, SupplierRepository
from app.schemas.supplier import (
    ProductSupplierCreate,
    ProductSupplierRead,
    ProductSupplierUpdate,
    SupplierRead,
)
from app.services.audit import AuditService, RequestContext
from app.services.base import CrudService


class SupplierService(CrudService):
    model = Supplier
    read_schema = SupplierRead
    entity_name = "Fornecedor"

    def _pre_create(self, data: dict) -> None:
        if SupplierRepository(self.db).get_by_cnpj(data["cnpj"]):
            raise ConflictError("Ja existe fornecedor com este CNPJ")


class ProductSupplierService:
    """Manages the product<->supplier links and keeps price history."""

    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = ProductSupplierRepository(db)
        self.audit = AuditService(db, self.ctx)

    def list_for_product(self, product_id: int) -> list[ProductSupplierRead]:
        return [ProductSupplierRead.model_validate(ps) for ps in self.repo.for_product(product_id)]

    def link(self, data: ProductSupplierCreate) -> ProductSupplierRead:
        if self.repo.get_by(product_id=data.product_id, supplier_id=data.supplier_id):
            raise ConflictError("Fornecedor ja vinculado a este produto")
        if data.is_primary:
            self.repo.clear_primary(data.product_id)

        ps = ProductSupplier(
            **data.model_dump(),
            last_price=data.current_price,
            average_price=data.current_price,
        )
        self.repo.add(ps)
        self.audit.log(
            AuditAction.CREATE,
            entity="ProductSupplier",
            entity_id=ps.id,
            new_value=f"produto {data.product_id} <- fornecedor {data.supplier_id}",
        )
        self.db.commit()
        self.db.refresh(ps)
        return ProductSupplierRead.model_validate(ps)

    def update(self, link_id: int, data: ProductSupplierUpdate) -> ProductSupplierRead:
        ps = self.repo.get(link_id)
        if not ps:
            raise NotFoundError("Vinculo produto-fornecedor nao encontrado")

        changes = data.model_dump(exclude_unset=True)

        # Track price changes into history and recompute the rolling average.
        if "current_price" in changes and changes["current_price"] != ps.current_price:
            old_price = ps.current_price
            new_price = changes["current_price"]
            self.db.add(
                SupplierPriceHistory(
                    product_supplier_id=ps.id,
                    old_price=old_price,
                    new_price=new_price,
                    changed_by_id=self.ctx.user.id if self.ctx.user else None,
                )
            )
            ps.last_price = old_price
            prices = [p for p in (old_price, new_price) if p is not None]
            if prices:
                ps.average_price = sum(prices) / len(prices)
            self.audit.log(
                AuditAction.UPDATE,
                entity="ProductSupplier",
                entity_id=ps.id,
                field="current_price",
                old_value=old_price,
                new_value=new_price,
            )

        if changes.get("is_primary"):
            self.repo.clear_primary(ps.product_id)

        for key, value in changes.items():
            setattr(ps, key, value)
        self.db.flush()
        self.db.commit()
        self.db.refresh(ps)
        return ProductSupplierRead.model_validate(ps)

    def unlink(self, link_id: int) -> None:
        ps = self.repo.get(link_id)
        if not ps:
            raise NotFoundError("Vinculo produto-fornecedor nao encontrado")
        self.audit.log(AuditAction.DELETE, entity="ProductSupplier", entity_id=ps.id)
        self.repo.delete(ps)
        self.db.commit()

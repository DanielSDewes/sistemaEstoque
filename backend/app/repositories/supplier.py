"""Supplier and product-supplier repositories."""
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models.supplier import ProductSupplier, Supplier
from app.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, db: Session) -> None:
        super().__init__(Supplier, db)

    def get_by_cnpj(self, cnpj: str) -> Supplier | None:
        return self.get_by(cnpj=cnpj)

    def search(self, term: str | None) -> Select:
        stmt = select(Supplier)
        if term:
            like = f"%{term.strip()}%"
            stmt = stmt.where(
                or_(
                    Supplier.legal_name.ilike(like),
                    Supplier.trade_name.ilike(like),
                    Supplier.cnpj.ilike(like),
                )
            )
        return stmt


class ProductSupplierRepository(BaseRepository[ProductSupplier]):
    def __init__(self, db: Session) -> None:
        super().__init__(ProductSupplier, db)

    def for_product(self, product_id: int) -> list[ProductSupplier]:
        stmt = select(ProductSupplier).where(ProductSupplier.product_id == product_id)
        return list(self.db.execute(stmt).scalars().all())

    def clear_primary(self, product_id: int) -> None:
        for ps in self.for_product(product_id):
            if ps.is_primary:
                ps.is_primary = False
        self.db.flush()

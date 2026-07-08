"""Product repository with advanced search across many attributes."""
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models.catalog import Brand, Category, Group
from app.models.location import Corridor, ProductLocation, Shelf
from app.models.product import Product
from app.models.supplier import ProductSupplier, Supplier
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session) -> None:
        super().__init__(Product, db)

    def build_search(
        self,
        term: str | None = None,
        category_id: int | None = None,
        group_id: int | None = None,
        brand_id: int | None = None,
        supplier_id: int | None = None,
        corridor_id: int | None = None,
        shelf_id: int | None = None,
        is_active: bool | None = None,
    ) -> Select:
        """Compose a filtered product query for the smart search endpoint."""
        stmt = select(Product).distinct()

        if term:
            like = f"%{term.strip()}%"
            stmt = (
                stmt.outerjoin(Category, Product.category_id == Category.id)
                .outerjoin(Group, Product.group_id == Group.id)
                .outerjoin(Brand, Product.brand_id == Brand.id)
            )
            stmt = stmt.where(
                or_(
                    Product.internal_code.ilike(like),
                    Product.barcode.ilike(like),
                    Product.sku.ilike(like),
                    Product.name.ilike(like),
                    Product.short_name.ilike(like),
                    Category.name.ilike(like),
                    Group.name.ilike(like),
                    Brand.name.ilike(like),
                )
            )

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if group_id is not None:
            stmt = stmt.where(Product.group_id == group_id)
        if brand_id is not None:
            stmt = stmt.where(Product.brand_id == brand_id)
        if is_active is not None:
            stmt = stmt.where(Product.is_active.is_(is_active))

        if supplier_id is not None:
            stmt = stmt.join(ProductSupplier, ProductSupplier.product_id == Product.id).where(
                ProductSupplier.supplier_id == supplier_id
            )
        if corridor_id is not None or shelf_id is not None:
            stmt = stmt.join(ProductLocation, ProductLocation.product_id == Product.id)
            if corridor_id is not None:
                stmt = stmt.where(ProductLocation.corridor_id == corridor_id)
            if shelf_id is not None:
                stmt = stmt.where(ProductLocation.shelf_id == shelf_id)

        return stmt

    def get_by_internal_code(self, code: str) -> Product | None:
        return self.get_by(internal_code=code)

    def get_by_barcode(self, barcode: str) -> Product | None:
        return self.get_by(barcode=barcode)


# Re-exported so services can reference joined tables if needed.
__all__ = ["ProductRepository", "Supplier", "Shelf", "Corridor"]

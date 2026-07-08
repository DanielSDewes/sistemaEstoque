"""Services for product batches (lotes) and product locations."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import AuditAction
from app.models.location import ProductLocation
from app.models.product import Batch
from app.repositories.base import BaseRepository
from app.schemas.location import ProductLocationCreate, ProductLocationRead
from app.schemas.product import BatchCreate, BatchRead
from app.services.audit import AuditService, RequestContext


class BatchService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = BaseRepository(Batch, db)
        self.audit = AuditService(db, self.ctx)

    def list_for_product(self, product_id: int) -> list[BatchRead]:
        stmt = select(Batch).where(Batch.product_id == product_id).order_by(Batch.expiry_date)
        return [BatchRead.model_validate(b) for b in self.db.execute(stmt).scalars().all()]

    def create(self, data: BatchCreate) -> BatchRead:
        batch = self.repo.create(**data.model_dump())
        self.audit.log(
            AuditAction.CREATE, entity="Batch", entity_id=batch.id, new_value=batch.lot_number
        )
        self.db.commit()
        self.db.refresh(batch)
        return BatchRead.model_validate(batch)

    def delete(self, batch_id: int) -> None:
        batch = self.repo.get(batch_id)
        if not batch:
            raise NotFoundError("Lote nao encontrado")
        self.audit.log(AuditAction.DELETE, entity="Batch", entity_id=batch.id)
        self.repo.delete(batch)
        self.db.commit()


class ProductLocationService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = BaseRepository(ProductLocation, db)
        self.audit = AuditService(db, self.ctx)

    def list_for_product(self, product_id: int) -> list[ProductLocationRead]:
        from app.repositories.movement import MovementRepository

        stmt = select(ProductLocation).where(ProductLocation.product_id == product_id)
        per_shelf = MovementRepository(self.db).balance_by_location(product_id)
        result = []
        for loc in self.db.execute(stmt).scalars():
            dto = ProductLocationRead.model_validate(loc)
            dto.stock_balance = float(per_shelf.get(loc.shelf_id, 0))
            result.append(dto)
        return result

    def assign(self, data: ProductLocationCreate) -> ProductLocationRead:
        if self.repo.get_by(product_id=data.product_id, shelf_id=data.shelf_id):
            raise ConflictError("Produto ja alocado nesta prateleira")
        loc = self.repo.create(**data.model_dump())
        self.audit.log(
            AuditAction.CREATE,
            entity="ProductLocation",
            entity_id=loc.id,
            new_value=f"produto {data.product_id} -> prateleira {data.shelf_id}",
        )
        self.db.commit()
        self.db.refresh(loc)
        return ProductLocationRead.model_validate(loc)

    def remove(self, location_id: int) -> None:
        loc = self.repo.get(location_id)
        if not loc:
            raise NotFoundError("Alocacao nao encontrada")
        self.audit.log(AuditAction.DELETE, entity="ProductLocation", entity_id=loc.id)
        self.repo.delete(loc)
        self.db.commit()

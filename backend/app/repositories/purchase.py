"""Purchase order repository."""
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.enums import PurchaseOrderStatus
from app.models.purchase import PurchaseOrder
from app.models.supplier import Supplier
from app.repositories.base import BaseRepository


class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    def __init__(self, db: Session) -> None:
        super().__init__(PurchaseOrder, db)

    def search(
        self,
        term: str | None = None,
        supplier_id: int | None = None,
        status: PurchaseOrderStatus | None = None,
    ) -> Select:
        stmt = select(PurchaseOrder)
        if term:
            like = f"%{term.strip()}%"
            stmt = stmt.join(Supplier).where(
                PurchaseOrder.number.ilike(like)
                | Supplier.legal_name.ilike(like)
                | Supplier.trade_name.ilike(like)
            )
        if supplier_id is not None:
            stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)
        if status is not None:
            stmt = stmt.where(PurchaseOrder.status == status)
        return stmt

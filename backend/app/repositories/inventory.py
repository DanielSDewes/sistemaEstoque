"""Inventory repository."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory, InventoryItem
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self, db: Session) -> None:
        super().__init__(Inventory, db)

    def get_by_code(self, code: str) -> Inventory | None:
        return self.get_by(code=code)


class InventoryItemRepository(BaseRepository[InventoryItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(InventoryItem, db)

    def items_for(self, inventory_id: int) -> list[InventoryItem]:
        stmt = select(InventoryItem).where(InventoryItem.inventory_id == inventory_id)
        return list(self.db.execute(stmt).scalars().all())

"""Inventory service - count sessions and auto-reconciliation on approval."""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.enums import (
    AuditAction,
    InventoryScope,
    InventoryStatus,
    MovementType,
)
from app.models.inventory import Inventory, InventoryItem
from app.models.location import ProductLocation
from app.models.product import Product
from app.repositories.inventory import InventoryItemRepository, InventoryRepository
from app.repositories.movement import MovementRepository
from app.schemas.inventory import (
    InventoryCreate,
    InventoryDetail,
    InventoryItemCount,
    InventoryRead,
    InventorySummary,
)
from app.schemas.movement import MovementCreate
from app.services.audit import AuditService, RequestContext
from app.services.movement import MovementService


class InventoryService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = InventoryRepository(db)
        self.items = InventoryItemRepository(db)
        self.movements = MovementRepository(db)
        self.audit = AuditService(db, self.ctx)

    def _products_in_scope(self, scope: InventoryScope, ref_id: int | None) -> list[Product]:
        stmt = select(Product).where(Product.is_active.is_(True))
        if scope == InventoryScope.CATEGORY:
            stmt = stmt.where(Product.category_id == ref_id)
        elif scope == InventoryScope.GROUP:
            stmt = stmt.where(Product.group_id == ref_id)
        elif scope == InventoryScope.CORRIDOR:
            stmt = stmt.join(ProductLocation).where(ProductLocation.corridor_id == ref_id)
        elif scope == InventoryScope.SHELF:
            stmt = stmt.join(ProductLocation).where(ProductLocation.shelf_id == ref_id)
        return list(self.db.execute(stmt.distinct()).scalars().all())

    def create(self, data: InventoryCreate) -> InventoryDetail:
        if self.repo.get_by_code(data.code):
            raise ConflictError("Ja existe um inventario com este codigo")
        if data.scope != InventoryScope.ALL and data.scope_ref_id is None:
            raise BusinessRuleError("Escopo selecionado exige uma referencia (scope_ref_id)")

        inventory = Inventory(
            code=data.code,
            description=data.description,
            scope=data.scope,
            scope_ref_id=data.scope_ref_id,
            status=InventoryStatus.OPEN,
            created_by_id=self.ctx.user.id if self.ctx.user else None,
        )
        self.repo.add(inventory)

        products = self._products_in_scope(data.scope, data.scope_ref_id)
        balances = self.movements.balances_for([p.id for p in products])
        for product in products:
            self.db.add(
                InventoryItem(
                    inventory_id=inventory.id,
                    product_id=product.id,
                    system_quantity=balances.get(product.id, 0.0),
                )
            )
        self.db.flush()
        self.audit.log(
            AuditAction.CREATE, entity="Inventory", entity_id=inventory.id, new_value=inventory.code
        )
        self.db.commit()
        self.db.refresh(inventory)
        return self.get_detail(inventory.id)

    def get_detail(self, inventory_id: int) -> InventoryDetail:
        inv = self.repo.get(inventory_id)
        if not inv:
            raise NotFoundError("Inventario nao encontrado")
        return InventoryDetail.model_validate(inv)

    def list(self, params) -> list[InventoryRead]:  # noqa: ANN001
        items, _ = self.repo.paginate(params)
        return [InventoryRead.model_validate(i) for i in items]

    def register_count(
        self, inventory_id: int, item_id: int, data: InventoryItemCount
    ) -> InventoryDetail:
        inv = self.repo.get(inventory_id)
        if not inv:
            raise NotFoundError("Inventario nao encontrado")
        if inv.status in (InventoryStatus.APPROVED, InventoryStatus.CANCELLED):
            raise BusinessRuleError("Inventario nao permite mais contagens")

        item = self.items.get(item_id)
        if not item or item.inventory_id != inventory_id:
            raise NotFoundError("Item de inventario nao encontrado")

        item.counted_quantity = data.counted_quantity
        item.notes = data.notes
        item.counted_at = datetime.now(UTC)
        item.counted_by_id = self.ctx.user.id if self.ctx.user else None

        if inv.status == InventoryStatus.OPEN:
            inv.status = InventoryStatus.IN_PROGRESS
        self.db.flush()
        self.db.commit()
        return self.get_detail(inventory_id)

    def summary(self, inventory_id: int) -> InventorySummary:
        items = self.items.items_for(inventory_id)
        surplus = sum(i.difference for i in items if i.difference and i.difference > 0)
        shortage = sum(-i.difference for i in items if i.difference and i.difference < 0)
        counted = sum(1 for i in items if i.counted_quantity is not None)
        return InventorySummary(
            total_items=len(items),
            counted_items=counted,
            surplus_qty=float(surplus),
            shortage_qty=float(shortage),
            net_difference=float(surplus - shortage),
        )

    def finish(self, inventory_id: int) -> InventoryDetail:
        inv = self.repo.get(inventory_id)
        if not inv:
            raise NotFoundError("Inventario nao encontrado")
        if inv.status not in (InventoryStatus.IN_PROGRESS, InventoryStatus.OPEN):
            raise BusinessRuleError("Somente inventarios em andamento podem ser finalizados")
        inv.status = InventoryStatus.FINISHED
        self.db.flush()
        self.audit.log(
            AuditAction.UPDATE, entity="Inventory", entity_id=inv.id, new_value="finalizado"
        )
        self.db.commit()
        return self.get_detail(inventory_id)

    def approve(self, inventory_id: int) -> InventoryDetail:
        """Approve and auto-generate adjustment movements for every divergence."""
        inv = self.repo.get(inventory_id)
        if not inv:
            raise NotFoundError("Inventario nao encontrado")
        if inv.status != InventoryStatus.FINISHED:
            raise BusinessRuleError("Somente inventarios finalizados podem ser aprovados")

        movement_service = MovementService(self.db, self.ctx)
        for item in self.items.items_for(inventory_id):
            diff = item.difference
            if not diff:
                continue
            mtype = (
                MovementType.ADJUSTMENT_IN if diff > 0 else MovementType.ADJUSTMENT_OUT
            )
            movement_service.create(
                MovementCreate(
                    product_id=item.product_id,
                    movement_type=mtype,
                    quantity=abs(diff),
                    reason=f"Ajuste inventario {inv.code}",
                    document=inv.code,
                ),
                inventory_id=inv.id,
            )

        inv.status = InventoryStatus.APPROVED
        inv.approved_by_id = self.ctx.user.id if self.ctx.user else None
        inv.approved_at = datetime.now(UTC)
        self.db.flush()
        self.audit.log(AuditAction.APPROVE, entity="Inventory", entity_id=inv.id)
        self.db.commit()
        return self.get_detail(inventory_id)

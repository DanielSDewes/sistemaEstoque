"""Purchase order service.

Draft -> placed -> received. Only *receiving* touches stock: it generates one
inbound ``compra`` movement per received quantity (via ``MovementService``), so
the weighted moving-average cost and the balance stay derived from movements.
All movements in a single receipt share one transaction.
"""
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError, ValidationAppError
from app.core.money import q_cost, q_money, q_qty, to_decimal
from app.core.pagination import Page, PageParams
from app.models.enums import AuditAction, MovementType, PurchaseOrderStatus
from app.models.product import Product
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.supplier import Supplier
from app.repositories.purchase import PurchaseOrderRepository
from app.schemas.movement import MovementCreate
from app.schemas.purchase import (
    PurchaseOrderCreate,
    PurchaseOrderItemRead,
    PurchaseOrderRead,
    PurchaseOrderReceive,
    PurchaseOrderUpdate,
)
from app.services.audit import AuditService, RequestContext
from app.services.dashboard import invalidate_dashboard_cache
from app.services.movement import MovementService


class PurchaseOrderService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = PurchaseOrderRepository(db)
        self.audit = AuditService(db, self.ctx)

    # --- helpers ---
    @staticmethod
    def _supplier_name(supplier: Supplier) -> str:
        return supplier.trade_name or supplier.legal_name

    def _to_read(self, po: PurchaseOrder) -> PurchaseOrderRead:
        return PurchaseOrderRead(
            id=po.id,
            number=po.number,
            supplier_id=po.supplier_id,
            supplier_name=self._supplier_name(po.supplier),
            status=po.status,
            order_date=po.order_date,
            expected_date=po.expected_date,
            notes=po.notes,
            total_amount=float(po.total_amount),
            extra_cost=float(po.extra_cost),
            items=[
                PurchaseOrderItemRead(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product.name,
                    product_code=item.product.internal_code,
                    quantity=float(item.quantity),
                    unit_cost=float(item.unit_cost),
                    received_quantity=float(item.received_quantity),
                    pending_quantity=float(
                        to_decimal(item.quantity) - to_decimal(item.received_quantity)
                    ),
                    line_total=float(item.line_total),
                )
                for item in po.items
            ],
            placed_at=po.placed_at,
            received_at=po.received_at,
            cancelled_at=po.cancelled_at,
        )

    def _get(self, po_id: int) -> PurchaseOrder:
        po = self.repo.get(po_id)
        if not po:
            raise NotFoundError("Pedido de compra nao encontrado")
        return po

    def _active_product(self, product_id: int) -> Product:
        product = self.db.get(Product, product_id)
        if not product:
            raise NotFoundError(f"Produto {product_id} nao encontrado")
        if not product.is_active:
            raise BusinessRuleError(f"Produto '{product.name}' esta inativo")
        return product

    def _build_items(self, po: PurchaseOrder, items_data: list) -> None:
        po.items = []
        total = q_money(0)
        for item in items_data:
            self._active_product(item.product_id)
            qty = q_qty(item.quantity)
            cost = q_cost(item.unit_cost)
            line_total = q_money(qty * cost)
            total += line_total
            po.items.append(
                PurchaseOrderItem(
                    product_id=item.product_id,
                    quantity=qty,
                    unit_cost=cost,
                    line_total=line_total,
                    received_quantity=q_qty(0),
                )
            )
        po.total_amount = total

    # --- read ---
    def get(self, po_id: int) -> PurchaseOrderRead:
        return self._to_read(self._get(po_id))

    def list(
        self,
        params: PageParams,
        term: str | None = None,
        supplier_id: int | None = None,
        status: PurchaseOrderStatus | None = None,
    ) -> Page[PurchaseOrderRead]:
        stmt = self.repo.search(term=term, supplier_id=supplier_id, status=status)
        items, total = self.repo.paginate(params, stmt)
        return Page.create([self._to_read(p) for p in items], total, params)

    # --- write ---
    def create(self, data: PurchaseOrderCreate) -> PurchaseOrderRead:
        supplier = self.db.get(Supplier, data.supplier_id)
        if not supplier:
            raise NotFoundError("Fornecedor nao encontrado")

        po = PurchaseOrder(
            supplier_id=supplier.id,
            order_date=data.order_date or datetime.now(UTC),
            expected_date=data.expected_date,
            notes=data.notes,
            extra_cost=q_money(data.extra_cost),
            status=PurchaseOrderStatus.DRAFT,
        )
        self._build_items(po, data.items)
        self.repo.add(po)  # flush -> assigns po.id
        po.number = f"OC-{po.id:06d}"
        self.audit.log(
            AuditAction.CREATE, entity="PedidoCompra", entity_id=po.id, new_value=po.number
        )
        self.db.commit()
        self.db.refresh(po)
        return self._to_read(po)

    def update(self, po_id: int, data: PurchaseOrderUpdate) -> PurchaseOrderRead:
        po = self._get(po_id)
        if po.status != PurchaseOrderStatus.DRAFT:
            raise BusinessRuleError("Somente pedidos de compra em rascunho podem ser editados")

        if data.supplier_id is not None:
            if not self.db.get(Supplier, data.supplier_id):
                raise NotFoundError("Fornecedor nao encontrado")
            po.supplier_id = data.supplier_id
        if data.order_date is not None:
            po.order_date = data.order_date
        if "expected_date" in data.model_fields_set:
            po.expected_date = data.expected_date
        if "notes" in data.model_fields_set:
            po.notes = data.notes
        if data.extra_cost is not None:
            po.extra_cost = q_money(data.extra_cost)
        if data.items is not None:
            self._build_items(po, data.items)

        self.audit.log(AuditAction.UPDATE, entity="PedidoCompra", entity_id=po.id)
        self.db.commit()
        self.db.refresh(po)
        return self._to_read(po)

    def place(self, po_id: int) -> PurchaseOrderRead:
        po = self._get(po_id)
        if po.status != PurchaseOrderStatus.DRAFT:
            raise BusinessRuleError("Somente rascunhos podem ser emitidos")
        if not po.items:
            raise BusinessRuleError("Pedido de compra sem itens nao pode ser emitido")
        po.status = PurchaseOrderStatus.PLACED
        po.placed_at = datetime.now(UTC)
        self.audit.log(
            AuditAction.UPDATE, entity="PedidoCompra", entity_id=po.id, new_value="emitido"
        )
        self.db.commit()
        self.db.refresh(po)
        return self._to_read(po)

    def receive(self, po_id: int, data: PurchaseOrderReceive) -> PurchaseOrderRead:
        po = self._get(po_id)
        if po.status not in (PurchaseOrderStatus.PLACED, PurchaseOrderStatus.PARTIAL):
            raise BusinessRuleError(
                "Somente pedidos emitidos ou parcialmente recebidos podem receber entrada"
            )

        items_by_id = {item.id: item for item in po.items}
        # Determine what to receive: an explicit list, or all remaining.
        if data.items:
            receipts: list[tuple[PurchaseOrderItem, object]] = []
            for entry in data.items:
                item = items_by_id.get(entry.item_id)
                if item is None:
                    raise ValidationAppError(f"Item {entry.item_id} nao pertence ao pedido")
                remaining = to_decimal(item.quantity) - to_decimal(item.received_quantity)
                qty = q_qty(entry.quantity)
                if qty > remaining:
                    raise BusinessRuleError(
                        f"Quantidade recebida ({qty}) excede o pendente ({remaining}) "
                        f"do produto '{item.product.name}'"
                    )
                receipts.append((item, qty))
        else:
            receipts = [
                (item, to_decimal(item.quantity) - to_decimal(item.received_quantity))
                for item in po.items
                if to_decimal(item.quantity) - to_decimal(item.received_quantity) > 0
            ]

        if not receipts:
            raise BusinessRuleError("Nao ha quantidade pendente para receber")

        movements = MovementService(self.db, self.ctx)
        for item, qty in receipts:
            movements.create(
                MovementCreate(
                    product_id=item.product_id,
                    movement_type=MovementType.PURCHASE,
                    quantity=float(qty),
                    unit_cost=float(item.unit_cost),
                    reason=f"Recebimento {po.number}",
                    document=po.number,
                ),
                commit=False,
            )
            item.received_quantity = q_qty(to_decimal(item.received_quantity) + to_decimal(qty))

        fully_received = all(
            to_decimal(item.received_quantity) >= to_decimal(item.quantity) for item in po.items
        )
        if fully_received:
            po.status = PurchaseOrderStatus.RECEIVED
            po.received_at = datetime.now(UTC)
            po.received_by_id = self.ctx.user.id if self.ctx.user else None
        else:
            po.status = PurchaseOrderStatus.PARTIAL

        self.audit.log(
            AuditAction.APPROVE,
            entity="PedidoCompra",
            entity_id=po.id,
            new_value=f"recebimento ({po.status.value})",
        )
        self.db.commit()
        invalidate_dashboard_cache()
        self.db.refresh(po)
        return self._to_read(po)

    def cancel(self, po_id: int, reason: str) -> PurchaseOrderRead:
        po = self._get(po_id)
        if po.status == PurchaseOrderStatus.CANCELLED:
            raise BusinessRuleError("Pedido de compra ja cancelado")
        if po.status in (PurchaseOrderStatus.PARTIAL, PurchaseOrderStatus.RECEIVED):
            raise BusinessRuleError(
                "Pedido com recebimento nao pode ser cancelado; registre uma devolucao"
            )
        po.status = PurchaseOrderStatus.CANCELLED
        po.cancelled_at = datetime.now(UTC)
        po.cancelled_by_id = self.ctx.user.id if self.ctx.user else None
        self.audit.log(
            AuditAction.CANCEL,
            entity="PedidoCompra",
            entity_id=po.id,
            new_value=f"cancelado: {reason}",
        )
        self.db.commit()
        self.db.refresh(po)
        return self._to_read(po)

    def delete(self, po_id: int) -> None:
        po = self._get(po_id)
        if po.status != PurchaseOrderStatus.DRAFT:
            raise BusinessRuleError("Somente pedidos de compra em rascunho podem ser excluidos")
        self.audit.log(AuditAction.DELETE, entity="PedidoCompra", entity_id=po.id)
        self.repo.delete(po)
        self.db.commit()

"""Movement service - the only place stock changes are recorded.

Business rules enforced here:
- Inactive products cannot be moved.
- Outbound movements cannot drive the balance negative (unless configured).
- Movements are never deleted; cancellation reverses their effect while
  preserving the full audit trail.
"""
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.money import q_cost, to_decimal
from app.models.enums import AuditAction, MovementDirection, MovementType
from app.models.movement import StockMovement
from app.models.product import Product
from app.repositories.movement import MovementRepository
from app.schemas.movement import MovementCreate
from app.services.audit import AuditService, RequestContext
from app.services.dashboard import invalidate_dashboard_cache


class MovementService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = MovementRepository(db)
        self.audit = AuditService(db, self.ctx)

    def _get_active_product(self, product_id: int) -> Product:
        product = self.db.get(Product, product_id)
        if not product:
            raise NotFoundError("Produto nao encontrado")
        if not product.is_active:
            raise BusinessRuleError("Produtos inativos nao podem ser movimentados")
        return product

    def current_balance(self, product_id: int) -> Decimal:
        return self.repo.current_balance(product_id)

    def _update_average_cost(
        self, product: Product, prior_balance: Decimal, in_qty: Decimal, unit_cost: Decimal
    ) -> None:
        """Weighted moving average: (prior_qty*prior_avg + in_qty*cost) / total."""
        prior_avg = to_decimal(product.average_cost)
        prior_qty = max(prior_balance, Decimal("0"))
        total_qty = prior_qty + in_qty
        if total_qty <= 0:
            return
        new_avg = (prior_qty * prior_avg + in_qty * unit_cost) / total_qty
        product.average_cost = q_cost(new_avg)

    def create(
        self,
        data: MovementCreate,
        *,
        inventory_id: int | None = None,
        commit: bool = True,
    ) -> StockMovement:
        product = self._get_active_product(data.product_id)
        direction = data.movement_type.direction
        quantity = to_decimal(data.quantity)

        # Lock the product row so the balance check and insert are atomic across
        # concurrent movements for the same product (prevents oversell races).
        balance = self.repo.current_balance(product.id, lock_product=True)

        if direction == MovementDirection.OUT and not settings.ALLOW_NEGATIVE_STOCK:
            if balance - quantity < 0:
                raise BusinessRuleError(
                    f"Saldo insuficiente: disponivel {balance}, solicitado {quantity}"
                )

        # Maintain weighted moving-average cost on inbound movements with a cost.
        if direction == MovementDirection.IN and data.unit_cost is not None:
            self._update_average_cost(product, balance, quantity, to_decimal(data.unit_cost))

        movement = StockMovement(
            product_id=product.id,
            batch_id=data.batch_id,
            movement_type=data.movement_type,
            direction=direction,
            quantity=data.quantity,
            unit_cost=data.unit_cost,
            moved_at=data.moved_at or datetime.now(UTC),
            reason=data.reason,
            document=data.document,
            notes=data.notes,
            origin_location_id=data.origin_location_id,
            destination_location_id=data.destination_location_id,
            user_id=self.ctx.user.id if self.ctx.user else None,
            inventory_id=inventory_id,
        )
        self.repo.add(movement)
        self.audit.log(
            AuditAction.MOVEMENT,
            entity="StockMovement",
            entity_id=movement.id,
            new_value=f"{data.movement_type.value} {data.quantity} (produto {product.id})",
        )
        # ``commit=False`` lets a caller (e.g. OrderService) batch several
        # movements into a single atomic transaction and invalidate once.
        if commit:
            self.db.commit()
            self.db.refresh(movement)
            invalidate_dashboard_cache()
        return movement

    def create_transfer(self, data: MovementCreate) -> tuple[StockMovement, StockMovement]:
        """A transfer is modeled as an OUT at origin + IN at destination."""
        if data.origin_location_id is None or data.destination_location_id is None:
            raise BusinessRuleError("Transferencia exige localizacao de origem e destino")
        out = self.create(
            data.model_copy(update={"movement_type": MovementType.TRANSFER})
        )
        in_data = data.model_copy(
            update={
                "movement_type": MovementType.ADJUSTMENT_IN,
                "reason": data.reason or "Transferencia (entrada destino)",
            }
        )
        inbound = self.create(in_data)
        return out, inbound

    def cancel(self, movement_id: int, reason: str, *, commit: bool = True) -> StockMovement:
        movement = self.db.get(StockMovement, movement_id)
        if not movement:
            raise NotFoundError("Movimentacao nao encontrada")
        if movement.is_cancelled:
            raise BusinessRuleError("Movimentacao ja cancelada")

        movement.is_cancelled = True
        movement.cancelled_at = datetime.now(UTC)
        movement.cancelled_by_id = self.ctx.user.id if self.ctx.user else None
        movement.notes = f"{movement.notes or ''}\n[CANCELADA] {reason}".strip()
        self.db.flush()

        self.audit.log(
            AuditAction.CANCEL,
            entity="StockMovement",
            entity_id=movement.id,
            old_value="ativa",
            new_value=f"cancelada: {reason}",
        )
        if commit:
            self.db.commit()
            self.db.refresh(movement)
            invalidate_dashboard_cache()
        return movement

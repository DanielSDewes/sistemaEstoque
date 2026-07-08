"""Repository for stock movements and movement-derived balances.

All balances are computed as ``Decimal`` to avoid floating-point drift when
summing many movements.
"""
from decimal import Decimal

from sqlalchemy import Select, and_, case, func, select

from app.core.money import q_qty, to_decimal
from app.core.pagination import PageParams
from app.models.enums import MovementDirection
from app.models.movement import StockMovement
from app.repositories.base import BaseRepository


class MovementRepository(BaseRepository[StockMovement]):
    def __init__(self, db) -> None:  # noqa: ANN001
        super().__init__(StockMovement, db)

    # --- Balance computation (stock is ALWAYS derived from movements) ---
    def _signed_sum_expr(self):
        return func.coalesce(
            func.sum(
                case(
                    (
                        StockMovement.direction == MovementDirection.IN,
                        StockMovement.quantity,
                    ),
                    else_=-StockMovement.quantity,
                )
            ),
            0,
        )

    def current_balance(self, product_id: int, *, lock_product: bool = False) -> Decimal:
        """Current balance for a product, derived from its movements.

        When ``lock_product`` is set the product row is locked FOR UPDATE first,
        serializing concurrent movements on the same product (Postgres); this is
        a safe no-op on SQLite.
        """
        if lock_product:
            from app.models.product import Product

            self.db.execute(
                select(Product.id).where(Product.id == product_id).with_for_update()
            ).first()
        stmt = (
            select(self._signed_sum_expr())
            .where(StockMovement.product_id == product_id)
            .where(StockMovement.is_cancelled.is_(False))
        )
        return q_qty(self.db.execute(stmt).scalar_one() or 0)

    def balances_for(self, product_ids: list[int]) -> dict[int, Decimal]:
        """Bulk balance lookup: {product_id: current_balance}."""
        if not product_ids:
            return {}
        stmt = (
            select(StockMovement.product_id, self._signed_sum_expr())
            .where(StockMovement.product_id.in_(product_ids))
            .where(StockMovement.is_cancelled.is_(False))
            .group_by(StockMovement.product_id)
        )
        return {pid: q_qty(bal or 0) for pid, bal in self.db.execute(stmt).all()}

    def all_balances(self) -> dict[int, Decimal]:
        stmt = (
            select(StockMovement.product_id, self._signed_sum_expr())
            .where(StockMovement.is_cancelled.is_(False))
            .group_by(StockMovement.product_id)
        )
        return {pid: q_qty(bal or 0) for pid, bal in self.db.execute(stmt).all()}

    def balance_by_location(self, product_id: int) -> dict[int, Decimal]:
        """Per-shelf balances derived from movements' origin/destination.

        Inbound movements credit the destination shelf; outbound movements debit
        the origin shelf. Movements without a location are ignored here.
        """
        balances: dict[int, Decimal] = {}
        rows = self.db.execute(
            select(
                StockMovement.direction,
                StockMovement.quantity,
                StockMovement.origin_location_id,
                StockMovement.destination_location_id,
            )
            .where(StockMovement.product_id == product_id)
            .where(StockMovement.is_cancelled.is_(False))
        ).all()
        for direction, quantity, origin, dest in rows:
            qty = to_decimal(quantity)
            if direction == MovementDirection.IN and dest is not None:
                balances[dest] = balances.get(dest, Decimal("0")) + qty
            elif direction == MovementDirection.OUT and origin is not None:
                balances[origin] = balances.get(origin, Decimal("0")) - qty
        return {shelf_id: q_qty(v) for shelf_id, v in balances.items()}

    # --- Listing / filtering ---
    def build_filter(
        self,
        product_id: int | None = None,
        movement_type: str | None = None,
        direction: str | None = None,
        include_cancelled: bool = True,
    ) -> Select:
        stmt = select(StockMovement)
        conditions = []
        if product_id is not None:
            conditions.append(StockMovement.product_id == product_id)
        if movement_type:
            conditions.append(StockMovement.movement_type == movement_type)
        if direction:
            conditions.append(StockMovement.direction == direction)
        if not include_cancelled:
            conditions.append(StockMovement.is_cancelled.is_(False))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        return stmt.order_by(StockMovement.moved_at.desc())

    def paginate_filtered(self, params: PageParams, **filters) -> tuple[list, int]:
        return self.paginate(params, self.build_filter(**filters))

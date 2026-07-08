"""Sales order service.

Orders are created as drafts. Confirming an order deducts stock atomically by
generating one ``venda`` movement per item (all in a single transaction);
cancelling a confirmed order reverses those movements.
"""
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.money import q_cost, q_money, q_qty, to_decimal
from app.core.pagination import Page, PageParams
from app.models.enums import AuditAction, MovementType, OrderStatus
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.repositories.customer import CustomerRepository
from app.repositories.order import OrderRepository
from app.schemas.customer import CustomerSummary
from app.schemas.movement import MovementCreate
from app.schemas.order import (
    OrderCreate,
    OrderItemRead,
    OrderRead,
    OrderUpdate,
    ProfitPeriod,
    ProfitReport,
)
from app.services.audit import AuditService, RequestContext
from app.services.dashboard import invalidate_dashboard_cache
from app.services.movement import MovementService


class OrderService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = OrderRepository(db)
        self.customers = CustomerRepository(db)
        self.audit = AuditService(db, self.ctx)

    # --- helpers ---
    def _to_read(self, order: Order) -> OrderRead:
        total_cost = sum(
            (q_money(to_decimal(i.quantity) * to_decimal(i.unit_cost)) for i in order.items),
            q_money(0),
        )
        extra_cost = q_money(order.extra_cost)
        profit = q_money(to_decimal(order.total_amount) - total_cost - extra_cost)
        return OrderRead(
            id=order.id,
            number=order.number,
            customer_id=order.customer_id,
            customer=CustomerSummary.model_validate(order.customer),
            status=order.status,
            order_date=order.order_date,
            notes=order.notes,
            total_amount=float(order.total_amount),
            extra_cost=float(extra_cost),
            total_cost=float(total_cost),
            profit=float(profit),
            items=[
                OrderItemRead(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product.name,
                    product_code=item.product.internal_code,
                    quantity=float(item.quantity),
                    unit_price=float(item.unit_price),
                    unit_cost=float(item.unit_cost),
                    line_total=float(item.line_total),
                )
                for item in order.items
            ],
            confirmed_at=order.confirmed_at,
            cancelled_at=order.cancelled_at,
        )

    def _get(self, order_id: int) -> Order:
        order = self.repo.get(order_id)
        if not order:
            raise NotFoundError("Pedido nao encontrado")
        return order

    def _active_product(self, product_id: int) -> Product:
        product = self.db.get(Product, product_id)
        if not product:
            raise NotFoundError(f"Produto {product_id} nao encontrado")
        if not product.is_active:
            raise BusinessRuleError(f"Produto '{product.name}' esta inativo")
        return product

    def _build_items(self, order: Order, items_data: list) -> None:
        """Replace an order's items and recompute the total.

        The item's ``unit_cost`` is snapshotted from the product's current
        average cost so drafts already show an estimated profit; it is
        refreshed at confirmation time (see ``confirm``).
        """
        order.items = []
        total = q_money(0)
        for item in items_data:
            product = self._active_product(item.product_id)
            qty = q_qty(item.quantity)
            price = q_money(item.unit_price)
            line_total = q_money(qty * price)
            total += line_total
            order.items.append(
                OrderItem(
                    product_id=item.product_id,
                    quantity=qty,
                    unit_price=price,
                    line_total=line_total,
                    unit_cost=q_cost(product.average_cost),
                )
            )
        order.total_amount = total

    # --- read ---
    def get(self, order_id: int) -> OrderRead:
        return self._to_read(self._get(order_id))

    def list(
        self,
        params: PageParams,
        term: str | None = None,
        customer_id: int | None = None,
        status: OrderStatus | None = None,
    ) -> Page[OrderRead]:
        stmt = self.repo.search(term=term, customer_id=customer_id, status=status)
        items, total = self.repo.paginate(params, stmt)
        return Page.create([self._to_read(o) for o in items], total, params)

    def list_for_customer(self, customer_id: int, params: PageParams) -> Page[OrderRead]:
        return self.list(params, customer_id=customer_id)

    # --- write ---
    def create(self, data: OrderCreate) -> OrderRead:
        customer = self.customers.get(data.customer_id)
        if not customer:
            raise NotFoundError("Cliente nao encontrado")

        order = Order(
            customer_id=customer.id,
            order_date=data.order_date or datetime.now(UTC),
            notes=data.notes,
            extra_cost=q_money(data.extra_cost),
            status=OrderStatus.DRAFT,
        )
        self._build_items(order, data.items)
        self.repo.add(order)  # flush -> assigns order.id
        order.number = f"PED-{order.id:06d}"
        self.audit.log(
            AuditAction.CREATE, entity="Pedido", entity_id=order.id, new_value=order.number
        )
        self.db.commit()
        self.db.refresh(order)
        return self._to_read(order)

    def update(self, order_id: int, data: OrderUpdate) -> OrderRead:
        order = self._get(order_id)
        if order.status != OrderStatus.DRAFT:
            raise BusinessRuleError("Somente pedidos em rascunho podem ser editados")

        if data.customer_id is not None:
            if not self.customers.get(data.customer_id):
                raise NotFoundError("Cliente nao encontrado")
            order.customer_id = data.customer_id
        if data.order_date is not None:
            order.order_date = data.order_date
        if "notes" in data.model_fields_set:
            order.notes = data.notes
        if data.extra_cost is not None:
            order.extra_cost = q_money(data.extra_cost)
        if data.items is not None:
            self._build_items(order, data.items)

        self.audit.log(AuditAction.UPDATE, entity="Pedido", entity_id=order.id)
        self.db.commit()
        self.db.refresh(order)
        return self._to_read(order)

    def confirm(self, order_id: int) -> OrderRead:
        order = self._get(order_id)
        if order.status != OrderStatus.DRAFT:
            raise BusinessRuleError("Somente pedidos em rascunho podem ser confirmados")
        if not order.items:
            raise BusinessRuleError("Pedido sem itens nao pode ser confirmado")

        movements = MovementService(self.db, self.ctx)
        # All movements share the transaction; any insufficient balance aborts
        # the whole confirmation before commit, so nothing is deducted.
        for item in order.items:
            # Refresh the COGS snapshot to the cost at the moment of the sale.
            product = self.db.get(Product, item.product_id)
            if product is not None:
                item.unit_cost = q_cost(product.average_cost)
            movement = movements.create(
                MovementCreate(
                    product_id=item.product_id,
                    movement_type=MovementType.SALE,
                    quantity=float(item.quantity),
                    reason=f"Pedido {order.number}",
                    document=order.number,
                ),
                commit=False,
            )
            item.movement_id = movement.id

        order.status = OrderStatus.CONFIRMED
        order.confirmed_at = datetime.now(UTC)
        order.confirmed_by_id = self.ctx.user.id if self.ctx.user else None
        self.audit.log(
            AuditAction.APPROVE, entity="Pedido", entity_id=order.id, new_value="confirmado"
        )
        self.db.commit()
        invalidate_dashboard_cache()
        self.db.refresh(order)
        return self._to_read(order)

    def cancel(self, order_id: int, reason: str) -> OrderRead:
        order = self._get(order_id)
        if order.status == OrderStatus.CANCELLED:
            raise BusinessRuleError("Pedido ja cancelado")

        if order.status == OrderStatus.CONFIRMED:
            movements = MovementService(self.db, self.ctx)
            for item in order.items:
                if item.movement_id:
                    movements.cancel(item.movement_id, reason, commit=False)

        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now(UTC)
        order.cancelled_by_id = self.ctx.user.id if self.ctx.user else None
        self.audit.log(
            AuditAction.CANCEL,
            entity="Pedido",
            entity_id=order.id,
            new_value=f"cancelado: {reason}",
        )
        self.db.commit()
        invalidate_dashboard_cache()
        self.db.refresh(order)
        return self._to_read(order)

    def delete(self, order_id: int) -> None:
        order = self._get(order_id)
        if order.status != OrderStatus.DRAFT:
            raise BusinessRuleError("Somente pedidos em rascunho podem ser excluidos")
        self.audit.log(AuditAction.DELETE, entity="Pedido", entity_id=order.id)
        self.repo.delete(order)
        self.db.commit()

    # --- profit report ---
    def profit_report(self, start: date, end: date, group_by: str = "month") -> ProfitReport:
        """Aggregate profit of confirmed orders in [start, end] by day or month.

        Profit = revenue (sale prices) - COGS (cost snapshots) - extra costs.
        Only confirmed orders count, bucketed by their confirmation date.
        """
        if group_by not in ("day", "month"):
            raise BusinessRuleError("group_by deve ser 'day' ou 'month'")
        stmt = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.status == OrderStatus.CONFIRMED)
        )
        orders = self.db.execute(stmt).scalars().all()

        buckets: dict[str, dict] = {}
        for order in orders:
            when = order.confirmed_at or order.order_date
            if when is None:
                continue
            day = when.date()
            if day < start or day > end:
                continue
            key = day.strftime("%Y-%m") if group_by == "month" else day.isoformat()
            revenue = sum(
                (q_money(to_decimal(i.quantity) * to_decimal(i.unit_price)) for i in order.items),
                q_money(0),
            )
            cost = sum(
                (q_money(to_decimal(i.quantity) * to_decimal(i.unit_cost)) for i in order.items),
                q_money(0),
            )
            extra = q_money(order.extra_cost)
            bucket = buckets.setdefault(
                key, {"orders": 0, "revenue": q_money(0), "cost": q_money(0), "extra": q_money(0)}
            )
            bucket["orders"] += 1
            bucket["revenue"] += revenue
            bucket["cost"] += cost
            bucket["extra"] += extra

        periods = [
            ProfitPeriod(
                period=key,
                orders=b["orders"],
                revenue=float(b["revenue"]),
                cost=float(b["cost"]),
                extra_cost=float(b["extra"]),
                profit=float(b["revenue"] - b["cost"] - b["extra"]),
            )
            for key, b in sorted(buckets.items())
        ]
        totals = ProfitPeriod(
            period="total",
            orders=sum(p.orders for p in periods),
            revenue=float(sum((to_decimal(p.revenue) for p in periods), to_decimal(0))),
            cost=float(sum((to_decimal(p.cost) for p in periods), to_decimal(0))),
            extra_cost=float(sum((to_decimal(p.extra_cost) for p in periods), to_decimal(0))),
            profit=float(sum((to_decimal(p.profit) for p in periods), to_decimal(0))),
        )
        return ProfitReport(
            start=start, end=end, group_by=group_by, totals=totals, periods=periods
        )

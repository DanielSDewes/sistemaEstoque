"""Dashboard service - aggregates KPIs and chart series."""
import time
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.money import q_money, q_qty, to_decimal
from app.models.catalog import Category
from app.models.enums import MovementDirection
from app.models.movement import StockMovement
from app.models.product import Batch, Product
from app.models.supplier import Supplier
from app.repositories.movement import MovementRepository
from app.schemas.dashboard import (
    DashboardResponse,
    KpiCards,
    NamedSeries,
    SeriesPoint,
)

# Small in-process TTL cache for the dashboard payload (per `days`).
_CACHE: dict[int, tuple[float, DashboardResponse]] = {}
_CACHE_TTL_SECONDS = 30


def invalidate_dashboard_cache() -> None:
    _CACHE.clear()


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.movements = MovementRepository(db)

    def build(self, days: int = 14, *, use_cache: bool = True) -> DashboardResponse:
        if use_cache:
            hit = _CACHE.get(days)
            if hit and time.monotonic() - hit[0] < _CACHE_TTL_SECONDS:
                return hit[1]

        balances = self.movements.all_balances()
        products = list(self.db.execute(select(Product)).scalars().all())

        total_products = len(products)
        total_qty = sum((balances.get(p.id, Decimal("0")) for p in products), Decimal("0"))
        # Valuation uses the maintained weighted-average cost (O(1) per product).
        total_value = sum(
            (balances.get(p.id, Decimal("0")) * to_decimal(p.average_cost) for p in products),
            Decimal("0"),
        )
        no_stock = sum(1 for p in products if balances.get(p.id, Decimal("0")) <= 0)
        below_min = sum(
            1 for p in products if balances.get(p.id, Decimal("0")) < to_decimal(p.min_stock)
        )

        kpis = KpiCards(
            total_products=total_products,
            products_no_stock=no_stock,
            products_below_min=below_min,
            products_near_expiry=self._near_expiry_count(),
            movements_today=self._movements_today(),
            total_stock_quantity=q_qty(total_qty),
            total_stock_value=q_money(total_value),
            total_suppliers=self.db.execute(select(func.count(Supplier.id))).scalar_one(),
        )

        response = DashboardResponse(
            kpis=kpis,
            movements_by_day=self._movements_by_day(days),
            top_moved_products=self._top_moved(),
            stock_by_category=self._stock_by_category(balances),
            entries_vs_exits=self._entries_vs_exits(days),
        )
        _CACHE[days] = (time.monotonic(), response)
        return response

    def _movements_today(self) -> int:
        start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.count(StockMovement.id)).where(StockMovement.moved_at >= start)
        return self.db.execute(stmt).scalar_one()

    def _near_expiry_count(self) -> int:
        limit = date.today() + timedelta(days=settings.EXPIRY_ALERT_DAYS)
        stmt = select(func.count(Batch.id)).where(
            Batch.expiry_date.isnot(None),
            Batch.expiry_date <= limit,
            Batch.expiry_date >= date.today(),
        )
        return self.db.execute(stmt).scalar_one()

    def _movements_by_day(self, days: int) -> list[SeriesPoint]:
        start = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(func.date(StockMovement.moved_at), func.count(StockMovement.id))
            .where(StockMovement.moved_at >= start)
            .group_by(func.date(StockMovement.moved_at))
            .order_by(func.date(StockMovement.moved_at))
        )
        return [SeriesPoint(label=str(d), value=float(c)) for d, c in self.db.execute(stmt).all()]

    def _entries_vs_exits(self, days: int) -> list[NamedSeries]:
        start = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(
                func.date(StockMovement.moved_at),
                StockMovement.direction,
                func.coalesce(func.sum(StockMovement.quantity), 0),
            )
            .where(StockMovement.moved_at >= start, StockMovement.is_cancelled.is_(False))
            .group_by(func.date(StockMovement.moved_at), StockMovement.direction)
            .order_by(func.date(StockMovement.moved_at))
        )
        ins: dict[str, float] = {}
        outs: dict[str, float] = {}
        for d, direction, qty in self.db.execute(stmt).all():
            (ins if direction == MovementDirection.IN else outs)[str(d)] = float(qty)
        labels = sorted(set(ins) | set(outs))
        return [
            NamedSeries(
                name="Entradas",
                points=[SeriesPoint(label=x, value=ins.get(x, 0)) for x in labels],
            ),
            NamedSeries(
                name="Saidas",
                points=[SeriesPoint(label=x, value=outs.get(x, 0)) for x in labels],
            ),
        ]

    def _top_moved(self, limit: int = 10) -> list[SeriesPoint]:
        stmt = (
            select(Product.name, func.coalesce(func.sum(StockMovement.quantity), 0).label("q"))
            .join(StockMovement, StockMovement.product_id == Product.id)
            .where(StockMovement.is_cancelled.is_(False))
            .group_by(Product.name)
            .order_by(func.sum(StockMovement.quantity).desc())
            .limit(limit)
        )
        return [SeriesPoint(label=n, value=float(q)) for n, q in self.db.execute(stmt).all()]

    def _stock_by_category(self, balances: dict[int, Decimal]) -> list[SeriesPoint]:
        rows = self.db.execute(
            select(Category.name, Product.id).join(Product, Product.category_id == Category.id)
        ).all()
        agg: dict[str, Decimal] = {}
        for name, pid in rows:
            agg[name] = agg.get(name, Decimal("0")) + balances.get(pid, Decimal("0"))
        return [
            SeriesPoint(label=k, value=q_qty(v))
            for k, v in sorted(agg.items(), key=lambda x: x[1], reverse=True)
        ]

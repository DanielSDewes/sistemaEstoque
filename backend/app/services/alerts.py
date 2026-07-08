"""Alerts service: actionable stock and expiry warnings."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.money import to_decimal
from app.models.product import Batch, Product
from app.repositories.movement import MovementRepository
from app.schemas.alerts import AlertsSummary, BelowMinimumItem, NearExpiryItem


class AlertsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.movements = MovementRepository(db)

    def below_minimum(self) -> list[BelowMinimumItem]:
        balances = self.movements.all_balances()
        products = self.db.execute(select(Product).where(Product.is_active.is_(True))).scalars()
        items: list[BelowMinimumItem] = []
        for p in products:
            current = balances.get(p.id, to_decimal(0))
            min_stock = to_decimal(p.min_stock)
            if current < min_stock:
                items.append(
                    BelowMinimumItem(
                        product_id=p.id,
                        internal_code=p.internal_code,
                        name=p.name,
                        current=float(current),
                        min_stock=float(min_stock),
                        reorder_point=float(p.reorder_point or 0),
                        deficit=float(min_stock - current),
                    )
                )
        return sorted(items, key=lambda i: i.deficit, reverse=True)

    def near_expiry(self, within_days: int | None = None) -> list[NearExpiryItem]:
        window = within_days or settings.EXPIRY_ALERT_DAYS
        today = date.today()
        limit = today + timedelta(days=window)
        rows = self.db.execute(
            select(
                Product.id, Product.internal_code, Product.name,
                Batch.lot_number, Batch.expiry_date,
            )
            .join(Batch, Batch.product_id == Product.id)
            .where(
                Batch.expiry_date.isnot(None),
                Batch.expiry_date <= limit,
                Batch.expiry_date >= today,
            )
            .order_by(Batch.expiry_date)
        ).all()
        return [
            NearExpiryItem(
                product_id=pid,
                internal_code=code,
                name=name,
                lot_number=lot,
                expiry_date=exp,
                days_remaining=(exp - today).days,
            )
            for pid, code, name, lot, exp in rows
        ]

    def summary(self) -> AlertsSummary:
        balances = self.movements.all_balances()
        products = list(
            self.db.execute(select(Product).where(Product.is_active.is_(True))).scalars()
        )
        below = sum(
            1 for p in products if balances.get(p.id, to_decimal(0)) < to_decimal(p.min_stock)
        )
        out = sum(1 for p in products if balances.get(p.id, to_decimal(0)) <= 0)
        today = date.today()
        limit = today + timedelta(days=settings.EXPIRY_ALERT_DAYS)
        from sqlalchemy import func

        near = self.db.execute(
            select(func.count(Batch.id)).where(
                Batch.expiry_date.isnot(None),
                Batch.expiry_date <= limit,
                Batch.expiry_date >= today,
            )
        ).scalar_one()
        expired = self.db.execute(
            select(func.count(Batch.id)).where(
                Batch.expiry_date.isnot(None), Batch.expiry_date < today
            )
        ).scalar_one()
        return AlertsSummary(
            below_minimum_count=below,
            near_expiry_count=near,
            expired_count=expired,
            out_of_stock_count=out,
        )

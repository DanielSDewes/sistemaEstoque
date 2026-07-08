"""Sales order repository."""
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.enums import OrderStatus
from app.models.order import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session) -> None:
        super().__init__(Order, db)

    def search(
        self,
        term: str | None = None,
        customer_id: int | None = None,
        status: OrderStatus | None = None,
    ) -> Select:
        stmt = select(Order)
        if term:
            like = f"%{term.strip()}%"
            stmt = stmt.join(Customer).where(
                Order.number.ilike(like) | Customer.name.ilike(like)
            )
        if customer_id is not None:
            stmt = stmt.where(Order.customer_id == customer_id)
        if status is not None:
            stmt = stmt.where(Order.status == status)
        return stmt

"""Customer repository."""
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, db: Session) -> None:
        super().__init__(Customer, db)

    def get_by_document(self, document: str) -> Customer | None:
        return self.get_by(document=document)

    def search(self, term: str | None) -> Select:
        stmt = select(Customer)
        if term:
            like = f"%{term.strip()}%"
            stmt = stmt.where(
                or_(
                    Customer.name.ilike(like),
                    Customer.phone.ilike(like),
                    Customer.document.ilike(like),
                )
            )
        return stmt

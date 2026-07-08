"""Financial account repository with filtered search."""
from datetime import date

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models.enums import FinancialDirection, FinancialStatus
from app.models.finance import FinancialAccount, FinancialInstallment
from app.repositories.base import BaseRepository


class FinancialAccountRepository(BaseRepository[FinancialAccount]):
    def __init__(self, db: Session) -> None:
        super().__init__(FinancialAccount, db)

    def search(
        self,
        *,
        direction: FinancialDirection | None = None,
        status: FinancialStatus | None = None,
        customer_id: int | None = None,
        supplier_id: int | None = None,
        category_id: int | None = None,
        overdue: bool | None = None,
        due_from: date | None = None,
        due_to: date | None = None,
        term: str | None = None,
    ) -> Select:
        stmt = select(FinancialAccount)
        if direction is not None:
            stmt = stmt.where(FinancialAccount.direction == direction)
        if status is not None:
            stmt = stmt.where(FinancialAccount.status == status)
        if customer_id is not None:
            stmt = stmt.where(FinancialAccount.customer_id == customer_id)
        if supplier_id is not None:
            stmt = stmt.where(FinancialAccount.supplier_id == supplier_id)
        if category_id is not None:
            stmt = stmt.where(FinancialAccount.category_id == category_id)
        if term:
            like = f"%{term.strip()}%"
            stmt = stmt.where(
                or_(
                    FinancialAccount.document.ilike(like),
                    FinancialAccount.description.ilike(like),
                )
            )
        # Filters that look into installments use EXISTS subqueries to avoid
        # duplicating account rows on the join.
        if overdue:
            sub = select(FinancialInstallment.account_id).where(
                FinancialInstallment.account_id == FinancialAccount.id,
                FinancialInstallment.status.in_(
                    [FinancialStatus.OPEN, FinancialStatus.PARTIAL]
                ),
                FinancialInstallment.due_date < date.today(),
            )
            stmt = stmt.where(sub.exists())
        if due_from is not None or due_to is not None:
            sub = select(FinancialInstallment.account_id).where(
                FinancialInstallment.account_id == FinancialAccount.id
            )
            if due_from is not None:
                sub = sub.where(FinancialInstallment.due_date >= due_from)
            if due_to is not None:
                sub = sub.where(FinancialInstallment.due_date <= due_to)
            stmt = stmt.where(sub.exists())
        return stmt

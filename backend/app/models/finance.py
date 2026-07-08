"""Financial module: accounts payable/receivable, installments and settlements.

A ``FinancialAccount`` (título) carries a ``direction`` (receber/pagar) and is
tied to a customer OR a supplier. It breaks down into ``FinancialInstallment``
rows (parcelas), each settled by one or more ``FinancialSettlement`` (baixas).
Settlements against a bank account create ``BankTransaction`` rows that keep the
account balance up to date.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.money import q_money
from app.models.enums import (
    BankTransactionType,
    FinancialCategoryKind,
    FinancialDirection,
    FinancialStatus,
    StatusEnum,
)
from app.models.mixins import TimestampMixin
from app.models.types import str_enum


def _money() -> Mapped[float]:
    """A 2-decimal money column defaulting to 0 (DB and Python side)."""
    return mapped_column(Numeric(14, 2), default=0, server_default="0", nullable=False)


# --- Supporting registrations (cadastros de apoio) ---
class PaymentMethod(Base, TimestampMixin):
    """Forma de pagamento (PIX, Dinheiro, Boleto...)."""

    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )


class FinancialCategory(Base, TimestampMixin):
    """Categoria financeira (receita/despesa) para relatórios."""

    __tablename__ = "financial_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    kind: Mapped[FinancialCategoryKind] = mapped_column(
        str_enum(FinancialCategoryKind, "financial_category_kind_enum"), nullable=False
    )
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )


class CostCenter(Base, TimestampMixin):
    """Centro de custo (Administrativo, Comercial, TI...)."""

    __tablename__ = "cost_centers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )


class BankAccount(Base, TimestampMixin):
    """Conta bancária/caixa cujo saldo é mantido pelas movimentações."""

    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    bank: Mapped[str | None] = mapped_column(String(80))
    agency: Mapped[str | None] = mapped_column(String(20))
    account_number: Mapped[str | None] = mapped_column(String(30))
    opening_balance: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, server_default="0", nullable=False
    )
    current_balance: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, server_default="0", nullable=False
    )
    status: Mapped[StatusEnum] = mapped_column(
        str_enum(StatusEnum, "status_enum"), default=StatusEnum.ACTIVE, nullable=False
    )


# --- Core ---
class FinancialAccount(Base, TimestampMixin):
    """A payable/receivable title, broken down into installments."""

    __tablename__ = "financial_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    direction: Mapped[FinancialDirection] = mapped_column(
        str_enum(FinancialDirection, "financial_direction_enum"), nullable=False, index=True
    )
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), index=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), index=True)
    document: Mapped[str | None] = mapped_column(String(60), index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("financial_categories.id"))
    cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"))
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[float] = mapped_column(
        Numeric(14, 2), default=0, server_default="0", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[FinancialStatus] = mapped_column(
        str_enum(FinancialStatus, "financial_status_enum"),
        default=FinancialStatus.OPEN,
        nullable=False,
        index=True,
    )

    customer = relationship("Customer", lazy="joined")
    supplier = relationship("Supplier", lazy="joined")
    category = relationship("FinancialCategory", lazy="joined")
    cost_center = relationship("CostCenter", lazy="joined")
    installments: Mapped[list[FinancialInstallment]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    @property
    def total_paid(self) -> float:
        return float(sum((q_money(i.amount_paid) for i in self.installments), q_money(0)))

    @property
    def balance(self) -> float:
        return float(sum((q_money(i.balance) for i in self.installments), q_money(0)))

    def effective_status(self, today: date | None = None) -> FinancialStatus:
        """Aggregate status across installments, deriving OVERDUE."""
        if self.status in (FinancialStatus.CANCELLED, FinancialStatus.RENEGOTIATED):
            return self.status
        statuses = [i.effective_status(today) for i in self.installments]
        if statuses and all(s == FinancialStatus.SETTLED for s in statuses):
            return FinancialStatus.SETTLED
        if any(s == FinancialStatus.OVERDUE for s in statuses):
            return FinancialStatus.OVERDUE
        if any(s in (FinancialStatus.PARTIAL, FinancialStatus.SETTLED) for s in statuses):
            return FinancialStatus.PARTIAL
        return FinancialStatus.OPEN


class FinancialInstallment(Base, TimestampMixin):
    """A single installment (parcela) of a financial account."""

    __tablename__ = "financial_installments"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("financial_accounts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_installments: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    original_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    # Accumulated adjustments applied through settlements (or manually).
    interest: Mapped[float] = _money()
    fine: Mapped[float] = _money()
    addition: Mapped[float] = _money()
    discount: Mapped[float] = _money()
    amount_paid: Mapped[float] = _money()
    status: Mapped[FinancialStatus] = mapped_column(
        str_enum(FinancialStatus, "financial_status_enum"),
        default=FinancialStatus.OPEN,
        nullable=False,
        index=True,
    )

    account: Mapped[FinancialAccount] = relationship(back_populates="installments")
    settlements: Mapped[list[FinancialSettlement]] = relationship(
        back_populates="installment", cascade="all, delete-orphan"
    )

    @property
    def effective_total(self) -> float:
        return float(
            q_money(self.original_amount)
            + q_money(self.interest)
            + q_money(self.fine)
            + q_money(self.addition)
            - q_money(self.discount)
        )

    @property
    def balance(self) -> float:
        return float(q_money(self.effective_total) - q_money(self.amount_paid))

    def effective_status(self, today: date | None = None) -> FinancialStatus:
        """Status with the time-based OVERDUE value derived from the due date."""
        if (
            self.status in (FinancialStatus.OPEN, FinancialStatus.PARTIAL)
            and self.balance > 0
            and self.due_date < (today or date.today())
        ):
            return FinancialStatus.OVERDUE
        return self.status


class FinancialSettlement(Base):
    """A payment/receipt (baixa) applied to an installment."""

    __tablename__ = "financial_settlements"

    id: Mapped[int] = mapped_column(primary_key=True)
    installment_id: Mapped[int] = mapped_column(
        ForeignKey("financial_installments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    settled_at: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    interest: Mapped[float] = _money()
    fine: Mapped[float] = _money()
    discount: Mapped[float] = _money()
    payment_method_id: Mapped[int | None] = mapped_column(ForeignKey("payment_methods.id"))
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("bank_accounts.id"))
    notes: Mapped[str | None] = mapped_column(String(255))
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    installment: Mapped[FinancialInstallment] = relationship(back_populates="settlements")
    payment_method = relationship("PaymentMethod", lazy="joined")
    bank_account = relationship("BankAccount")


class BankTransaction(Base):
    """A cash movement that updates a bank account's balance."""

    __tablename__ = "bank_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_account_id: Mapped[int] = mapped_column(
        ForeignKey("bank_accounts.id"), index=True, nullable=False
    )
    type: Mapped[BankTransactionType] = mapped_column(
        str_enum(BankTransactionType, "bank_transaction_type_enum"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    settlement_id: Mapped[int | None] = mapped_column(ForeignKey("financial_settlements.id"))
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    bank_account = relationship("BankAccount")

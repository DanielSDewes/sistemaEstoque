"""Financial module schemas."""
from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    FinancialCategoryKind,
    FinancialDirection,
    FinancialStatus,
    StatusEnum,
)
from app.schemas.common import ORMModel


# --- Supporting registrations ---
class PaymentMethodBase(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    status: StatusEnum = StatusEnum.ACTIVE


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    status: StatusEnum | None = None


class PaymentMethodRead(ORMModel):
    id: int
    name: str
    status: StatusEnum


class FinancialCategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: FinancialCategoryKind
    status: StatusEnum = StatusEnum.ACTIVE


class FinancialCategoryCreate(FinancialCategoryBase):
    pass


class FinancialCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    kind: FinancialCategoryKind | None = None
    status: StatusEnum | None = None


class FinancialCategoryRead(ORMModel):
    id: int
    name: str
    kind: FinancialCategoryKind
    status: StatusEnum


class CostCenterBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    status: StatusEnum = StatusEnum.ACTIVE


class CostCenterCreate(CostCenterBase):
    pass


class CostCenterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    status: StatusEnum | None = None


class CostCenterRead(ORMModel):
    id: int
    name: str
    status: StatusEnum


class BankAccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    bank: str | None = None
    agency: str | None = None
    account_number: str | None = None
    opening_balance: float = 0
    status: StatusEnum = StatusEnum.ACTIVE


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    bank: str | None = None
    agency: str | None = None
    account_number: str | None = None
    status: StatusEnum | None = None


class BankAccountRead(ORMModel):
    id: int
    name: str
    bank: str | None
    agency: str | None
    account_number: str | None
    opening_balance: float
    current_balance: float
    status: StatusEnum


# --- Financial accounts (títulos), installments and settlements ---
class InstallmentInput(BaseModel):
    due_date: date
    amount: float = Field(gt=0)


class InstallmentPlan(BaseModel):
    count: int = Field(ge=1, le=360)
    first_due_date: date
    interval_days: int = Field(default=30, ge=0)


class FinancialAccountCreate(BaseModel):
    direction: FinancialDirection
    customer_id: int | None = None
    supplier_id: int | None = None
    document: str | None = None
    description: str | None = None
    category_id: int | None = None
    cost_center_id: int | None = None
    issue_date: date | None = None
    notes: str | None = None
    # Provide either an explicit installments list OR a total + plan.
    total_amount: float | None = Field(default=None, gt=0)
    installment_plan: InstallmentPlan | None = None
    installments: list[InstallmentInput] | None = None

    @model_validator(mode="after")
    def _check_source(self) -> "FinancialAccountCreate":
        if not self.installments and not (self.total_amount and self.installment_plan):
            raise ValueError(
                "Informe 'installments' ou 'total_amount' + 'installment_plan'."
            )
        return self


class FinancialAccountUpdate(BaseModel):
    document: str | None = None
    description: str | None = None
    category_id: int | None = None
    cost_center_id: int | None = None
    issue_date: date | None = None
    notes: str | None = None


class SettlementCreate(BaseModel):
    amount: float = Field(gt=0)
    settled_at: date | None = None
    payment_method_id: int | None = None
    bank_account_id: int | None = None
    interest: float = Field(default=0, ge=0)
    fine: float = Field(default=0, ge=0)
    discount: float = Field(default=0, ge=0)
    notes: str | None = None


class SettlementRead(BaseModel):
    id: int
    installment_id: int
    settled_at: date
    amount: float
    interest: float
    fine: float
    discount: float
    payment_method_id: int | None
    payment_method_name: str | None
    bank_account_id: int | None
    notes: str | None
    is_cancelled: bool


class InstallmentRead(BaseModel):
    id: int
    number: int
    total_installments: int
    due_date: date
    original_amount: float
    interest: float
    fine: float
    addition: float
    discount: float
    amount_paid: float
    balance: float
    status: FinancialStatus
    settlements: list[SettlementRead]


class FinancialAccountRead(BaseModel):
    id: int
    direction: FinancialDirection
    customer_id: int | None
    supplier_id: int | None
    party_name: str | None
    document: str | None
    description: str | None
    category_id: int | None
    category_name: str | None
    cost_center_id: int | None
    cost_center_name: str | None
    issue_date: date
    total_amount: float
    total_paid: float
    balance: float
    notes: str | None
    status: FinancialStatus
    installments: list[InstallmentRead]


class SuggestedCharges(BaseModel):
    days_overdue: int
    interest: float
    fine: float
    balance: float


# --- Cash flow ---
class CashFlowPeriod(BaseModel):
    period: str
    inflow_expected: float
    outflow_expected: float
    inflow_realized: float
    outflow_realized: float
    net_expected: float
    net_realized: float


class CashFlowReport(BaseModel):
    start: date
    end: date
    group_by: str
    totals: CashFlowPeriod
    periods: list[CashFlowPeriod]


# --- Finance dashboard ---
class BankBalance(BaseModel):
    id: int
    name: str
    balance: float


class FinanceDashboard(BaseModel):
    receivable_open: float
    receivable_overdue: float
    received_today: float
    received_month: float
    payable_open: float
    payable_overdue: float
    paid_today: float
    paid_month: float
    cash_total: float
    banks: list[BankBalance]

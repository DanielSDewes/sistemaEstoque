"""Financial services: supporting registrations + accounts/settlements engine."""
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.money import q_money, to_decimal
from app.core.pagination import Page, PageParams
from app.models.enums import (
    AuditAction,
    BankTransactionType,
    FinancialDirection,
    FinancialStatus,
)
from app.models.finance import (
    BankAccount,
    BankTransaction,
    CostCenter,
    FinancialAccount,
    FinancialCategory,
    FinancialInstallment,
    FinancialSettlement,
    PaymentMethod,
)
from app.repositories.customer import CustomerRepository
from app.repositories.finance import FinancialAccountRepository
from app.repositories.supplier import SupplierRepository
from app.schemas.finance import (
    BankAccountRead,
    BankBalance,
    CashFlowPeriod,
    CashFlowReport,
    CostCenterRead,
    FinanceDashboard,
    FinancialAccountCreate,
    FinancialAccountRead,
    FinancialAccountUpdate,
    FinancialCategoryRead,
    InstallmentRead,
    PaymentMethodRead,
    SettlementCreate,
    SettlementRead,
    SuggestedCharges,
)
from app.services.audit import AuditService, RequestContext
from app.services.base import CrudService

# Default late-payment charges (used only to *suggest* values on a baixa).
DAILY_INTEREST_RATE = Decimal("0.00033")  # ~1%/mês
FINE_RATE = Decimal("0.02")  # 2%


# --- Supporting registrations (simple CRUD) ---
class PaymentMethodService(CrudService):
    model = PaymentMethod
    read_schema = PaymentMethodRead
    entity_name = "Forma de pagamento"


class FinancialCategoryService(CrudService):
    model = FinancialCategory
    read_schema = FinancialCategoryRead
    entity_name = "Categoria financeira"


class CostCenterService(CrudService):
    model = CostCenter
    read_schema = CostCenterRead
    entity_name = "Centro de custo"


class BankAccountService(CrudService):
    model = BankAccount
    read_schema = BankAccountRead
    entity_name = "Conta bancaria"

    def _pre_create(self, data: dict) -> None:
        # Opening balance seeds the running balance.
        data.setdefault("current_balance", data.get("opening_balance", 0))


# --- Accounts, installments and settlements engine ---
class FinanceService:
    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = FinancialAccountRepository(db)
        self.audit = AuditService(db, self.ctx)

    # --- read builders ---
    def _to_settlement_read(self, s: FinancialSettlement) -> SettlementRead:
        return SettlementRead(
            id=s.id,
            installment_id=s.installment_id,
            settled_at=s.settled_at,
            amount=float(s.amount),
            interest=float(s.interest),
            fine=float(s.fine),
            discount=float(s.discount),
            payment_method_id=s.payment_method_id,
            payment_method_name=s.payment_method.name if s.payment_method else None,
            bank_account_id=s.bank_account_id,
            notes=s.notes,
            is_cancelled=s.is_cancelled,
        )

    def _to_installment_read(self, i: FinancialInstallment) -> InstallmentRead:
        return InstallmentRead(
            id=i.id,
            number=i.number,
            total_installments=i.total_installments,
            due_date=i.due_date,
            original_amount=float(i.original_amount),
            interest=float(i.interest),
            fine=float(i.fine),
            addition=float(i.addition),
            discount=float(i.discount),
            amount_paid=float(i.amount_paid),
            balance=i.balance,
            status=i.effective_status(),
            settlements=[
                self._to_settlement_read(s) for s in i.settlements if not s.is_cancelled
            ],
        )

    def _party_name(self, a: FinancialAccount) -> str | None:
        if a.customer:
            return a.customer.name
        if a.supplier:
            return a.supplier.trade_name or a.supplier.legal_name
        return None

    def _to_account_read(self, a: FinancialAccount) -> FinancialAccountRead:
        return FinancialAccountRead(
            id=a.id,
            direction=a.direction,
            customer_id=a.customer_id,
            supplier_id=a.supplier_id,
            party_name=self._party_name(a),
            document=a.document,
            description=a.description,
            category_id=a.category_id,
            category_name=a.category.name if a.category else None,
            cost_center_id=a.cost_center_id,
            cost_center_name=a.cost_center.name if a.cost_center else None,
            issue_date=a.issue_date,
            total_amount=float(a.total_amount),
            total_paid=a.total_paid,
            balance=a.balance,
            notes=a.notes,
            status=a.effective_status(),
            installments=[self._to_installment_read(i) for i in a.installments],
        )

    # --- helpers ---
    def _get_account(self, account_id: int) -> FinancialAccount:
        account = self.repo.get(account_id)
        if not account:
            raise NotFoundError("Conta financeira nao encontrada")
        return account

    def _validate_party(self, direction, customer_id, supplier_id) -> None:  # noqa: ANN001
        if direction == FinancialDirection.RECEIVABLE:
            if not customer_id:
                raise BusinessRuleError("Conta a receber exige um cliente")
            if not CustomerRepository(self.db).get(customer_id):
                raise NotFoundError("Cliente nao encontrado")
        else:
            if not supplier_id:
                raise BusinessRuleError("Conta a pagar exige um fornecedor")
            if not SupplierRepository(self.db).get(supplier_id):
                raise NotFoundError("Fornecedor nao encontrado")

    def _build_installments(self, data: FinancialAccountCreate) -> list[FinancialInstallment]:
        if data.installments:
            rows = data.installments
            return [
                FinancialInstallment(
                    number=n,
                    total_installments=len(rows),
                    due_date=r.due_date,
                    original_amount=q_money(r.amount),
                    status=FinancialStatus.OPEN,
                )
                for n, r in enumerate(rows, start=1)
            ]
        plan = data.installment_plan
        total = q_money(data.total_amount)
        count = plan.count
        base = q_money(total / count)
        amounts = [base] * count
        # Put the rounding remainder on the first installment.
        amounts[0] = q_money(amounts[0] + (total - base * count))
        return [
            FinancialInstallment(
                number=i + 1,
                total_installments=count,
                due_date=plan.first_due_date + timedelta(days=plan.interval_days * i),
                original_amount=amounts[i],
                status=FinancialStatus.OPEN,
            )
            for i in range(count)
        ]

    def _recompute_installment(self, i: FinancialInstallment) -> None:
        if i.status in (FinancialStatus.CANCELLED, FinancialStatus.RENEGOTIATED):
            return
        if i.balance <= 0:
            i.status = FinancialStatus.SETTLED
        elif to_decimal(i.amount_paid) > 0:
            i.status = FinancialStatus.PARTIAL
        else:
            i.status = FinancialStatus.OPEN

    def _recompute_account(self, a: FinancialAccount) -> None:
        if a.status in (FinancialStatus.CANCELLED, FinancialStatus.RENEGOTIATED):
            return
        sts = [i.status for i in a.installments if i.status != FinancialStatus.CANCELLED]
        if sts and all(s == FinancialStatus.SETTLED for s in sts):
            a.status = FinancialStatus.SETTLED
        elif any(s in (FinancialStatus.PARTIAL, FinancialStatus.SETTLED) for s in sts):
            a.status = FinancialStatus.PARTIAL
        else:
            a.status = FinancialStatus.OPEN

    def _apply_bank(
        self, direction, bank_account_id: int, amount, settlement: FinancialSettlement, when: date
    ) -> None:  # noqa: ANN001
        bank = self.db.get(BankAccount, bank_account_id)
        if not bank:
            raise NotFoundError("Conta bancaria nao encontrada")
        ttype = (
            BankTransactionType.CREDIT
            if direction == FinancialDirection.RECEIVABLE
            else BankTransactionType.DEBIT
        )
        self.db.add(
            BankTransaction(
                bank_account_id=bank.id,
                type=ttype,
                amount=amount,
                occurred_at=when,
                description=f"Baixa parcela #{settlement.installment_id}",
                settlement_id=settlement.id,
                created_by_id=self.ctx.user.id if self.ctx.user else None,
            )
        )
        delta = amount if ttype == BankTransactionType.CREDIT else -amount
        bank.current_balance = q_money(to_decimal(bank.current_balance) + to_decimal(delta))

    # --- write operations ---
    def create_account(self, data: FinancialAccountCreate) -> FinancialAccountRead:
        self._validate_party(data.direction, data.customer_id, data.supplier_id)
        is_receivable = data.direction == FinancialDirection.RECEIVABLE
        account = FinancialAccount(
            direction=data.direction,
            customer_id=data.customer_id if is_receivable else None,
            supplier_id=data.supplier_id if not is_receivable else None,
            document=data.document,
            description=data.description,
            category_id=data.category_id,
            cost_center_id=data.cost_center_id,
            issue_date=data.issue_date or date.today(),
            notes=data.notes,
            status=FinancialStatus.OPEN,
        )
        account.installments = self._build_installments(data)
        account.total_amount = q_money(
            sum((to_decimal(i.original_amount) for i in account.installments), Decimal("0"))
        )
        self.repo.add(account)
        self.audit.log(
            AuditAction.CREATE,
            entity="ContaFinanceira",
            entity_id=account.id,
            new_value=f"{data.direction.value} {account.total_amount}",
        )
        self.db.commit()
        self.db.refresh(account)
        return self._to_account_read(account)

    def update_account(self, account_id: int, data: FinancialAccountUpdate) -> FinancialAccountRead:
        account = self._get_account(account_id)
        if account.status == FinancialStatus.CANCELLED:
            raise BusinessRuleError("Conta cancelada nao pode ser editada")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(account, key, value)
        self.audit.log(AuditAction.UPDATE, entity="ContaFinanceira", entity_id=account.id)
        self.db.commit()
        self.db.refresh(account)
        return self._to_account_read(account)

    def settle(self, installment_id: int, data: SettlementCreate) -> FinancialAccountRead:
        installment = self.db.get(FinancialInstallment, installment_id)
        if not installment:
            raise NotFoundError("Parcela nao encontrada")
        account = installment.account
        if account.status == FinancialStatus.CANCELLED:
            raise BusinessRuleError("Conta cancelada")
        if installment.status in (FinancialStatus.CANCELLED, FinancialStatus.SETTLED):
            raise BusinessRuleError("Parcela ja quitada ou cancelada")

        settlement = FinancialSettlement(
            installment_id=installment.id,
            settled_at=data.settled_at or date.today(),
            amount=q_money(data.amount),
            interest=q_money(data.interest),
            fine=q_money(data.fine),
            discount=q_money(data.discount),
            payment_method_id=data.payment_method_id,
            bank_account_id=data.bank_account_id,
            notes=data.notes,
            created_by_id=self.ctx.user.id if self.ctx.user else None,
        )
        self.db.add(settlement)
        self.db.flush()

        installment.interest = q_money(to_decimal(installment.interest) + to_decimal(data.interest))
        installment.fine = q_money(to_decimal(installment.fine) + to_decimal(data.fine))
        installment.discount = q_money(to_decimal(installment.discount) + to_decimal(data.discount))
        installment.amount_paid = q_money(
            to_decimal(installment.amount_paid) + to_decimal(data.amount)
        )
        self._recompute_installment(installment)

        if data.bank_account_id:
            self._apply_bank(
                account.direction, data.bank_account_id, q_money(data.amount),
                settlement, settlement.settled_at,
            )

        self._recompute_account(account)
        self.audit.log(
            AuditAction.UPDATE,
            entity="BaixaFinanceira",
            entity_id=settlement.id,
            new_value=f"baixa {settlement.amount} parcela {installment.id}",
        )
        self.db.commit()
        self.db.refresh(account)
        return self._to_account_read(account)

    def cancel_settlement(self, settlement_id: int) -> FinancialAccountRead:
        settlement = self.db.get(FinancialSettlement, settlement_id)
        if not settlement:
            raise NotFoundError("Baixa nao encontrada")
        if settlement.is_cancelled:
            raise BusinessRuleError("Baixa ja estornada")
        installment = settlement.installment

        installment.interest = q_money(
            to_decimal(installment.interest) - to_decimal(settlement.interest)
        )
        installment.fine = q_money(to_decimal(installment.fine) - to_decimal(settlement.fine))
        installment.discount = q_money(
            to_decimal(installment.discount) - to_decimal(settlement.discount)
        )
        installment.amount_paid = q_money(
            to_decimal(installment.amount_paid) - to_decimal(settlement.amount)
        )
        settlement.is_cancelled = True
        self._recompute_installment(installment)

        txn = self.db.execute(
            select(BankTransaction).where(
                BankTransaction.settlement_id == settlement.id,
                BankTransaction.is_cancelled.is_(False),
            )
        ).scalar_one_or_none()
        if txn:
            bank = self.db.get(BankAccount, txn.bank_account_id)
            delta = txn.amount if txn.type == BankTransactionType.CREDIT else -txn.amount
            bank.current_balance = q_money(to_decimal(bank.current_balance) - to_decimal(delta))
            txn.is_cancelled = True

        account = installment.account
        self._recompute_account(account)
        self.audit.log(
            AuditAction.CANCEL, entity="BaixaFinanceira", entity_id=settlement.id
        )
        self.db.commit()
        self.db.refresh(account)
        return self._to_account_read(account)

    def cancel_account(self, account_id: int) -> FinancialAccountRead:
        account = self._get_account(account_id)
        if account.status == FinancialStatus.CANCELLED:
            raise BusinessRuleError("Conta ja cancelada")
        if account.total_paid > 0:
            raise BusinessRuleError("Estorne as baixas antes de cancelar a conta")
        account.status = FinancialStatus.CANCELLED
        for installment in account.installments:
            installment.status = FinancialStatus.CANCELLED
        self.audit.log(AuditAction.CANCEL, entity="ContaFinanceira", entity_id=account.id)
        self.db.commit()
        self.db.refresh(account)
        return self._to_account_read(account)

    # --- reads / queries ---
    def get_account(self, account_id: int) -> FinancialAccountRead:
        return self._to_account_read(self._get_account(account_id))

    def list_accounts(self, params: PageParams, **filters) -> Page[FinancialAccountRead]:
        stmt = self.repo.search(**filters)
        items, total = self.repo.paginate(params, stmt)
        return Page.create([self._to_account_read(a) for a in items], total, params)

    def suggested_charges(self, installment_id: int) -> SuggestedCharges:
        installment = self.db.get(FinancialInstallment, installment_id)
        if not installment:
            raise NotFoundError("Parcela nao encontrada")
        today = date.today()
        if installment.effective_status(today) != FinancialStatus.OVERDUE:
            return SuggestedCharges(days_overdue=0, interest=0, fine=0, balance=installment.balance)
        days = (today - installment.due_date).days
        bal = to_decimal(installment.balance)
        return SuggestedCharges(
            days_overdue=days,
            interest=float(q_money(bal * DAILY_INTEREST_RATE * days)),
            fine=float(q_money(bal * FINE_RATE)),
            balance=installment.balance,
        )

    def _period_key(self, d: date, group_by: str) -> str:
        if group_by == "day":
            return d.isoformat()
        if group_by == "week":
            iso = d.isocalendar()
            return f"{iso.year}-W{iso.week:02d}"
        return d.strftime("%Y-%m")

    def cashflow(self, start: date, end: date, group_by: str = "month") -> CashFlowReport:
        if group_by not in ("day", "week", "month"):
            raise BusinessRuleError("group_by deve ser 'day', 'week' ou 'month'")
        buckets: dict[str, dict] = {}

        def bucket(key: str) -> dict:
            return buckets.setdefault(
                key,
                {"ie": Decimal("0"), "oe": Decimal("0"), "ir": Decimal("0"), "or_": Decimal("0")},
            )

        # Expected: open/partial installments by due date.
        expected = self.db.execute(
            select(FinancialInstallment, FinancialAccount.direction)
            .join(FinancialAccount, FinancialAccount.id == FinancialInstallment.account_id)
            .where(
                FinancialInstallment.status.in_(
                    [FinancialStatus.OPEN, FinancialStatus.PARTIAL]
                ),
                FinancialInstallment.due_date >= start,
                FinancialInstallment.due_date <= end,
            )
        ).all()
        for inst, direction in expected:
            b = bucket(self._period_key(inst.due_date, group_by))
            bal = to_decimal(inst.balance)
            if direction == FinancialDirection.RECEIVABLE:
                b["ie"] += bal
            else:
                b["oe"] += bal

        # Realized: settlements by settlement date.
        realized = self.db.execute(
            select(FinancialSettlement, FinancialAccount.direction)
            .join(
                FinancialInstallment,
                FinancialInstallment.id == FinancialSettlement.installment_id,
            )
            .join(FinancialAccount, FinancialAccount.id == FinancialInstallment.account_id)
            .where(
                FinancialSettlement.is_cancelled.is_(False),
                FinancialSettlement.settled_at >= start,
                FinancialSettlement.settled_at <= end,
            )
        ).all()
        for s, direction in realized:
            b = bucket(self._period_key(s.settled_at, group_by))
            amt = to_decimal(s.amount)
            if direction == FinancialDirection.RECEIVABLE:
                b["ir"] += amt
            else:
                b["or_"] += amt

        def to_period(key: str, b: dict) -> CashFlowPeriod:
            return CashFlowPeriod(
                period=key,
                inflow_expected=float(q_money(b["ie"])),
                outflow_expected=float(q_money(b["oe"])),
                inflow_realized=float(q_money(b["ir"])),
                outflow_realized=float(q_money(b["or_"])),
                net_expected=float(q_money(b["ie"] - b["oe"])),
                net_realized=float(q_money(b["ir"] - b["or_"])),
            )

        periods = [to_period(k, b) for k, b in sorted(buckets.items())]
        agg = {"ie": Decimal("0"), "oe": Decimal("0"), "ir": Decimal("0"), "or_": Decimal("0")}
        for b in buckets.values():
            for k in agg:
                agg[k] += b[k]
        totals = to_period("total", agg)
        return CashFlowReport(
            start=start, end=end, group_by=group_by, totals=totals, periods=periods
        )

    def dashboard(self) -> FinanceDashboard:
        today = date.today()
        month_start = today.replace(day=1)
        acc = {
            "recv_open": Decimal("0"), "recv_over": Decimal("0"),
            "pay_open": Decimal("0"), "pay_over": Decimal("0"),
            "recv_today": Decimal("0"), "recv_month": Decimal("0"),
            "pay_today": Decimal("0"), "pay_month": Decimal("0"),
        }
        open_rows = self.db.execute(
            select(FinancialInstallment, FinancialAccount.direction)
            .join(FinancialAccount, FinancialAccount.id == FinancialInstallment.account_id)
            .where(FinancialInstallment.status.in_([FinancialStatus.OPEN, FinancialStatus.PARTIAL]))
        ).all()
        for inst, direction in open_rows:
            bal = to_decimal(inst.balance)
            if bal <= 0:
                continue
            overdue = inst.due_date < today
            if direction == FinancialDirection.RECEIVABLE:
                acc["recv_open"] += bal
                if overdue:
                    acc["recv_over"] += bal
            else:
                acc["pay_open"] += bal
                if overdue:
                    acc["pay_over"] += bal

        settle_rows = self.db.execute(
            select(FinancialSettlement, FinancialAccount.direction)
            .join(
                FinancialInstallment,
                FinancialInstallment.id == FinancialSettlement.installment_id,
            )
            .join(FinancialAccount, FinancialAccount.id == FinancialInstallment.account_id)
            .where(FinancialSettlement.is_cancelled.is_(False))
        ).all()
        for s, direction in settle_rows:
            amt = to_decimal(s.amount)
            in_month = s.settled_at >= month_start
            is_today = s.settled_at == today
            if direction == FinancialDirection.RECEIVABLE:
                if is_today:
                    acc["recv_today"] += amt
                if in_month:
                    acc["recv_month"] += amt
            else:
                if is_today:
                    acc["pay_today"] += amt
                if in_month:
                    acc["pay_month"] += amt

        banks = list(
            self.db.execute(select(BankAccount).order_by(BankAccount.name)).scalars().all()
        )
        cash_total = sum((to_decimal(b.current_balance) for b in banks), Decimal("0"))
        return FinanceDashboard(
            receivable_open=float(q_money(acc["recv_open"])),
            receivable_overdue=float(q_money(acc["recv_over"])),
            received_today=float(q_money(acc["recv_today"])),
            received_month=float(q_money(acc["recv_month"])),
            payable_open=float(q_money(acc["pay_open"])),
            payable_overdue=float(q_money(acc["pay_over"])),
            paid_today=float(q_money(acc["pay_today"])),
            paid_month=float(q_money(acc["pay_month"])),
            cash_total=float(q_money(cash_total)),
            banks=[
                BankBalance(id=b.id, name=b.name, balance=float(b.current_balance)) for b in banks
            ],
        )

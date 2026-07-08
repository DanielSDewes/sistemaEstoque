"""Financial module endpoints: registrations, accounts, settlements, reports."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_page_params, get_request_context, require_permission
from app.api.v1._crud_factory import build_crud_router
from app.core.database import get_db
from app.core.pagination import Page, PageParams
from app.models.enums import FinancialDirection, FinancialStatus
from app.schemas.finance import (
    BankAccountCreate,
    BankAccountRead,
    BankAccountUpdate,
    CashFlowReport,
    CostCenterCreate,
    CostCenterRead,
    CostCenterUpdate,
    FinanceDashboard,
    FinancialAccountCreate,
    FinancialAccountRead,
    FinancialAccountUpdate,
    FinancialCategoryCreate,
    FinancialCategoryRead,
    FinancialCategoryUpdate,
    PaymentMethodCreate,
    PaymentMethodRead,
    PaymentMethodUpdate,
    SettlementCreate,
    SuggestedCharges,
)
from app.services.audit import RequestContext
from app.services.finance import (
    BankAccountService,
    CostCenterService,
    FinanceService,
    FinancialCategoryService,
    PaymentMethodService,
)

router = APIRouter(prefix="/finance", tags=["Financeiro"])

# --- Supporting registrations (standard CRUD behind the 'finance' permission) ---
router.include_router(
    build_crud_router(
        prefix="/payment-methods", tag="Financeiro", permission="finance",
        service_cls=PaymentMethodService,
        create_schema=PaymentMethodCreate, update_schema=PaymentMethodUpdate,
        read_schema=PaymentMethodRead,
    )
)
router.include_router(
    build_crud_router(
        prefix="/categories", tag="Financeiro", permission="finance",
        service_cls=FinancialCategoryService,
        create_schema=FinancialCategoryCreate, update_schema=FinancialCategoryUpdate,
        read_schema=FinancialCategoryRead,
    )
)
router.include_router(
    build_crud_router(
        prefix="/cost-centers", tag="Financeiro", permission="finance",
        service_cls=CostCenterService,
        create_schema=CostCenterCreate, update_schema=CostCenterUpdate,
        read_schema=CostCenterRead,
    )
)
router.include_router(
    build_crud_router(
        prefix="/bank-accounts", tag="Financeiro", permission="finance",
        service_cls=BankAccountService,
        create_schema=BankAccountCreate, update_schema=BankAccountUpdate,
        read_schema=BankAccountRead,
    )
)


# --- Reports (declared before /accounts/{id} to avoid path clashes) ---
@router.get(
    "/cashflow", response_model=CashFlowReport, summary="Fluxo de caixa (previsto x realizado)"
)
def cashflow(
    start: date | None = None,
    end: date | None = None,
    group_by: str = Query("month", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
    _=Depends(require_permission("finance:view")),
) -> CashFlowReport:
    today = date.today()
    end = end or (today + timedelta(days=60))
    start = start or (today - timedelta(days=30))
    return FinanceService(db).cashflow(start, end, group_by)


@router.get("/dashboard", response_model=FinanceDashboard, summary="Dashboard financeiro")
def finance_dashboard(
    db: Session = Depends(get_db),
    _=Depends(require_permission("finance:view")),
) -> FinanceDashboard:
    return FinanceService(db).dashboard()


# --- Accounts ---
@router.get(
    "/accounts", response_model=Page[FinancialAccountRead], summary="Listar contas financeiras"
)
def list_accounts(
    direction: FinancialDirection | None = None,
    account_status: FinancialStatus | None = Query(None, alias="status"),
    customer_id: int | None = None,
    supplier_id: int | None = None,
    category_id: int | None = None,
    overdue: bool | None = None,
    due_from: date | None = None,
    due_to: date | None = None,
    q: str | None = None,
    params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
    _=Depends(require_permission("finance:view")),
) -> Page[FinancialAccountRead]:
    # 'vencido' is derived, not stored: translate it into the overdue filter.
    if account_status == FinancialStatus.OVERDUE:
        overdue = True
        account_status = None
    return FinanceService(db).list_accounts(
        params,
        direction=direction,
        status=account_status,
        customer_id=customer_id,
        supplier_id=supplier_id,
        category_id=category_id,
        overdue=overdue,
        due_from=due_from,
        due_to=due_to,
        term=q,
    )


@router.get(
    "/accounts/{account_id}", response_model=FinancialAccountRead, summary="Detalhe da conta"
)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("finance:view")),
) -> FinancialAccountRead:
    return FinanceService(db).get_account(account_id)


@router.post(
    "/accounts", response_model=FinancialAccountRead, status_code=status.HTTP_201_CREATED,
    summary="Criar conta (com parcelas)",
)
def create_account(
    payload: FinancialAccountCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("finance:create")),
) -> FinancialAccountRead:
    return FinanceService(db, ctx).create_account(payload)


@router.put(
    "/accounts/{account_id}", response_model=FinancialAccountRead, summary="Atualizar conta"
)
def update_account(
    account_id: int,
    payload: FinancialAccountUpdate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("finance:update")),
) -> FinancialAccountRead:
    return FinanceService(db, ctx).update_account(account_id, payload)


@router.post(
    "/accounts/{account_id}/cancel", response_model=FinancialAccountRead, summary="Cancelar conta"
)
def cancel_account(
    account_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("finance:cancel")),
) -> FinancialAccountRead:
    return FinanceService(db, ctx).cancel_account(account_id)


# --- Installments / settlements (baixas) ---
@router.get(
    "/installments/{installment_id}/suggested-charges",
    response_model=SuggestedCharges,
    summary="Sugestao de juros/multa por atraso",
)
def suggested_charges(
    installment_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("finance:view")),
) -> SuggestedCharges:
    return FinanceService(db).suggested_charges(installment_id)


@router.post(
    "/installments/{installment_id}/settlements",
    response_model=FinancialAccountRead,
    summary="Registrar baixa (pagamento/recebimento)",
)
def settle(
    installment_id: int,
    payload: SettlementCreate,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("finance:settle")),
) -> FinancialAccountRead:
    return FinanceService(db, ctx).settle(installment_id, payload)


@router.post(
    "/settlements/{settlement_id}/cancel",
    response_model=FinancialAccountRead,
    summary="Estornar baixa",
)
def cancel_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _=Depends(require_permission("finance:settle")),
) -> FinancialAccountRead:
    return FinanceService(db, ctx).cancel_settlement(settlement_id)

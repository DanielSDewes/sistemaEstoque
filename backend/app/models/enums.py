"""Enumerations shared across models and schemas."""
import enum


class StatusEnum(str, enum.Enum):
    ACTIVE = "ativo"
    INACTIVE = "inativo"


class MovementDirection(str, enum.Enum):
    IN = "entrada"
    OUT = "saida"


class MovementType(str, enum.Enum):
    # Entradas
    PURCHASE = "compra"
    ADJUSTMENT_IN = "ajuste_entrada"
    RETURN = "devolucao"
    PRODUCTION = "producao"
    # Saidas
    SALE = "venda"
    INTERNAL_USE = "consumo_interno"
    LOSS = "perda"
    BREAKAGE = "quebra"
    TRANSFER = "transferencia"
    ADJUSTMENT_OUT = "ajuste_saida"
    # Inventory reconciliation
    INVENTORY_ADJUSTMENT = "ajuste_inventario"

    @property
    def direction(self) -> MovementDirection:
        return (
            MovementDirection.IN
            if self in _INBOUND_TYPES
            else MovementDirection.OUT
        )


_INBOUND_TYPES = {
    MovementType.PURCHASE,
    MovementType.ADJUSTMENT_IN,
    MovementType.RETURN,
    MovementType.PRODUCTION,
}


class OrderStatus(str, enum.Enum):
    DRAFT = "rascunho"
    CONFIRMED = "confirmado"
    CANCELLED = "cancelado"


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "rascunho"        # being edited, no stock effect yet
    PLACED = "emitido"        # sent to supplier, awaiting delivery
    PARTIAL = "parcial"       # some items received
    RECEIVED = "recebido"     # all items received (stock entries generated)
    CANCELLED = "cancelado"


class FinancialDirection(str, enum.Enum):
    RECEIVABLE = "receber"
    PAYABLE = "pagar"


class FinancialStatus(str, enum.Enum):
    OPEN = "em_aberto"
    PARTIAL = "parcial"
    SETTLED = "quitado"
    OVERDUE = "vencido"  # derived at read time (never stored)
    CANCELLED = "cancelado"
    RENEGOTIATED = "renegociado"


class FinancialCategoryKind(str, enum.Enum):
    INCOME = "receita"
    EXPENSE = "despesa"


class BankTransactionType(str, enum.Enum):
    CREDIT = "credito"
    DEBIT = "debito"


class InventoryStatus(str, enum.Enum):
    OPEN = "em_aberto"
    IN_PROGRESS = "em_andamento"
    FINISHED = "finalizado"
    APPROVED = "aprovado"
    CANCELLED = "cancelado"


class InventoryScope(str, enum.Enum):
    ALL = "todo_estoque"
    CATEGORY = "categoria"
    GROUP = "grupo"
    CORRIDOR = "corredor"
    SHELF = "prateleira"


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "inclusao"
    UPDATE = "alteracao"
    DELETE = "exclusao"
    MOVEMENT = "movimentacao"
    APPROVE = "aprovacao"
    CANCEL = "cancelamento"

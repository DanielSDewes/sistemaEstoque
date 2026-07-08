"""Central catalog of permission codes and default role -> permission mapping."""
from __future__ import annotations

# Resource groups get standard CRUD verbs; special actions are listed explicitly.
_CRUD_RESOURCES = [
    "product",
    "category",
    "group",
    "subgroup",
    "brand",
    "corridor",
    "shelf",
    "supplier",
    "customer",
    "order",
    "finance",
    "user",
    "role",
]

_SPECIAL = {
    "movement:create": "Realizar movimentacoes de estoque",
    "movement:cancel": "Cancelar movimentacoes",
    "inventory:create": "Criar inventarios",
    "inventory:count": "Registrar contagem de inventario",
    "inventory:approve": "Aprovar inventarios",
    "order:confirm": "Confirmar pedidos (baixa estoque)",
    "order:cancel": "Cancelar pedidos (estorna estoque)",
    "finance:settle": "Registrar baixas (pagar/receber)",
    "finance:cancel": "Cancelar contas financeiras",
    "audit:view": "Visualizar auditoria",
    "dashboard:view": "Visualizar dashboard",
    "report:view": "Visualizar e exportar relatorios",
}

_VERB_LABEL = {
    "view": "Visualizar",
    "create": "Inserir",
    "update": "Alterar",
    "delete": "Excluir",
}


def all_permissions() -> dict[str, str]:
    """Return {code: description} for every permission in the system."""
    perms: dict[str, str] = {}
    for resource in _CRUD_RESOURCES:
        for verb, label in _VERB_LABEL.items():
            perms[f"{resource}:{verb}"] = f"{label} {resource}"
    perms.update(_SPECIAL)
    return perms


# --- Default profiles (perfis) required by the spec ---
def _crud(*resources: str) -> set[str]:
    return {f"{r}:{v}" for r in resources for v in _VERB_LABEL}


ADMIN = set(all_permissions().keys())

SUPERVISOR = (
    _crud(
        "product", "category", "group", "subgroup", "brand", "corridor", "shelf",
        "supplier", "customer", "order", "finance",
    )
    | {
        "movement:create",
        "movement:cancel",
        "order:confirm",
        "order:cancel",
        "finance:settle",
        "finance:cancel",
        "inventory:create",
        "inventory:count",
        "inventory:approve",
        "dashboard:view",
        "report:view",
        "audit:view",
        "user:view",
    }
)

OPERATOR = {
    "product:view",
    "product:create",
    "product:update",
    "category:view",
    "group:view",
    "subgroup:view",
    "brand:view",
    "corridor:view",
    "shelf:view",
    "supplier:view",
    "customer:view",
    "customer:create",
    "customer:update",
    "order:view",
    "order:create",
    "order:update",
    "order:confirm",
    "finance:view",
    "finance:settle",
    "movement:create",
    "inventory:count",
    "dashboard:view",
    "report:view",
}

READ_ONLY = {
    f"{r}:view"
    for r in [
        "product", "category", "group", "subgroup", "brand", "corridor", "shelf",
        "supplier", "customer", "order", "finance",
    ]
} | {"dashboard:view", "report:view"}


DEFAULT_ROLES: dict[str, dict[str, object]] = {
    "Administrador": {"description": "Acesso total ao sistema", "permissions": ADMIN},
    "Supervisor": {"description": "Gestao operacional e aprovacoes", "permissions": SUPERVISOR},
    "Operador": {"description": "Operacao de estoque", "permissions": OPERATOR},
    "Somente Consulta": {"description": "Acesso somente leitura", "permissions": READ_ONLY},
}

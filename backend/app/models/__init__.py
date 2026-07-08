"""ORM models package.

Importing every model here guarantees they are registered on the shared
``Base.metadata`` before Alembic autogenerate or ``create_all`` run.
"""
from app.models.audit import AuditLog  # noqa: F401
from app.models.catalog import (  # noqa: F401
    Brand,
    Category,
    Group,
    Subgroup,
)
from app.models.customer import Customer, CustomerAddress  # noqa: F401
from app.models.finance import (  # noqa: F401
    BankAccount,
    BankTransaction,
    CostCenter,
    FinancialAccount,
    FinancialCategory,
    FinancialInstallment,
    FinancialSettlement,
    PaymentMethod,
)
from app.models.inventory import Inventory, InventoryItem  # noqa: F401
from app.models.location import Corridor, ProductLocation, Shelf  # noqa: F401
from app.models.movement import StockMovement  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
from app.models.product import Batch, Product  # noqa: F401
from app.models.security import RevokedToken  # noqa: F401
from app.models.supplier import (  # noqa: F401
    ProductSupplier,
    Supplier,
    SupplierPriceHistory,
)
from app.models.user import Permission, Role, User, role_permissions  # noqa: F401

__all__ = [
    "AuditLog",
    "Brand",
    "Category",
    "Group",
    "Subgroup",
    "Customer",
    "CustomerAddress",
    "PaymentMethod",
    "FinancialCategory",
    "CostCenter",
    "BankAccount",
    "FinancialAccount",
    "FinancialInstallment",
    "FinancialSettlement",
    "BankTransaction",
    "Inventory",
    "InventoryItem",
    "Corridor",
    "Shelf",
    "ProductLocation",
    "StockMovement",
    "Order",
    "OrderItem",
    "Product",
    "Batch",
    "Supplier",
    "ProductSupplier",
    "SupplierPriceHistory",
    "User",
    "Role",
    "Permission",
    "role_permissions",
    "RevokedToken",
]

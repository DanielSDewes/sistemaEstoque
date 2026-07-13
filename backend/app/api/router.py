"""Aggregate API router mounting every v1 sub-router."""
from fastapi import APIRouter

from app.api.v1 import (
    alerts,
    audit,
    auth,
    customers,
    dashboard,
    finance,
    inventory,
    movements,
    orders,
    products,
    purchase,
    reports,
    stock_items,
    users,
)
from app.api.v1.catalog import (
    brands_router,
    categories_router,
    groups_router,
    subgroups_router,
)
from app.api.v1.locations import corridors_router, shelves_router
from app.api.v1.suppliers import product_suppliers_router, suppliers_router

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(dashboard.router)
api_router.include_router(alerts.router)
api_router.include_router(customers.router)
api_router.include_router(orders.router)
api_router.include_router(purchase.router)
api_router.include_router(finance.router)
api_router.include_router(products.router)
api_router.include_router(stock_items.router)
api_router.include_router(categories_router)
api_router.include_router(groups_router)
api_router.include_router(subgroups_router)
api_router.include_router(brands_router)
api_router.include_router(corridors_router)
api_router.include_router(shelves_router)
api_router.include_router(suppliers_router)
api_router.include_router(product_suppliers_router)
api_router.include_router(movements.router)
api_router.include_router(inventory.router)
api_router.include_router(audit.router)
api_router.include_router(reports.router)

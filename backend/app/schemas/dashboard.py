"""Dashboard indicator and chart schemas."""
from pydantic import BaseModel


class KpiCards(BaseModel):
    total_products: int
    products_no_stock: int
    products_below_min: int
    products_near_expiry: int
    movements_today: int
    total_stock_quantity: float
    total_stock_value: float
    total_suppliers: int


class SeriesPoint(BaseModel):
    label: str
    value: float


class NamedSeries(BaseModel):
    name: str
    points: list[SeriesPoint]


class DashboardResponse(BaseModel):
    kpis: KpiCards
    movements_by_day: list[SeriesPoint]
    top_moved_products: list[SeriesPoint]
    stock_by_category: list[SeriesPoint]
    entries_vs_exits: list[NamedSeries]

"""Corridor and Shelf routers."""
from app.api.v1._crud_factory import build_crud_router
from app.schemas.location import (
    CorridorCreate,
    CorridorRead,
    CorridorUpdate,
    ShelfCreate,
    ShelfRead,
    ShelfUpdate,
)
from app.services.location import CorridorService, ShelfService

corridors_router = build_crud_router(
    prefix="/corridors", tag="Corredores", permission="corridor",
    service_cls=CorridorService,
    create_schema=CorridorCreate, update_schema=CorridorUpdate, read_schema=CorridorRead,
)

shelves_router = build_crud_router(
    prefix="/shelves", tag="Prateleiras", permission="shelf",
    service_cls=ShelfService,
    create_schema=ShelfCreate, update_schema=ShelfUpdate, read_schema=ShelfRead,
)

"""Catalog routers (Category, Group, Subgroup, Brand) built via the factory."""
from app.api.v1._crud_factory import build_crud_router
from app.schemas.catalog import CatalogCreate, CatalogRead, CatalogUpdate
from app.services.catalog import (
    BrandService,
    CategoryService,
    GroupService,
    SubgroupService,
)

categories_router = build_crud_router(
    prefix="/categories", tag="Categorias", permission="category",
    service_cls=CategoryService,
    create_schema=CatalogCreate, update_schema=CatalogUpdate, read_schema=CatalogRead,
)

groups_router = build_crud_router(
    prefix="/groups", tag="Grupos", permission="group",
    service_cls=GroupService,
    create_schema=CatalogCreate, update_schema=CatalogUpdate, read_schema=CatalogRead,
)

subgroups_router = build_crud_router(
    prefix="/subgroups", tag="Subgrupos", permission="subgroup",
    service_cls=SubgroupService,
    create_schema=CatalogCreate, update_schema=CatalogUpdate, read_schema=CatalogRead,
)

brands_router = build_crud_router(
    prefix="/brands", tag="Marcas", permission="brand",
    service_cls=BrandService,
    create_schema=CatalogCreate, update_schema=CatalogUpdate, read_schema=CatalogRead,
)

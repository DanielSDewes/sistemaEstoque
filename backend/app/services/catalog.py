"""Services for the independent catalog taxonomies."""
from app.core.exceptions import ConflictError
from app.models.catalog import Brand, Category, Group, Subgroup
from app.schemas.catalog import CatalogRead
from app.services.base import CrudService


class _CatalogService(CrudService):
    read_schema = CatalogRead

    def _pre_create(self, data: dict) -> None:
        if self.repo.get_by(code=data["code"]):
            raise ConflictError(f"Ja existe {self.entity_name} com o codigo {data['code']}")

    def _pre_update(self, obj, data: dict) -> None:  # noqa: ANN001
        if "code" in data and data["code"] != obj.code and self.repo.get_by(code=data["code"]):
            raise ConflictError(f"Ja existe {self.entity_name} com o codigo {data['code']}")


class CategoryService(_CatalogService):
    model = Category
    entity_name = "Categoria"


class GroupService(_CatalogService):
    model = Group
    entity_name = "Grupo"


class SubgroupService(_CatalogService):
    model = Subgroup
    entity_name = "Subgrupo"


class BrandService(_CatalogService):
    model = Brand
    entity_name = "Marca"

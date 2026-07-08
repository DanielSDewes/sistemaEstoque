"""Corridor and Shelf services."""
from app.core.exceptions import ConflictError, NotFoundError
from app.models.location import Corridor, Shelf
from app.schemas.location import CorridorRead, ShelfRead
from app.services.base import CrudService


class CorridorService(CrudService):
    model = Corridor
    read_schema = CorridorRead
    entity_name = "Corredor"

    def _pre_create(self, data: dict) -> None:
        if self.repo.get_by(code=data["code"]):
            raise ConflictError(f"Ja existe corredor com o codigo {data['code']}")


class ShelfService(CrudService):
    model = Shelf
    read_schema = ShelfRead
    entity_name = "Prateleira"

    def _pre_create(self, data: dict) -> None:
        from app.repositories.base import BaseRepository

        if not BaseRepository(Corridor, self.db).get(data["corridor_id"]):
            raise NotFoundError("Corredor informado nao existe")

"""Generic repository implementing common CRUD + pagination."""
from typing import Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.pagination import PageParams

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """CRUD helpers shared by all concrete repositories."""

    def __init__(self, model: type[ModelT], db: Session) -> None:
        self.model = model
        self.db = db

    def get(self, obj_id: int) -> ModelT | None:
        return self.db.get(self.model, obj_id)

    def get_by(self, **filters: object) -> ModelT | None:
        stmt = select(self.model).filter_by(**filters).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, stmt: Select | None = None) -> list[ModelT]:
        stmt = stmt if stmt is not None else select(self.model)
        return list(self.db.execute(stmt).scalars().all())

    def paginate(
        self, params: PageParams, stmt: Select | None = None
    ) -> tuple[list[ModelT], int]:
        """Return (items, total) applying ordering, offset and limit."""
        base_stmt = stmt if stmt is not None else select(self.model)

        count_stmt = select(func.count()).select_from(base_stmt.order_by(None).subquery())
        total = self.db.execute(count_stmt).scalar_one()

        if params.sort_by and hasattr(self.model, params.sort_by):
            column = getattr(self.model, params.sort_by)
            base_stmt = base_stmt.order_by(
                column.desc() if params.sort_dir == "desc" else column.asc()
            )
        elif hasattr(self.model, "id"):
            base_stmt = base_stmt.order_by(self.model.id.desc())

        base_stmt = base_stmt.offset(params.offset).limit(params.size)
        items = list(self.db.execute(base_stmt).scalars().all())
        return items, total

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        return obj

    def create(self, **data: object) -> ModelT:
        obj = self.model(**data)
        return self.add(obj)

    def update(self, obj: ModelT, data: dict[str, object]) -> ModelT:
        for key, value in data.items():
            setattr(obj, key, value)
        self.db.flush()
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()

    def count(self, stmt: Select | None = None) -> int:
        base = stmt if stmt is not None else select(self.model)
        return self.db.execute(
            select(func.count()).select_from(base.order_by(None).subquery())
        ).scalar_one()

"""Generic CRUD service with built-in auditing, reused by simple entities."""
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import NotFoundError
from app.core.pagination import Page, PageParams
from app.models.enums import AuditAction
from app.repositories.base import BaseRepository
from app.services.audit import AuditService, RequestContext

ModelT = TypeVar("ModelT", bound=Base)
ReadT = TypeVar("ReadT", bound=BaseModel)


class CrudService(Generic[ModelT, ReadT]):
    """Reusable create/read/update/delete with audit logging.

    Concrete services set ``model``, ``read_schema`` and ``entity_name`` and may
    override hooks such as ``_pre_create`` for uniqueness checks.
    """

    model: type[ModelT]
    read_schema: type[ReadT]
    entity_name: str

    def __init__(self, db: Session, ctx: RequestContext | None = None) -> None:
        self.db = db
        self.ctx = ctx or RequestContext()
        self.repo = BaseRepository(self.model, db)
        self.audit = AuditService(db, self.ctx)

    # --- hooks (override as needed) ---
    def _pre_create(self, data: dict) -> None:  # noqa: ANN001
        pass

    def _pre_update(self, obj: ModelT, data: dict) -> None:  # noqa: ANN001
        pass

    def _base_query(self) -> Select | None:
        return None

    # --- operations ---
    def get(self, obj_id: int) -> ReadT:
        obj = self.repo.get(obj_id)
        if not obj:
            raise NotFoundError(f"{self.entity_name} nao encontrado")
        return self.read_schema.model_validate(obj)

    def list(self, params: PageParams, stmt: Select | None = None) -> Page[ReadT]:
        stmt = stmt if stmt is not None else self._base_query()
        items, total = self.repo.paginate(params, stmt)
        reads = [self.read_schema.model_validate(i) for i in items]
        return Page.create(reads, total, params)

    def create(self, payload: BaseModel) -> ReadT:
        data = payload.model_dump()
        self._pre_create(data)
        obj = self.repo.create(**data)
        self.audit.log(
            AuditAction.CREATE,
            entity=self.entity_name,
            entity_id=obj.id,
            new_value=getattr(obj, "name", None) or getattr(obj, "id", None),
        )
        self.db.commit()
        self.db.refresh(obj)
        return self.read_schema.model_validate(obj)

    def update(self, obj_id: int, payload: BaseModel) -> ReadT:
        obj = self.repo.get(obj_id)
        if not obj:
            raise NotFoundError(f"{self.entity_name} nao encontrado")
        data = payload.model_dump(exclude_unset=True)
        self._pre_update(obj, data)
        before = {k: getattr(obj, k) for k in data}
        self.repo.update(obj, data)
        self.audit.log_diff(AuditAction.UPDATE, self.entity_name, obj.id, before, data)
        self.db.commit()
        self.db.refresh(obj)
        return self.read_schema.model_validate(obj)

    def delete(self, obj_id: int) -> None:
        obj = self.repo.get(obj_id)
        if not obj:
            raise NotFoundError(f"{self.entity_name} nao encontrado")
        self.audit.log(AuditAction.DELETE, entity=self.entity_name, entity_id=obj.id)
        self.repo.delete(obj)
        self.db.commit()

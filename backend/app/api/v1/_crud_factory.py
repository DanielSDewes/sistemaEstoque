"""Factory that builds a standard CRUD router for a simple entity/service."""
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_page_params, get_request_context, require_permission
from app.core.database import get_db
from app.core.pagination import Page, PageParams
from app.schemas.common import Message
from app.services.audit import RequestContext


def build_crud_router(
    *,
    prefix: str,
    tag: str,
    permission: str,
    service_cls: type,
    create_schema: type,
    update_schema: type,
    read_schema: type,
) -> APIRouter:
    """Wire the 5 standard CRUD endpoints for an entity behind RBAC guards."""
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.get("", response_model=Page[read_schema], summary=f"Listar {tag}")
    def list_items(
        params: PageParams = Depends(get_page_params),
        db: Session = Depends(get_db),
        _=Depends(require_permission(f"{permission}:view")),
    ) -> Any:
        return service_cls(db).list(params)

    @router.get("/{item_id}", response_model=read_schema, summary=f"Detalhe de {tag}")
    def get_item(
        item_id: int,
        db: Session = Depends(get_db),
        _=Depends(require_permission(f"{permission}:view")),
    ) -> Any:
        return service_cls(db).get(item_id)

    @router.post(
        "", response_model=read_schema, status_code=status.HTTP_201_CREATED,
        summary=f"Criar {tag}",
    )
    def create_item(
        payload: create_schema,  # type: ignore[valid-type]
        db: Session = Depends(get_db),
        ctx: RequestContext = Depends(get_request_context),
        _=Depends(require_permission(f"{permission}:create")),
    ) -> Any:
        return service_cls(db, ctx).create(payload)

    @router.put("/{item_id}", response_model=read_schema, summary=f"Atualizar {tag}")
    def update_item(
        item_id: int,
        payload: update_schema,  # type: ignore[valid-type]
        db: Session = Depends(get_db),
        ctx: RequestContext = Depends(get_request_context),
        _=Depends(require_permission(f"{permission}:update")),
    ) -> Any:
        return service_cls(db, ctx).update(item_id, payload)

    @router.delete("/{item_id}", response_model=Message, summary=f"Excluir {tag}")
    def delete_item(
        item_id: int,
        db: Session = Depends(get_db),
        ctx: RequestContext = Depends(get_request_context),
        _=Depends(require_permission(f"{permission}:delete")),
    ) -> Message:
        service_cls(db, ctx).delete(item_id)
        return Message(detail=f"{tag} excluido")

    return router

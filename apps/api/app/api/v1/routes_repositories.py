from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from acp_core.schemas import RepositoryCreate, RepositoryRead
from app.api.ws.events import broadcast_change
from app.bootstrap.dependencies import get_repository_service

router = APIRouter(tags=["repositories"])


@router.get("/repositories", response_model=list[RepositoryRead])
def list_repositories(
    project_id: str | None = Query(default=None),
    service=Depends(get_repository_service),
) -> list[RepositoryRead]:
    return [RepositoryRead.model_validate(item) for item in service.list_repositories(project_id=project_id)]


@router.post("/repositories", response_model=RepositoryRead, status_code=201)
def create_repository(payload: RepositoryCreate, request: Request, service=Depends(get_repository_service)) -> RepositoryRead:
    try:
        repository = service.create_repository(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = RepositoryRead.model_validate(repository)
    broadcast_change(
        request,
        event_type="repository.created",
        entity_type="repository",
        entity_id=response.id,
        project_id=response.project_id,
        detail={"name": response.name},
    )
    return response


@router.get("/repositories/{repository_id}", response_model=RepositoryRead)
def get_repository(repository_id: str, service=Depends(get_repository_service)) -> RepositoryRead:
    try:
        repository = service.get_repository(repository_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RepositoryRead.model_validate(repository)

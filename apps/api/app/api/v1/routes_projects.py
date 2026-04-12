from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from acp_core.schemas import (
    ProjectBootstrapCreate,
    ProjectBootstrapPreviewRead,
    ProjectBootstrapRead,
    ProjectCreate,
    ProjectOverview,
    ProjectSummary,
)
from app.api.errors import RUNTIME_ERROR_RESPONSES
from app.api.ws.events import broadcast_change
from app.bootstrap.dependencies import get_bootstrap_service, get_project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
def list_projects(service=Depends(get_project_service)) -> list[ProjectSummary]:
    """Handle list projects requests.

    Args:
        service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    return [ProjectSummary.model_validate(project) for project in service.list_projects()]


@router.post("", response_model=ProjectSummary, status_code=201)
def create_project(payload: ProjectCreate, request: Request, service=Depends(get_project_service)) -> ProjectSummary:
    """Handle create project requests.

    Args:
        payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    project = service.create_project(payload)
    response = ProjectSummary.model_validate(project)
    broadcast_change(
        request,
        event_type="project.created",
        entity_type="project",
        entity_id=response.id,
        project_id=response.id,
        detail={"name": response.name},
    )
    return response


@router.post("/bootstrap/preview", response_model=ProjectBootstrapPreviewRead)
def preview_bootstrap_project(
    payload: ProjectBootstrapCreate,
    service=Depends(get_bootstrap_service),
) -> ProjectBootstrapPreviewRead:
    try:
        return service.preview_bootstrap_project(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bootstrap", response_model=ProjectBootstrapRead, status_code=201, responses=RUNTIME_ERROR_RESPONSES)
def bootstrap_project(
    payload: ProjectBootstrapCreate,
    request: Request,
    service=Depends(get_bootstrap_service),
) -> ProjectBootstrapRead:
    """Handle bootstrap project requests.

    Args:
        payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    WHY:
        Keeps workflow/event semantics centralized in services before broadcasting UI invalidation.
    """
    try:
        response = service.bootstrap_project(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    broadcast_change(
        request,
        event_type="project.bootstrapped",
        entity_type="project",
        entity_id=response.project.id,
        project_id=response.project.id,
        task_id=response.kickoff_task.id,
        session_id=response.kickoff_session.id,
        detail={"name": response.project.name, "use_worktree": response.use_worktree},
    )
    return response


@router.get("/{project_id}", response_model=ProjectOverview)
def get_project(project_id: str, service=Depends(get_project_service)) -> ProjectOverview:
    """Handle get project requests.

    Args:
        project_id: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        return service.get_project_overview(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

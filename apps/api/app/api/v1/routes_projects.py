from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from acp_core.schemas import ProjectBootstrapCreate, ProjectBootstrapRead, ProjectCreate, ProjectOverview, ProjectSummary
from app.api.ws.events import broadcast_change
from app.bootstrap.dependencies import get_bootstrap_service, get_project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
def list_projects(service=Depends(get_project_service)) -> list[ProjectSummary]:
    return [ProjectSummary.model_validate(project) for project in service.list_projects()]


@router.post("", response_model=ProjectSummary, status_code=201)
def create_project(payload: ProjectCreate, request: Request, service=Depends(get_project_service)) -> ProjectSummary:
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


@router.post("/bootstrap", response_model=ProjectBootstrapRead, status_code=201)
def bootstrap_project(
    payload: ProjectBootstrapCreate,
    request: Request,
    service=Depends(get_bootstrap_service),
) -> ProjectBootstrapRead:
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
    try:
        return service.get_project_overview(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

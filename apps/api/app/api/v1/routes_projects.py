from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from acp_core.schemas import ProjectCreate, ProjectOverview, ProjectSummary
from app.bootstrap.dependencies import get_project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
def list_projects(service=Depends(get_project_service)) -> list[ProjectSummary]:
    return [ProjectSummary.model_validate(project) for project in service.list_projects()]


@router.post("", response_model=ProjectSummary, status_code=201)
def create_project(payload: ProjectCreate, service=Depends(get_project_service)) -> ProjectSummary:
    project = service.create_project(payload)
    return ProjectSummary.model_validate(project)


@router.get("/{project_id}", response_model=ProjectOverview)
def get_project(project_id: str, service=Depends(get_project_service)) -> ProjectOverview:
    try:
        project = service.get_project(project_id)
        board = service.get_board_view(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ProjectOverview(project=ProjectSummary.model_validate(project), board=board)


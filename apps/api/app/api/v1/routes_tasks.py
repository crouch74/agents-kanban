from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from acp_core.schemas import TaskCreate, TaskPatch, TaskRead
from app.bootstrap.dependencies import get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    project_id: str | None = Query(default=None),
    service=Depends(get_task_service),
) -> list[TaskRead]:
    return [TaskRead.model_validate(task) for task in service.list_tasks(project_id=project_id)]


@router.post("", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, service=Depends(get_task_service)) -> TaskRead:
    try:
        task = service.create_task(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, service=Depends(get_task_service)) -> TaskRead:
    try:
        task = service.get_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
def patch_task(task_id: str, payload: TaskPatch, service=Depends(get_task_service)) -> TaskRead:
    try:
        task = service.patch_task(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskRead.model_validate(task)


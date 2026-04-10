from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from acp_core.schemas import (
    TaskArtifactCreate,
    TaskArtifactRead,
    TaskCheckCreate,
    TaskCheckRead,
    TaskCommentCreate,
    TaskCommentRead,
    TaskCreate,
    TaskDependencyCreate,
    TaskDependencyRead,
    TaskDetail,
    TaskPatch,
    TaskRead,
)
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


@router.get("/{task_id}/detail", response_model=TaskDetail)
def get_task_detail(task_id: str, service=Depends(get_task_service)) -> TaskDetail:
    try:
        return service.get_task_detail(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{task_id}", response_model=TaskRead)
def patch_task(task_id: str, payload: TaskPatch, service=Depends(get_task_service)) -> TaskRead:
    try:
        task = service.patch_task(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskRead.model_validate(task)


@router.post("/{task_id}/comments", response_model=TaskCommentRead, status_code=201)
def add_comment(task_id: str, payload: TaskCommentCreate, service=Depends(get_task_service)) -> TaskCommentRead:
    try:
        comment = service.add_comment(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskCommentRead.model_validate(comment)


@router.post("/{task_id}/checks", response_model=TaskCheckRead, status_code=201)
def add_check(task_id: str, payload: TaskCheckCreate, service=Depends(get_task_service)) -> TaskCheckRead:
    try:
        check = service.add_check(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskCheckRead.model_validate(check)


@router.post("/{task_id}/artifacts", response_model=TaskArtifactRead, status_code=201)
def add_artifact(task_id: str, payload: TaskArtifactCreate, service=Depends(get_task_service)) -> TaskArtifactRead:
    try:
        artifact = service.add_artifact(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskArtifactRead.model_validate(artifact)


@router.get("/{task_id}/dependencies", response_model=list[TaskDependencyRead])
def list_dependencies(task_id: str, service=Depends(get_task_service)) -> list[TaskDependencyRead]:
    try:
        return service.get_dependencies(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{task_id}/dependencies", response_model=TaskDependencyRead, status_code=201)
def add_dependency(
    task_id: str,
    payload: TaskDependencyCreate,
    service=Depends(get_task_service),
) -> TaskDependencyRead:
    try:
        dependency = service.add_dependency(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskDependencyRead.model_validate(dependency)

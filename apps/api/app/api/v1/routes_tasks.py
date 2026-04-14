from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from acp_core.schemas import TaskCommentCreate, TaskCommentRead, TaskCreate, TaskDetail, TaskPatch, TaskRead
from app.api.ws.events import broadcast_change
from app.bootstrap.dependencies import get_task_service
from acp_core.services.task_service import comment_to_read, task_to_read

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    project_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    service=Depends(get_task_service),
) -> list[TaskRead]:
    return [TaskRead(**task_to_read(task)) for task in service.list_tasks(project_id=project_id, status=status, q=q)]


@router.post("", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, request: Request, service=Depends(get_task_service)) -> TaskRead:
    try:
        task = service.create_task(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = TaskRead(**task_to_read(task))
    broadcast_change(
        request,
        event_type="task.created",
        entity_type="task",
        entity_id=response.id,
        project_id=response.project_id,
        task_id=response.id,
        detail={"title": response.title, "workflow_state": response.workflow_state},
    )
    return response


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, service=Depends(get_task_service)) -> TaskRead:
    try:
        task = service.get_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TaskRead(**task_to_read(task))


@router.get("/{task_id}/detail", response_model=TaskDetail)
def get_task_detail(task_id: str, service=Depends(get_task_service)) -> TaskDetail:
    try:
        return service.get_task_detail(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{task_id}", response_model=TaskRead)
def patch_task(task_id: str, payload: TaskPatch, request: Request, service=Depends(get_task_service)) -> TaskRead:
    try:
        task = service.patch_task(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = TaskRead(**task_to_read(task))
    broadcast_change(
        request,
        event_type="task.updated",
        entity_type="task",
        entity_id=response.id,
        project_id=response.project_id,
        task_id=response.id,
        detail={"workflow_state": response.workflow_state},
    )
    return response


@router.get("/{task_id}/comments", response_model=list[TaskCommentRead])
def list_comments(task_id: str, service=Depends(get_task_service)) -> list[TaskCommentRead]:
    try:
        return service.list_comments(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{task_id}/comments", response_model=TaskCommentRead, status_code=201)
def add_comment(task_id: str, payload: TaskCommentCreate, request: Request, service=Depends(get_task_service)) -> TaskCommentRead:
    try:
        comment = service.add_comment(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = comment_to_read(comment)
    task = service.get_task(task_id)
    broadcast_change(
        request,
        event_type="task.comment_added",
        entity_type="task_comment",
        entity_id=response.id,
        project_id=task.project_id,
        task_id=task.id,
        detail={"actor_name": response.author_name, "source": response.source},
    )
    return response

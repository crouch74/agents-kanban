from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

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
from app.api.ws.events import broadcast_change
from app.bootstrap.dependencies import get_task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    project_id: str | None = Query(default=None),
    service=Depends(get_task_service),
) -> list[TaskRead]:
    """Handle list tasks requests.

    Args:
        project_id: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    return [TaskRead.model_validate(task) for task in service.list_tasks(project_id=project_id)]


@router.post("", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, request: Request, service=Depends(get_task_service)) -> TaskRead:
    """Handle create task requests.

    Args:
        payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        task = service.create_task(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = TaskRead.model_validate(task)
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
    """Handle get task requests.

    Args:
        task_id: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        task = service.get_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TaskRead.model_validate(task)


@router.get("/{task_id}/detail", response_model=TaskDetail)
def get_task_detail(task_id: str, service=Depends(get_task_service)) -> TaskDetail:
    """Handle get task detail requests.

    Args:
        task_id: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        return service.get_task_detail(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{task_id}", response_model=TaskRead)
def patch_task(task_id: str, payload: TaskPatch, request: Request, service=Depends(get_task_service)) -> TaskRead:
    """Handle patch task requests.

    Args:
        task_id: from request/signature.; payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    WHY:
        Keeps workflow/event semantics centralized in services before broadcasting UI invalidation.
    """
    try:
        task = service.patch_task(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = TaskRead.model_validate(task)
    broadcast_change(
        request,
        event_type="task.updated",
        entity_type="task",
        entity_id=response.id,
        project_id=response.project_id,
        task_id=response.id,
        detail={"workflow_state": response.workflow_state, "waiting_for_human": response.waiting_for_human},
    )
    return response


@router.post("/{task_id}/comments", response_model=TaskCommentRead, status_code=201)
def add_comment(task_id: str, payload: TaskCommentCreate, request: Request, service=Depends(get_task_service)) -> TaskCommentRead:
    """Handle add comment requests.

    Args:
        task_id: from request/signature.; payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        comment = service.add_comment(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = TaskCommentRead.model_validate(comment)
    task = service.get_task(task_id)
    broadcast_change(
        request,
        event_type="task.comment_added",
        entity_type="task_comment",
        entity_id=response.id,
        project_id=task.project_id,
        task_id=task.id,
        detail={"author_name": response.author_name},
    )
    return response


@router.post("/{task_id}/checks", response_model=TaskCheckRead, status_code=201)
def add_check(task_id: str, payload: TaskCheckCreate, request: Request, service=Depends(get_task_service)) -> TaskCheckRead:
    """Handle add check requests.

    Args:
        task_id: from request/signature.; payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        check = service.add_check(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = TaskCheckRead.model_validate(check)
    task = service.get_task(task_id)
    broadcast_change(
        request,
        event_type="task.check_added",
        entity_type="task_check",
        entity_id=response.id,
        project_id=task.project_id,
        task_id=task.id,
        detail={"status": response.status, "check_type": response.check_type},
    )
    return response


@router.post("/{task_id}/artifacts", response_model=TaskArtifactRead, status_code=201)
def add_artifact(task_id: str, payload: TaskArtifactCreate, request: Request, service=Depends(get_task_service)) -> TaskArtifactRead:
    """Handle add artifact requests.

    Args:
        task_id: from request/signature.; payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        artifact = service.add_artifact(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = TaskArtifactRead.model_validate(artifact)
    task = service.get_task(task_id)
    broadcast_change(
        request,
        event_type="task.artifact_added",
        entity_type="task_artifact",
        entity_id=response.id,
        project_id=task.project_id,
        task_id=task.id,
        detail={"artifact_type": response.artifact_type, "name": response.name},
    )
    return response


@router.get("/{task_id}/dependencies", response_model=list[TaskDependencyRead])
def list_dependencies(task_id: str, service=Depends(get_task_service)) -> list[TaskDependencyRead]:
    """Handle list dependencies requests.

    Args:
        task_id: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        return service.get_dependencies(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{task_id}/dependencies", response_model=TaskDependencyRead, status_code=201)
def add_dependency(
    task_id: str,
    payload: TaskDependencyCreate,
    request: Request,
    service=Depends(get_task_service),
) -> TaskDependencyRead:
    """Handle add dependency requests.

    Args:
        task_id: from request/signature.; payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        dependency = service.add_dependency(task_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = TaskDependencyRead.model_validate(dependency)
    task = service.get_task(task_id)
    broadcast_change(
        request,
        event_type="task.dependency_added",
        entity_type="task_dependency",
        entity_id=response.id,
        project_id=task.project_id,
        task_id=task.id,
        detail={"depends_on_task_id": response.depends_on_task_id},
    )
    return response

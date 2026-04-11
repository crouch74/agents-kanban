from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from acp_core.schemas import WorktreeCreate, WorktreePatch, WorktreeRead
from app.api.ws.events import broadcast_change
from app.bootstrap.dependencies import get_worktree_service

router = APIRouter(tags=["worktrees"])


@router.get("/worktrees", response_model=list[WorktreeRead])
def list_worktrees(
    project_id: str | None = Query(default=None),
    service=Depends(get_worktree_service),
) -> list[WorktreeRead]:
    """Handle list worktrees requests.

    Args:
        project_id: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    return [WorktreeRead.model_validate(item) for item in service.list_worktrees(project_id=project_id)]


@router.post("/worktrees", response_model=WorktreeRead, status_code=201)
def create_worktree(payload: WorktreeCreate, request: Request, service=Depends(get_worktree_service)) -> WorktreeRead:
    """Handle create worktree requests.

    Args:
        payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        worktree = service.create_worktree(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = WorktreeRead.model_validate(worktree)
    broadcast_change(
        request,
        event_type="worktree.created",
        entity_type="worktree",
        entity_id=response.id,
        task_id=response.task_id,
        session_id=response.session_id,
        detail={"branch_name": response.branch_name},
    )
    return response


@router.get("/worktrees/{worktree_id}", response_model=WorktreeRead)
def get_worktree(worktree_id: str, service=Depends(get_worktree_service)) -> WorktreeRead:
    """Handle get worktree requests.

    Args:
        worktree_id: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    """
    try:
        worktree = service.get_worktree(worktree_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WorktreeRead.model_validate(worktree)


@router.patch("/worktrees/{worktree_id}", response_model=WorktreeRead)
def patch_worktree(
    worktree_id: str,
    payload: WorktreePatch,
    request: Request,
    service=Depends(get_worktree_service),
) -> WorktreeRead:
    """Handle patch worktree requests.

    Args:
        worktree_id: from request/signature.; payload: from request/signature.; request: from request/signature.; service: from request/signature.

    Returns:
        Response model declared by the route decorator.

    Raises:
        HTTPException: Mirrors service-layer ValueError as 4xx responses.
    WHY:
        Keeps workflow/event semantics centralized in services before broadcasting UI invalidation.
    """
    try:
        worktree = service.patch_worktree(worktree_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = WorktreeRead.model_validate(worktree)
    broadcast_change(
        request,
        event_type="worktree.updated",
        entity_type="worktree",
        entity_id=response.id,
        task_id=response.task_id,
        session_id=response.session_id,
        detail={"status": response.status},
    )
    return response

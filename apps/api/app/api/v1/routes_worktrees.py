from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from acp_core.schemas import WorktreeCreate, WorktreePatch, WorktreeRead
from app.bootstrap.dependencies import get_worktree_service

router = APIRouter(tags=["worktrees"])


@router.get("/worktrees", response_model=list[WorktreeRead])
def list_worktrees(
    project_id: str | None = Query(default=None),
    service=Depends(get_worktree_service),
) -> list[WorktreeRead]:
    return [WorktreeRead.model_validate(item) for item in service.list_worktrees(project_id=project_id)]


@router.post("/worktrees", response_model=WorktreeRead, status_code=201)
def create_worktree(payload: WorktreeCreate, service=Depends(get_worktree_service)) -> WorktreeRead:
    try:
        worktree = service.create_worktree(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorktreeRead.model_validate(worktree)


@router.get("/worktrees/{worktree_id}", response_model=WorktreeRead)
def get_worktree(worktree_id: str, service=Depends(get_worktree_service)) -> WorktreeRead:
    try:
        worktree = service.get_worktree(worktree_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WorktreeRead.model_validate(worktree)


@router.patch("/worktrees/{worktree_id}", response_model=WorktreeRead)
def patch_worktree(
    worktree_id: str,
    payload: WorktreePatch,
    service=Depends(get_worktree_service),
) -> WorktreeRead:
    try:
        worktree = service.patch_worktree(worktree_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorktreeRead.model_validate(worktree)

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from acp_core.schemas import EventRecord
from app.bootstrap.dependencies import get_event_service

router = APIRouter(tags=["events"])


@router.get("/events", response_model=list[EventRecord])
def list_events(
    project_id: str | None = Query(default=None),
    task_id: str | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=200),
    service=Depends(get_event_service),
) -> list[EventRecord]:
    return service.list_events(project_id=project_id, task_id=task_id, limit=limit)

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from acp_core.schemas import AgentSessionCreate, AgentSessionFollowUpCreate, AgentSessionRead, SessionTailRead, SessionTimelineRead
from app.api.ws.events import broadcast_change
from app.bootstrap.dependencies import get_session_service

router = APIRouter(tags=["sessions"])


@router.get("/sessions", response_model=list[AgentSessionRead])
def list_sessions(
    project_id: str | None = Query(default=None),
    task_id: str | None = Query(default=None),
    service=Depends(get_session_service),
) -> list[AgentSessionRead]:
    return [
        AgentSessionRead.model_validate(item)
        for item in service.list_sessions(project_id=project_id, task_id=task_id)
    ]


@router.post("/sessions", response_model=AgentSessionRead, status_code=201)
def spawn_session(payload: AgentSessionCreate, request: Request, service=Depends(get_session_service)) -> AgentSessionRead:
    try:
        session = service.spawn_session(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = AgentSessionRead.model_validate(session)
    broadcast_change(
        request,
        event_type="session.spawned",
        entity_type="session",
        entity_id=response.id,
        project_id=response.project_id,
        task_id=response.task_id,
        session_id=response.id,
        detail={"profile": response.profile, "status": response.status},
    )
    return response


@router.post("/sessions/{session_id}/follow-up", response_model=AgentSessionRead, status_code=201)
def spawn_follow_up_session(
    session_id: str,
    payload: AgentSessionFollowUpCreate,
    request: Request,
    service=Depends(get_session_service),
) -> AgentSessionRead:
    try:
        session = service.spawn_follow_up_session(session_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = AgentSessionRead.model_validate(session)
    broadcast_change(
        request,
        event_type="session.follow_up_spawned",
        entity_type="session",
        entity_id=response.id,
        project_id=response.project_id,
        task_id=response.task_id,
        session_id=response.id,
        detail={"profile": response.profile, "status": response.status},
    )
    return response


@router.get("/sessions/{session_id}", response_model=AgentSessionRead)
def get_session(session_id: str, service=Depends(get_session_service)) -> AgentSessionRead:
    try:
        session = service.refresh_session_status(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AgentSessionRead.model_validate(session)


@router.get("/sessions/{session_id}/tail", response_model=SessionTailRead)
def tail_session(
    session_id: str,
    lines: int = Query(default=80, ge=1, le=400),
    service=Depends(get_session_service),
) -> SessionTailRead:
    try:
        return service.tail_session(session_id, lines=lines)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/timeline", response_model=SessionTimelineRead)
def session_timeline(session_id: str, service=Depends(get_session_service)) -> SessionTimelineRead:
    try:
        return service.get_session_timeline(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/cancel", response_model=AgentSessionRead)
def cancel_session(session_id: str, request: Request, service=Depends(get_session_service)) -> AgentSessionRead:
    try:
        session = service.cancel_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response = AgentSessionRead.model_validate(session)
    broadcast_change(
        request,
        event_type="session.cancelled",
        entity_type="session",
        entity_id=response.id,
        project_id=response.project_id,
        task_id=response.task_id,
        session_id=response.id,
        detail={"status": response.status},
    )
    return response

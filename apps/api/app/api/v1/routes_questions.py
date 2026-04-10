from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from acp_core.schemas import (
    HumanReplyCreate,
    WaitingQuestionCreate,
    WaitingQuestionDetail,
    WaitingQuestionRead,
)
from app.api.ws.events import broadcast_change
from app.bootstrap.dependencies import get_waiting_service

router = APIRouter(tags=["questions"])


@router.get("/questions", response_model=list[WaitingQuestionRead])
def list_questions(
    project_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service=Depends(get_waiting_service),
) -> list[WaitingQuestionRead]:
    return [
        WaitingQuestionRead.model_validate(item)
        for item in service.list_questions(project_id=project_id, status=status)
    ]


@router.post("/questions", response_model=WaitingQuestionRead, status_code=201)
def open_question(payload: WaitingQuestionCreate, request: Request, service=Depends(get_waiting_service)) -> WaitingQuestionRead:
    try:
        question = service.open_question(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = WaitingQuestionRead.model_validate(question)
    broadcast_change(
        request,
        event_type="waiting_question.opened",
        entity_type="waiting_question",
        entity_id=response.id,
        project_id=response.project_id,
        task_id=response.task_id,
        session_id=response.session_id,
        detail={"urgency": response.urgency, "status": response.status},
    )
    return response


@router.get("/questions/{question_id}", response_model=WaitingQuestionDetail)
def get_question(question_id: str, service=Depends(get_waiting_service)) -> WaitingQuestionDetail:
    try:
        return service.get_question_detail(question_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/questions/{question_id}/replies", response_model=WaitingQuestionDetail)
def answer_question(
    question_id: str,
    payload: HumanReplyCreate,
    request: Request,
    service=Depends(get_waiting_service),
) -> WaitingQuestionDetail:
    try:
        service.answer_question(question_id, payload)
        response = service.get_question_detail(question_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    broadcast_change(
        request,
        event_type="waiting_question.answered",
        entity_type="waiting_question",
        entity_id=response.id,
        project_id=response.project_id,
        task_id=response.task_id,
        session_id=response.session_id,
        detail={"status": response.status, "reply_count": len(response.replies)},
    )
    return response

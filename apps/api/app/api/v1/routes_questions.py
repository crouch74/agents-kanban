from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from acp_core.schemas import (
    HumanReplyCreate,
    WaitingQuestionCreate,
    WaitingQuestionDetail,
    WaitingQuestionRead,
)
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
def open_question(payload: WaitingQuestionCreate, service=Depends(get_waiting_service)) -> WaitingQuestionRead:
    try:
        question = service.open_question(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WaitingQuestionRead.model_validate(question)


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
    service=Depends(get_waiting_service),
) -> WaitingQuestionDetail:
    try:
        service.answer_question(question_id, payload)
        return service.get_question_detail(question_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

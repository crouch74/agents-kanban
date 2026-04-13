from __future__ import annotations

from typing import Any

from acp_core.enums import Urgency
from acp_core.schemas import WaitingQuestionCreate, WaitingQuestionRead
from acp_core.services.waiting_service import WaitingService

from acp_mcp_server.idempotency import (
    IDEMPOTENT_EVENT_TYPES,
    run_idempotent_write,
    run_read_operation,
)


def question_open(
    task_id: str,
    prompt: str,
    session_id: str | None = None,
    blocked_reason: str | None = None,
    urgency: str | Urgency | None = None,
    options_json: list[dict[str, Any]] | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["question_open"],
        client_request_id=client_request_id,
        write_fn=lambda context: WaitingService(context).open_question(
            WaitingQuestionCreate(
                task_id=task_id,
                session_id=session_id,
                prompt=prompt,
                blocked_reason=blocked_reason,
                urgency=urgency,
                options_json=options_json or [],
            )
        ),
        serialize_fn=lambda _context, question: WaitingQuestionRead.model_validate(
            question
        ).model_dump(),
    )


def question_answer_get(question_id: str) -> dict[str, Any]:
    return run_read_operation(
        lambda context: WaitingService(context)
        .get_question_detail(question_id)
        .model_dump()
    )


def question_resource(question_id: str) -> dict[str, Any]:
    return question_answer_get(question_id)

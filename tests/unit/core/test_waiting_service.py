from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from acp_core.models import AgentSession, Task, WaitingQuestion
from acp_core.schemas import HumanReplyCreate, WaitingQuestionCreate
from acp_core.services.base_service import ServiceContext
from acp_core.services.waiting_service import WaitingService


@pytest.fixture
def db_session_mock() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.get = MagicMock()
    db.scalar = MagicMock(return_value=None)
    db.scalars = MagicMock(return_value=[])
    return db


@pytest.fixture
def service_context(db_session_mock: MagicMock) -> ServiceContext:
    return ServiceContext(db=db_session_mock, actor_type="human", actor_name="tester")


def test_open_question_applies_waiting_overlay_to_task_and_session(service_context: ServiceContext) -> None:
    task = Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Need operator input",
        workflow_state="in_progress",
        priority="high",
        waiting_for_human=False,
        metadata_json={},
    )
    session = AgentSession(
        id="sess-1",
        project_id="proj-1",
        task_id=task.id,
        profile="executor",
        status="running",
        session_name="sess-name",
        runtime_metadata={"session_family_id": "sess-1"},
    )

    service_context.db.get.side_effect = lambda model, key: {
        (Task, task.id): task,
        (AgentSession, session.id): session,
    }.get((model, key))

    service = WaitingService(service_context, runtime=MagicMock())
    question = service.open_question(
        WaitingQuestionCreate(
            task_id=task.id,
            session_id=session.id,
            prompt="Which environment should I target?",
            urgency="high",
        )
    )

    assert isinstance(question, WaitingQuestion)
    assert task.waiting_for_human is True
    assert session.status == "waiting_human"
    assert service_context.db.add.call_count >= 2
    service_context.db.commit.assert_called_once()


@pytest.mark.parametrize(("session_exists", "expected_status"), [(True, "running"), (False, "failed")])
def test_answer_question_clears_waiting_overlay_and_refreshes_session_status(
    service_context: ServiceContext,
    session_exists: bool,
    expected_status: str,
) -> None:
    task = Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Need operator input",
        workflow_state="in_progress",
        priority="high",
        waiting_for_human=True,
        metadata_json={},
    )
    session = AgentSession(
        id="sess-1",
        project_id="proj-1",
        task_id=task.id,
        profile="executor",
        status="waiting_human",
        session_name="sess-name",
        runtime_metadata={"session_family_id": "sess-1"},
    )
    question = WaitingQuestion(
        id="q-1",
        project_id=task.project_id,
        task_id=task.id,
        session_id=session.id,
        status="open",
        prompt="Clarify priority",
    )

    service_context.db.get.side_effect = lambda model, key: {
        (Task, task.id): task,
        (AgentSession, session.id): session,
    }.get((model, key))

    runtime = MagicMock()
    runtime.session_exists.return_value = session_exists
    service = WaitingService(service_context, runtime=runtime)
    service.get_question = MagicMock(return_value=question)

    answered = service.answer_question(question.id, HumanReplyCreate(responder_name="Operator", body="Use staging."))

    assert answered.status == "closed"
    assert task.waiting_for_human is False
    assert session.status == expected_status
    service_context.db.commit.assert_called_once()


def test_answer_question_keeps_waiting_overlay_until_all_questions_close(service_context: ServiceContext) -> None:
    task = Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Need operator input",
        workflow_state="in_progress",
        priority="high",
        waiting_for_human=True,
        metadata_json={},
    )
    session = AgentSession(
        id="sess-1",
        project_id="proj-1",
        task_id=task.id,
        profile="executor",
        status="waiting_human",
        session_name="sess-name",
        runtime_metadata={"session_family_id": "sess-1"},
    )
    question = WaitingQuestion(
        id="q-1",
        project_id=task.project_id,
        task_id=task.id,
        session_id=session.id,
        status="open",
        prompt="Clarify priority",
    )

    service_context.db.get.side_effect = lambda model, key: {
        (Task, task.id): task,
        (AgentSession, session.id): session,
    }.get((model, key))
    service_context.db.scalar.side_effect = [1, 1]

    runtime = MagicMock()
    service = WaitingService(service_context, runtime=runtime)
    service.get_question = MagicMock(return_value=question)

    answered = service.answer_question(question.id, HumanReplyCreate(responder_name="Operator", body="Use staging."))

    assert answered.status == "closed"
    assert task.waiting_for_human is True
    assert session.status == "waiting_human"
    runtime.session_exists.assert_not_called()

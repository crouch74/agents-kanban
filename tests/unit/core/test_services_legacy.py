from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from acp_core.models import AgentSession, Task, WaitingQuestion
from acp_core.schemas import AgentSessionFollowUpCreate, HumanReplyCreate, TaskPatch, WaitingQuestionCreate
from acp_core.services_legacy import ProjectService, ServiceContext, SessionService, TaskService, WaitingService


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


@pytest.fixture
def task_record() -> Task:
    return Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Task",
        workflow_state="review",
        priority="medium",
        waiting_for_human=False,
        metadata_json={},
    )


@pytest.mark.parametrize(
    ("current_state", "next_state"),
    [
        ("backlog", "done"),
        ("ready", "review"),
        ("in_progress", "done"),
        ("cancelled", "ready"),
    ],
)
def test_patch_task_rejects_invalid_workflow_transitions(
    service_context: ServiceContext,
    task_record: Task,
    current_state: str,
    next_state: str,
) -> None:
    task_record.workflow_state = current_state
    service = TaskService(service_context)
    service.get_task = MagicMock(return_value=task_record)

    with pytest.raises(ValueError, match="Invalid workflow transition"):
        service.patch_task(task_record.id, TaskPatch(workflow_state=next_state))


@pytest.mark.parametrize(
    "missing_requirements",
    [
        ["attach at least one passing check or artifact"],
        ["resolve blocking dependencies"],
        ["close open waiting questions"],
    ],
)
def test_patch_task_enforces_completion_gating(
    service_context: ServiceContext,
    task_record: Task,
    missing_requirements: list[str],
) -> None:
    service = TaskService(service_context)
    service.get_task = MagicMock(return_value=task_record)
    service.get_completion_readiness = MagicMock(
        return_value=SimpleNamespace(can_mark_done=False, missing_requirements=missing_requirements)
    )

    with pytest.raises(ValueError, match="Task cannot move to done"):
        service.patch_task(task_record.id, TaskPatch(workflow_state="done"))


def test_get_board_view_excludes_cancelled_tasks(
    service_context: ServiceContext,
) -> None:
    board = SimpleNamespace(id="board-1", name="Board", columns=[])
    project = SimpleNamespace(id="proj-1", board=board)
    service = ProjectService(service_context)
    service.get_project = MagicMock(return_value=project)
    service._repair_board_columns = MagicMock()

    captured = {}

    def _capture(stmt):
        captured["stmt"] = stmt
        return []

    service_context.db.scalars.side_effect = _capture

    result = service.get_board_view("proj-1")

    assert result.tasks == []
    where_clause = captured["stmt"].whereclause
    assert isinstance(where_clause, BooleanClauseList)
    clauses = tuple(where_clause.clauses)
    assert any(
        isinstance(clause, BinaryExpression)
        and getattr(getattr(clause, "left", None), "name", None) == "workflow_state"
        and getattr(getattr(clause, "right", None), "value", None) == "cancelled"
        for clause in clauses
    )


def test_open_question_applies_waiting_overlay_to_task_and_session(
    service_context: ServiceContext,
) -> None:
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
    assert service_context.db.add.call_count >= 2  # question + session message
    service_context.db.commit.assert_called_once()


@pytest.mark.parametrize(
    ("session_exists", "expected_status"),
    [(True, "running"), (False, "failed")],
)
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

    answered = service.answer_question(
        question.id,
        HumanReplyCreate(responder_name="Operator", body="Use staging."),
    )

    assert answered.status == "closed"
    assert task.waiting_for_human is False
    assert session.status == expected_status
    service_context.db.commit.assert_called_once()


def test_answer_question_keeps_waiting_overlay_until_all_questions_close(
    service_context: ServiceContext,
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
    service_context.db.scalar.side_effect = [1, 1]

    runtime = MagicMock()
    service = WaitingService(service_context, runtime=runtime)
    service.get_question = MagicMock(return_value=question)

    answered = service.answer_question(
        question.id,
        HumanReplyCreate(responder_name="Operator", body="Use staging."),
    )

    assert answered.status == "closed"
    assert task.waiting_for_human is True
    assert session.status == "waiting_human"
    runtime.session_exists.assert_not_called()


def test_spawn_follow_up_session_keeps_session_lineage_and_sets_default_follow_up_type(
    service_context: ServiceContext,
) -> None:
    task = Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Review me",
        workflow_state="review",
        priority="medium",
        waiting_for_human=False,
        metadata_json={},
    )
    source = AgentSession(
        id="sess-source",
        project_id=task.project_id,
        task_id=task.id,
        repository_id="repo-1",
        worktree_id="wt-1",
        profile="executor",
        status="running",
        session_name="sess-source-name",
        runtime_metadata={"session_family_id": "family-1"},
    )
    spawned = AgentSession(
        id="sess-follow-up",
        project_id=task.project_id,
        task_id=task.id,
        repository_id="repo-1",
        worktree_id="wt-1",
        profile="reviewer",
        status="running",
        session_name="sess-review",
        runtime_metadata={},
    )

    service_context.db.get.side_effect = lambda model, key: {
        (Task, task.id): task,
    }.get((model, key))

    service = SessionService(service_context, runtime=MagicMock())
    service.get_session = MagicMock(return_value=source)
    service._spawn_session_record = MagicMock(return_value=spawned)

    payload = AgentSessionFollowUpCreate(profile="reviewer", follow_up_type=None)
    result = service.spawn_follow_up_session(source.id, payload)

    assert result is spawned
    service._spawn_session_record.assert_called_once()
    kwargs = service._spawn_session_record.call_args.kwargs
    assert kwargs["repository_id"] == "repo-1"
    assert kwargs["worktree_id"] == "wt-1"
    assert kwargs["runtime_metadata_extra"]["session_family_id"] == "family-1"
    assert kwargs["runtime_metadata_extra"]["follow_up_of_session_id"] == source.id
    assert kwargs["runtime_metadata_extra"]["follow_up_type"] == "review"
    service_context.db.commit.assert_called_once()


@pytest.mark.parametrize(
    "reuse_flags",
    [(False, True), (True, False), (False, False)],
)
def test_spawn_follow_up_session_respects_reuse_policy_flags(
    service_context: ServiceContext,
    reuse_flags: tuple[bool, bool],
) -> None:
    reuse_worktree, reuse_repository = reuse_flags
    task = Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Review me",
        workflow_state="review",
        priority="medium",
        waiting_for_human=False,
        metadata_json={},
    )
    source = AgentSession(
        id="sess-source",
        project_id=task.project_id,
        task_id=task.id,
        repository_id="repo-1",
        worktree_id="wt-1",
        profile="executor",
        status="running",
        session_name="sess-source-name",
        runtime_metadata={"session_family_id": "family-1"},
    )
    spawned = AgentSession(
        id="sess-follow-up",
        project_id=task.project_id,
        task_id=task.id,
        profile="verifier",
        status="running",
        session_name="sess-verify",
        runtime_metadata={},
    )

    service_context.db.get.side_effect = lambda model, key: {(Task, task.id): task}.get((model, key))

    service = SessionService(service_context, runtime=MagicMock())
    service.get_session = MagicMock(return_value=source)
    service._spawn_session_record = MagicMock(return_value=spawned)

    service.spawn_follow_up_session(
        source.id,
        AgentSessionFollowUpCreate(
            profile="verifier",
            follow_up_type="verify",
            reuse_worktree=reuse_worktree,
            reuse_repository=reuse_repository,
        ),
    )

    kwargs = service._spawn_session_record.call_args.kwargs
    assert kwargs["repository_id"] == ("repo-1" if reuse_repository else None)
    assert kwargs["worktree_id"] == ("wt-1" if reuse_worktree else None)

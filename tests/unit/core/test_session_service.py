from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from acp_core.models import AgentSession, Task
from acp_core.schemas import AgentSessionFollowUpCreate
from acp_core.services.base_service import ServiceContext
from acp_core.services.session_service import SessionService
from acp_core.settings import settings


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

    service_context.db.get.side_effect = lambda model, key: {(Task, task.id): task}.get(
        (model, key)
    )

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
    assert kwargs["launch_inputs"].agent_name == "codex"
    service_context.db.commit.assert_called_once()


@pytest.mark.parametrize("reuse_flags", [(False, True), (True, False), (False, False)])
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

    service_context.db.get.side_effect = lambda model, key: {(Task, task.id): task}.get(
        (model, key)
    )

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


def test_spawn_follow_up_session_uses_flow_specific_agent_defaults(
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
        profile="verifier",
        status="running",
        session_name="sess-verify",
        runtime_metadata={},
    )

    service_context.db.get.side_effect = lambda model, key: {(Task, task.id): task}.get(
        (model, key)
    )

    original_default_agent = settings.default_agent
    original_review_agent = settings.review_agent
    original_verify_agent = settings.verify_agent
    settings.default_agent = "aider"
    settings.review_agent = "claude-code"
    settings.verify_agent = "codex"
    try:
        service = SessionService(service_context, runtime=MagicMock())
        service.get_session = MagicMock(return_value=source)
        service._spawn_session_record = MagicMock(return_value=spawned)

        service.spawn_follow_up_session(
            source.id,
            AgentSessionFollowUpCreate(profile="reviewer", follow_up_type="review"),
        )
        review_kwargs = service._spawn_session_record.call_args.kwargs
        assert review_kwargs["launch_inputs"].agent_name == "claude_code"

        service.spawn_follow_up_session(
            source.id,
            AgentSessionFollowUpCreate(profile="verifier", follow_up_type="verify"),
        )
        verify_kwargs = service._spawn_session_record.call_args.kwargs
        assert verify_kwargs["launch_inputs"].agent_name == "codex"
    finally:
        settings.default_agent = original_default_agent
        settings.review_agent = original_review_agent
        settings.verify_agent = original_verify_agent

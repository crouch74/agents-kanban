from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acp_core.agents.types import SessionLaunchInputs
from acp_core.models import AgentSession, Repository, Task, Worktree
from acp_core.runtime import RuntimeLaunchSpec
from acp_core.schemas import AgentSessionFollowUpCreate, SessionLaunchInputCreate
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


def _follow_up_get_side_effect(task: Task):
    source_repository = Repository(
        id="repo-1",
        project_id=task.project_id,
        name="test-repo",
        local_path="/tmp/repo",
    )
    source_worktree = Worktree(
        id="wt-1",
        repository_id=source_repository.id,
        task_id=task.id,
        branch_name="test",
        path="/tmp/work",
    )

    def _side_effect(model: type[object], key: str) -> object | None:
        return {
            (Task, task.id): task,
            (Repository, source_repository.id): source_repository,
            (Worktree, source_worktree.id): source_worktree,
        }.get((model, key))

    return _side_effect


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

    service_context.db.get.side_effect = _follow_up_get_side_effect(task)

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


def test_spawn_follow_up_session_prefers_top_level_agent_override(
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

    service_context.db.get.side_effect = _follow_up_get_side_effect(task)

    service = SessionService(service_context, runtime=MagicMock())
    service.get_session = MagicMock(return_value=source)
    service._spawn_session_record = MagicMock(return_value=spawned)

    service.spawn_follow_up_session(
        source.id,
        AgentSessionFollowUpCreate(
            profile="reviewer",
            follow_up_type=None,
            agent_name="aider",
            launch_input=SessionLaunchInputCreate(agent_name="codex"),
        ),
    )

    kwargs = service._spawn_session_record.call_args.kwargs
    assert kwargs["launch_inputs"].agent_name == "aider"


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

    service_context.db.get.side_effect = _follow_up_get_side_effect(task)

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

    service_context.db.get.side_effect = _follow_up_get_side_effect(task)

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


def test_spawn_session_record_includes_agent_details_in_session_and_run_metadata(
    service_context: ServiceContext,
) -> None:
    task = Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Implement feature",
        workflow_state="in_progress",
        priority="medium",
        waiting_for_human=False,
        metadata_json={},
    )
    runtime = MagicMock()
    runtime.spawn_session.return_value = SimpleNamespace(
        session_name="sess-1",
        pane_id="%1",
        window_name="main",
        working_directory="/tmp/work",
        command="env ACP_RUNTIME_HOME=/runtime codex exec -",
    )

    service = SessionService(service_context, runtime=runtime)
    service._resolve_session_target = MagicMock(return_value=(None, None, Path("/tmp/work")))
    service._next_attempt_number = MagicMock(return_value=1)

    launch_inputs = SessionLaunchInputs(
        task_kind="execute",
        agent_name="codex",
        prompt="Plan work",
        working_directory=Path("/tmp/work"),
    )
    launch_spec = RuntimeLaunchSpec(
        argv=["codex", "exec", "-"],
        env={"ACP_RUNTIME_HOME": "/runtime"},
        display_command="codex exec - < prompt.md",
        working_directory="/tmp/work",
        adapter_metadata={"agent": "codex"},
    )

    service._spawn_session_record(
        task=task,
        profile="executor",
        launch_spec=launch_spec,
        launch_inputs=launch_inputs,
    )

    session = service_context.db.add.call_args_list[0].args[0]
    run = service_context.db.add.call_args_list[1].args[0]
    assert session.runtime_metadata["agent_name"] == "codex"
    assert session.runtime_metadata["launch_argv"] == ["codex", "exec", "-"]
    assert session.runtime_metadata["adapter_metadata"] == {"agent": "codex"}
    assert run.runtime_metadata["agent_name"] == "codex"
    assert run.runtime_metadata["launch_inputs"]["task_kind"] == "execute"


@pytest.mark.parametrize(
    ("profile", "follow_up_type"),
    [("executor", "retry"), ("reviewer", "review"), ("verifier", "verify")],
)
def test_spawn_follow_up_session_preserves_family_lineage_across_flow_types(
    service_context: ServiceContext,
    profile: str,
    follow_up_type: str,
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
        profile=profile,
        status="running",
        session_name=f"sess-{follow_up_type}",
        runtime_metadata={},
    )

    service_context.db.get.side_effect = _follow_up_get_side_effect(task)

    service = SessionService(service_context, runtime=MagicMock())
    service.get_session = MagicMock(return_value=source)
    service._spawn_session_record = MagicMock(return_value=spawned)

    service.spawn_follow_up_session(
        source.id,
        AgentSessionFollowUpCreate(profile=profile, follow_up_type=None),
    )

    kwargs = service._spawn_session_record.call_args.kwargs
    assert kwargs["runtime_metadata_extra"]["session_family_id"] == "family-1"
    assert kwargs["runtime_metadata_extra"]["follow_up_of_session_id"] == "sess-source"
    assert kwargs["runtime_metadata_extra"]["follow_up_type"] == follow_up_type


def test_refresh_session_status_auto_completes_kickoff_task(
    service_context: ServiceContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Kickoff",
        workflow_state="in_progress",
        priority="medium",
        waiting_for_human=False,
        metadata_json={},
    )
    session = AgentSession(
        id="sess-1",
        project_id=task.project_id,
        task_id=task.id,
        profile="executor",
        status="running",
        session_name="sess-1-name",
        runtime_metadata={"task_kind": "kickoff"},
    )

    service_context.db.get.side_effect = (
        lambda model, key: task if model is Task and key == task.id else None
    )
    runtime = MagicMock()
    runtime.session_exists.return_value = False

    completed_payloads: list[object] = []

    class FakeTaskService:
        def __init__(self, context: ServiceContext) -> None:
            self.context = context

        def patch_task(self, task_id: str, payload):
            completed_payloads.append(payload)
            task.workflow_state = payload.workflow_state
            return task

    monkeypatch.setattr("acp_core.services.task_service.TaskService", FakeTaskService)

    service = SessionService(service_context, runtime=runtime)
    service.get_session = MagicMock(return_value=session)

    refreshed = service.refresh_session_status(session.id)

    assert refreshed.status == "done"
    assert completed_payloads
    assert completed_payloads[0].workflow_state == "done"
    assert task.workflow_state == "done"

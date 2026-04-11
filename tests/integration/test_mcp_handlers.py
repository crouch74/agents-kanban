from __future__ import annotations

from pathlib import Path

from acp_mcp_server import handlers
from acp_core.runtime import RuntimeSessionInfo
from git import Repo


class FakeRuntime:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, str]] = {}

    def spawn_session(self, *, session_name: str, working_directory: Path, profile: str, command: str | None = None):
        self.sessions[session_name] = {
            "working_directory": str(working_directory),
            "command": command or profile,
        }
        return RuntimeSessionInfo(
            session_name=session_name,
            pane_id="%2",
            window_name="main",
            working_directory=str(working_directory),
            command=command or profile,
        )

    def session_exists(self, session_name: str) -> bool:
        return session_name in self.sessions

    def capture_tail(self, session_name: str, *, lines: int = 120) -> str:
        return f"session={session_name}\nlines={lines}"

    def terminate_session(self, session_name: str) -> None:
        self.sessions.pop(session_name, None)

    def list_sessions(self, *, prefix: str | None = None):
        names = sorted(self.sessions)
        if prefix is not None:
            names = [name for name in names if name.startswith(prefix)]
        return [
            type("RuntimeSessionSummary", (), {"session_name": name, "window_name": "main"})()
            for name in names
        ]


def _assert_snapshot_keys(payload: dict[str, object], expected_keys: tuple[str, ...]) -> None:
    assert tuple(payload.keys()) == expected_keys


def test_mcp_handlers_expose_core_control_plane_workflows(monkeypatch, tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    original_session_service = handlers.SessionService
    original_bootstrap_service = handlers.BootstrapService
    monkeypatch.setattr(
        handlers,
        "SessionService",
        lambda context: original_session_service(context, runtime=fake_runtime),
    )
    monkeypatch.setattr(
        handlers,
        "BootstrapService",
        lambda context: original_bootstrap_service(context, runtime=fake_runtime),
    )

    project = handlers.project_create("MCP Ops", "Agent-facing surface", client_request_id="project-1")
    project_id = project["id"]
    project_replayed = handlers.project_create("MCP Ops", "Agent-facing surface", client_request_id="project-1")
    assert project_replayed["id"] == project_id

    repo_path = tmp_path / "mcp-bootstrap"
    repo_path.mkdir()
    repo = Repo.init(repo_path)
    repo.git.config("user.name", "ACP Test")
    repo.git.config("user.email", "acp@example.test")
    (repo_path / "README.md").write_text("# mcp bootstrap\n", encoding="utf-8")
    repo.git.add("--all")
    repo.index.commit("init")
    bootstrap = handlers.project_bootstrap(
        name="Bootstrap MCP Ops",
        repo_path=str(repo_path.resolve()),
        stack_preset="python-package",
        initial_prompt="Plan the first project tasks.",
        client_request_id="bootstrap-1",
    )
    assert bootstrap["kickoff_session"]["status"] == "running"
    bootstrap_replayed = handlers.project_bootstrap(
        name="Bootstrap MCP Ops",
        repo_path=str(repo_path.resolve()),
        stack_preset="python-package",
        initial_prompt="Plan the first project tasks.",
        client_request_id="bootstrap-1",
    )
    assert bootstrap_replayed["project"]["id"] == bootstrap["project"]["id"]

    board = handlers.board_get(project_id)
    assert board["project_id"] == project_id

    task = handlers.task_create(project_id=project_id, title="Ship MCP tools", client_request_id="task-1")
    task_id = task["id"]
    _assert_snapshot_keys(
        task,
        (
            "id",
            "project_id",
            "board_column_id",
            "parent_task_id",
            "title",
            "description",
            "workflow_state",
            "priority",
            "tags",
            "blocked_reason",
            "waiting_for_human",
            "created_at",
            "updated_at",
        ),
    )
    task_replayed = handlers.task_create(project_id=project_id, title="Ship MCP tools", client_request_id="task-1")
    assert task_replayed == task

    task_updated = handlers.task_update(
        task_id=task_id,
        description="End-to-end handler flow",
        waiting_for_human=True,
        client_request_id="task-update-1",
    )
    _assert_snapshot_keys(task_updated, tuple(task.keys()))
    task_updated_replayed = handlers.task_update(
        task_id=task_id,
        description="End-to-end handler flow",
        waiting_for_human=True,
        client_request_id="task-update-1",
    )
    assert task_updated_replayed == task_updated

    comment = handlers.task_comment_add(
        task_id=task_id,
        author_name="agent",
        body="starting work",
        client_request_id="comment-1",
    )
    _assert_snapshot_keys(
        comment,
        ("id", "task_id", "author_type", "author_name", "body", "metadata_json", "created_at"),
    )
    assert comment["task_id"] == task_id
    comment_replayed = handlers.task_comment_add(
        task_id=task_id,
        author_name="agent",
        body="starting work",
        client_request_id="comment-1",
    )
    assert comment_replayed == comment

    check = handlers.task_check_add(
        task_id=task_id,
        check_type="self_check",
        status="passed",
        summary="looks good",
        client_request_id="check-1",
    )
    assert check["status"] == "passed"
    check_replayed = handlers.task_check_add(
        task_id=task_id,
        check_type="self_check",
        status="passed",
        summary="looks good",
        client_request_id="check-1",
    )
    assert check_replayed["id"] == check["id"]

    artifact = handlers.task_artifact_add(
        task_id=task_id,
        artifact_type="diff",
        name="Patch diff",
        uri="git:diff:HEAD~1..HEAD",
        client_request_id="artifact-1",
    )
    assert artifact["task_id"] == task_id
    artifact_replayed = handlers.task_artifact_add(
        task_id=task_id,
        artifact_type="diff",
        name="Patch diff",
        uri="git:diff:HEAD~1..HEAD",
        client_request_id="artifact-1",
    )
    assert artifact_replayed["id"] == artifact["id"]

    blocker = handlers.task_create(project_id=project_id, title="Unblock dependency", client_request_id="task-2")
    dependency = handlers.task_dependency_add(
        task_id=task_id,
        depends_on_task_id=blocker["id"],
        client_request_id="dependency-1",
    )
    assert dependency["task_id"] == task_id
    dependency_replayed = handlers.task_dependency_add(
        task_id=task_id,
        depends_on_task_id=blocker["id"],
        client_request_id="dependency-1",
    )
    assert dependency_replayed["id"] == dependency["id"]

    question = handlers.question_open(
        task_id=task_id,
        prompt="Need a final confirmation?",
        urgency="medium",
        client_request_id="question-1",
    )
    assert question["task_id"] == task_id
    question_replayed = handlers.question_open(
        task_id=task_id,
        prompt="Need a final confirmation?",
        urgency="medium",
        client_request_id="question-1",
    )
    assert question_replayed["id"] == question["id"]

    question_detail = handlers.question_answer_get(question["id"])
    assert question_detail["prompt"] == "Need a final confirmation?"

    search = handlers.context_search("confirmation", project_id=project_id)
    assert search["hits"]
    assert any(hit["entity_type"] == "waiting_question" for hit in search["hits"])

    completion = handlers.task_completion_readiness(task_id)
    assert completion["can_mark_done"] is False
    assert completion["blocking_dependency_count"] == 1
    assert completion["artifact_count"] >= 1
    assert completion["open_waiting_question_count"] == 1

    session = handlers.session_spawn(task_id=task_id, profile="executor", client_request_id="session-1")
    _assert_snapshot_keys(
        session,
        (
            "id",
            "project_id",
            "task_id",
            "repository_id",
            "worktree_id",
            "profile",
            "status",
            "session_name",
            "runtime_metadata",
            "created_at",
            "updated_at",
        ),
    )
    assert session["task_id"] == task_id
    session_replayed = handlers.session_spawn(task_id=task_id, profile="executor", client_request_id="session-1")
    assert session_replayed == session

    worktree = handlers.worktree_create(
        repository_id=bootstrap["repository"]["id"],
        task_id=task_id,
        label="handler-test",
        client_request_id="worktree-1",
    )
    _assert_snapshot_keys(
        worktree,
        (
            "id",
            "repository_id",
            "task_id",
            "session_id",
            "branch_name",
            "path",
            "status",
            "lock_reason",
            "metadata_json",
            "created_at",
            "updated_at",
        ),
    )
    worktree_replayed = handlers.worktree_create(
        repository_id=bootstrap["repository"]["id"],
        task_id=task_id,
        label="handler-test",
        client_request_id="worktree-1",
    )
    assert worktree_replayed == worktree

    follow_up = handlers.session_follow_up(
        session["id"],
        profile="verifier",
        follow_up_type="verify",
        client_request_id="follow-up-1",
    )
    assert follow_up["runtime_metadata"]["follow_up_of_session_id"] == session["id"]
    follow_up_replayed = handlers.session_follow_up(
        session["id"],
        profile="verifier",
        follow_up_type="verify",
        client_request_id="follow-up-1",
    )
    assert follow_up_replayed["id"] == follow_up["id"]

    diagnostics = handlers.diagnostics_get()
    assert "stale_worktree_count" in diagnostics
    assert "orphan_runtime_session_count" in diagnostics

    events = handlers.recent_events_resource(task_id=task_id)
    assert events
    assert any(event["event_type"] == "task.created" for event in events)

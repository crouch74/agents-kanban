from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from git import Repo

from app.bootstrap.dependencies import get_runtime_adapter
from app.main import app
from acp_core.settings import settings
from acp_core.runtime import RuntimeSessionInfo


class FakeRuntime:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, str]] = {}

    def spawn_session(
        self,
        *,
        session_name: str,
        working_directory: Path,
        profile: str,
        launch_spec=None,
        command: str | None = None,
    ):
        self.sessions[session_name] = {
            "working_directory": str(working_directory),
            "command": launch_spec.display_command
            if launch_spec
            else (command or profile),
        }
        return RuntimeSessionInfo(
            session_name=session_name,
            pane_id="%1",
            window_name="main",
            working_directory=str(launch_spec.working_directory)
            if launch_spec
            else str(working_directory),
            command=launch_spec.display_command
            if launch_spec
            else (command or profile),
        )

    def session_exists(self, session_name: str) -> bool:
        return session_name in self.sessions

    def is_session_active(self, session_name: str) -> bool:
        return session_name in self.sessions

    def capture_tail(self, session_name: str, *, lines: int = 120) -> str:
        return "\n".join(
            [
                "🤖 Session booted",
                f"session={session_name}",
                f"lines={lines}",
            ]
        )

    def terminate_session(self, session_name: str) -> None:
        self.sessions.pop(session_name, None)

    def list_sessions(self, *, prefix: str | None = None):
        names = sorted(self.sessions)
        if prefix is not None:
            names = [name for name in names if name.startswith(prefix)]
        return [
            type(
                "RuntimeSessionSummary",
                (),
                {"session_name": name, "window_name": "main"},
            )()
            for name in names
        ]


class FailingRuntime(FakeRuntime):
    def spawn_session(
        self,
        *,
        session_name: str,
        working_directory: Path,
        profile: str,
        launch_spec=None,
        command: str | None = None,
    ):
        raise RuntimeError("runtime down")


def create_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.name", "ACP Test")
    repo.git.config("user.email", "acp@example.test")
    (path / "README.md").write_text("# temp repo\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("init")
    return path


def test_session_write_routes_reject_malformed_payloads_and_missing_foreign_keys() -> (
    None
):
    with TestClient(app) as client:
        malformed_spawn = client.post("/api/v1/sessions", json={"profile": "executor"})
        assert malformed_spawn.status_code == 422
        assert malformed_spawn.json()["detail"][0]["loc"] == ["body", "task_id"]

        missing_fk_spawn = client.post(
            "/api/v1/sessions",
            json={"task_id": "task-missing", "profile": "executor"},
        )
        assert missing_fk_spawn.status_code == 400
        assert missing_fk_spawn.json() == {"detail": "Task not found"}

        malformed_follow_up = client.post(
            "/api/v1/sessions/session-missing/follow-up",
            json={"profile": "invalid"},
        )
        assert malformed_follow_up.status_code == 422
        assert malformed_follow_up.json()["detail"][0]["loc"] == ["body", "profile"]


def test_spawn_session_and_tail_runtime(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime

    repo_path = create_git_repo(tmp_path / "session-repo")

    try:
        with TestClient(app) as client:
            project_id = client.post(
                "/api/v1/projects", json={"name": "Runtime Ops"}
            ).json()["id"]
            repository_id = client.post(
                "/api/v1/repositories",
                json={"project_id": project_id, "local_path": str(repo_path)},
            ).json()["id"]
            task_id = client.post(
                "/api/v1/tasks",
                json={
                    "project_id": project_id,
                    "title": "Run executor",
                    "board_column_key": "ready",
                },
            ).json()["id"]
            worktree_id = client.post(
                "/api/v1/worktrees",
                json={"repository_id": repository_id, "task_id": task_id},
            ).json()["id"]

            session_response = client.post(
                "/api/v1/sessions",
                json={
                    "task_id": task_id,
                    "profile": "executor",
                    "worktree_id": worktree_id,
                    "launch_input": {
                        "task_kind": "execute",
                        "agent_name": "codex",
                        "prompt": "Implement the task and summarize changes.",
                        "permission_mode": "danger-full-access",
                        "output_mode": "json",
                        "max_turns": 3,
                        "allowed_tools": ["bash"],
                        "disallowed_tools": ["python"],
                        "extra_env": {"ACP_SESSION_MODE": "test"},
                    },
                },
            )
            assert session_response.status_code == 201
            session = session_response.json()
            assert session["status"] == "running"
            assert session["worktree_id"] == worktree_id
            assert (
                session["runtime_metadata"]["launch_inputs"]["task_kind"] == "execute"
            )
            assert session["runtime_metadata"]["launch_inputs"]["agent_name"] == "codex"
            assert session["runtime_metadata"]["launch_inputs"]["max_turns"] == 3
            assert session["runtime_metadata"]["agent_name"] == "codex"
            assert session["runtime_metadata"]["task_kind"] == "execute"
            assert (
                session["runtime_metadata"]["permission_mode"] == "danger-full-access"
            )
            assert session["runtime_metadata"]["output_mode"] == "json"
            assert session["runtime_metadata"]["model"] is None
            assert session["runtime_metadata"]["launch_argv"][0] == "codex"
            assert session["runtime_metadata"]["display_command"].startswith("codex ")
            assert session["runtime_metadata"]["resume_token"] is None
            assert session["runtime_metadata"]["resume_token_hint"]
            assert session["runtime_metadata"]["adapter_metadata"]["agent"] == "codex"
            assert (
                session["runtime_metadata"]["working_directory_source"]
                == session["runtime_metadata"]["working_directory"]
            )

            list_response = client.get(f"/api/v1/sessions?project_id={project_id}")
            assert list_response.status_code == 200
            assert len(list_response.json()) == 1

            tail_response = client.get(f"/api/v1/sessions/{session['id']}/tail")
            assert tail_response.status_code == 200
            payload = tail_response.json()
            assert "Session booted" in "\n".join(payload["lines"])
            assert payload["session"]["session_name"] == session["session_name"]

            timeline_response = client.get(f"/api/v1/sessions/{session['id']}/timeline")
            assert timeline_response.status_code == 200
            timeline = timeline_response.json()
            assert timeline["session"]["id"] == session["id"]
            assert timeline["runs"][0]["status"] == "running"
            assert (
                timeline["runs"][0]["runtime_metadata"]["agent_name"]
                == session["runtime_metadata"]["agent_name"]
            )
            assert (
                timeline["runs"][0]["runtime_metadata"]["launch_argv"]
                == session["runtime_metadata"]["launch_argv"]
            )
            assert (
                timeline["runs"][0]["runtime_metadata"]["adapter_metadata"]
                == session["runtime_metadata"]["adapter_metadata"]
            )
            assert timeline["messages"]
            assert any(
                event["event_type"] == "session.spawned" for event in timeline["events"]
            )
            assert len(timeline["related_sessions"]) == 1

            follow_up_response = client.post(
                f"/api/v1/sessions/{session['id']}/follow-up",
                json={"profile": "verifier", "follow_up_type": "verify"},
            )
            assert follow_up_response.status_code == 201
            follow_up = follow_up_response.json()
            assert follow_up["task_id"] == task_id
            assert follow_up["worktree_id"] == worktree_id
            assert (
                follow_up["runtime_metadata"]["follow_up_of_session_id"]
                == session["id"]
            )
            assert follow_up["runtime_metadata"]["follow_up_type"] == "verify"
            assert follow_up["runtime_metadata"]["agent_name"] == "codex"
            assert follow_up["runtime_metadata"]["task_kind"] == "verify"

            follow_up_timeline_response = client.get(
                f"/api/v1/sessions/{follow_up['id']}/timeline"
            )
            assert follow_up_timeline_response.status_code == 200
            follow_up_timeline = follow_up_timeline_response.json()
            assert len(follow_up_timeline["related_sessions"]) == 2
            assert any(
                item["id"] == session["id"]
                for item in follow_up_timeline["related_sessions"]
            )
            assert any(
                event["event_type"] == "session.follow_up_spawned"
                for event in follow_up_timeline["events"]
            )

            cancel_response = client.post(f"/api/v1/sessions/{session['id']}/cancel")
            assert cancel_response.status_code == 200
            cancelled = cancel_response.json()
            assert cancelled["status"] == "cancelled"

            refreshed_response = client.get(f"/api/v1/sessions/{session['id']}")
            assert refreshed_response.status_code == 200
            assert refreshed_response.json()["status"] == "cancelled"

            follow_up_cancel_response = client.post(
                f"/api/v1/sessions/{follow_up['id']}/cancel"
            )
            assert follow_up_cancel_response.status_code == 200
            assert follow_up_cancel_response.json()["status"] == "cancelled"

            diagnostics_response = client.get("/api/v1/diagnostics")
            assert diagnostics_response.status_code == 200
            diagnostics = diagnostics_response.json()
            assert diagnostics["stale_worktree_count"] >= 1
            assert any(
                issue["worktree_id"] == worktree_id
                and issue["recommendation"] == "archive"
                for issue in diagnostics["stale_worktrees"]
            )
    finally:
        app.dependency_overrides.clear()


def test_session_spawn_and_follow_up_surface_runtime_adapter_failure(
    tmp_path: Path,
) -> None:
    app.dependency_overrides[get_runtime_adapter] = lambda: FailingRuntime()
    repo_path = create_git_repo(tmp_path / "session-runtime-failure-repo")

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            project_id = client.post(
                "/api/v1/projects", json={"name": "Session Runtime Failure"}
            ).json()["id"]
            repository_id = client.post(
                "/api/v1/repositories",
                json={"project_id": project_id, "local_path": str(repo_path)},
            ).json()["id"]
            task_id = client.post(
                "/api/v1/tasks",
                json={"project_id": project_id, "title": "Runtime fail task"},
            ).json()["id"]

            spawn_response = client.post(
                "/api/v1/sessions",
                json={
                    "task_id": task_id,
                    "profile": "executor",
                    "repository_id": repository_id,
                },
            )
            assert spawn_response.status_code == 502
            payload = spawn_response.json()
            assert payload["error"]["code"] == "runtime_adapter_failure"
            assert payload["error"]["details"]["operation"] == "session_spawn"
    finally:
        app.dependency_overrides.clear()


def test_session_spawn_rejects_cross_project_repository(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "cross-project-session-repo")

    try:
        with TestClient(app) as client:
            project_a = client.post(
                "/api/v1/projects", json={"name": "Project A"}
            ).json()["id"]
            project_b = client.post(
                "/api/v1/projects", json={"name": "Project B"}
            ).json()["id"]
            repository_id = client.post(
                "/api/v1/repositories",
                json={"project_id": project_a, "local_path": str(repo_path)},
            ).json()["id"]
            task_id = client.post(
                "/api/v1/tasks",
                json={"project_id": project_b, "title": "Cross-project task"},
            ).json()["id"]

            response = client.post(
                "/api/v1/sessions",
                json={
                    "task_id": task_id,
                    "profile": "executor",
                    "repository_id": repository_id,
                },
            )
            assert response.status_code == 400
            assert (
                response.json()["detail"]
                == "Session repository must belong to the same project as the task"
            )
    finally:
        app.dependency_overrides.clear()


def test_session_spawn_validates_agent_capabilities(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "capability-session-repo")

    try:
        with TestClient(app) as client:
            project_id = client.post(
                "/api/v1/projects", json={"name": "Capability Project"}
            ).json()["id"]
            repository_id = client.post(
                "/api/v1/repositories",
                json={"project_id": project_id, "local_path": str(repo_path)},
            ).json()["id"]
            task_id = client.post(
                "/api/v1/tasks",
                json={"project_id": project_id, "title": "Capability task"},
            ).json()["id"]

            response = client.post(
                "/api/v1/sessions",
                json={
                    "task_id": task_id,
                    "profile": "executor",
                    "repository_id": repository_id,
                    "launch_input": {
                        "task_kind": "execute",
                        "agent_name": "claude-code",
                        "prompt": "Run review.",
                        "permission_mode": "danger-full-access",
                    },
                },
            )
            assert response.status_code == 400
            assert (
                response.json()["detail"]
                == "Agent 'claude_code' does not support permission_mode='danger-full-access'. Supported values: none"
            )
    finally:
        app.dependency_overrides.clear()


def test_follow_up_session_uses_default_agent_when_no_override(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "session-followup-default-agent")

    original_verify_agent = settings.verify_agent
    original_default_agent = settings.default_agent
    try:
        settings.verify_agent = None
        settings.default_agent = "codex"

        with TestClient(app) as client:
            project_id = client.post(
                "/api/v1/projects", json={"name": "Follow-up Defaults"}
            ).json()["id"]
            repository_id = client.post(
                "/api/v1/repositories",
                json={"project_id": project_id, "local_path": str(repo_path)},
            ).json()["id"]
            task_id = client.post(
                "/api/v1/tasks",
                json={
                    "project_id": project_id,
                    "title": "Run follow-up default test",
                },
            ).json()["id"]

            session_response = client.post(
                "/api/v1/sessions",
                json={
                    "task_id": task_id,
                    "profile": "executor",
                    "repository_id": repository_id,
                },
            )
            assert session_response.status_code == 201
            session = session_response.json()

            follow_up_response = client.post(
                f"/api/v1/sessions/{session['id']}/follow-up",
                json={"profile": "verifier", "follow_up_type": "verify"},
            )
            assert follow_up_response.status_code == 201
            follow_up = follow_up_response.json()

            assert follow_up["runtime_metadata"]["agent_name"] == "codex"
            assert follow_up["runtime_metadata"]["task_kind"] == "verify"
            assert follow_up["runtime_metadata"]["follow_up_of_session_id"] == session["id"]
    finally:
        settings.verify_agent = original_verify_agent
        settings.default_agent = original_default_agent
        app.dependency_overrides.clear()

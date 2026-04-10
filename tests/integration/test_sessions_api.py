from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from git import Repo

from app.bootstrap.dependencies import get_runtime_adapter
from app.main import app
from acp_core.runtime import RuntimeSessionInfo


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
            pane_id="%1",
            window_name="main",
            working_directory=str(working_directory),
            command=command or profile,
        )

    def session_exists(self, session_name: str) -> bool:
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
            type("RuntimeSessionSummary", (), {"session_name": name, "window_name": "main"})()
            for name in names
        ]


def create_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.name", "ACP Test")
    repo.git.config("user.email", "acp@example.test")
    (path / "README.md").write_text("# temp repo\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("init")
    return path


def test_spawn_session_and_tail_runtime(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime

    repo_path = create_git_repo(tmp_path / "session-repo")

    try:
        with TestClient(app) as client:
            project_id = client.post("/api/v1/projects", json={"name": "Runtime Ops"}).json()["id"]
            repository_id = client.post(
                "/api/v1/repositories",
                json={"project_id": project_id, "local_path": str(repo_path)},
            ).json()["id"]
            task_id = client.post(
                "/api/v1/tasks",
                json={"project_id": project_id, "title": "Run executor", "board_column_key": "ready"},
            ).json()["id"]
            worktree_id = client.post(
                "/api/v1/worktrees",
                json={"repository_id": repository_id, "task_id": task_id},
            ).json()["id"]

            session_response = client.post(
                "/api/v1/sessions",
                json={"task_id": task_id, "profile": "executor", "worktree_id": worktree_id},
            )
            assert session_response.status_code == 201
            session = session_response.json()
            assert session["status"] == "running"
            assert session["worktree_id"] == worktree_id

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
            assert timeline["messages"]
            assert any(event["event_type"] == "session.spawned" for event in timeline["events"])

            cancel_response = client.post(f"/api/v1/sessions/{session['id']}/cancel")
            assert cancel_response.status_code == 200
            cancelled = cancel_response.json()
            assert cancelled["status"] == "cancelled"

            refreshed_response = client.get(f"/api/v1/sessions/{session['id']}")
            assert refreshed_response.status_code == 200
            assert refreshed_response.json()["status"] == "cancelled"

            diagnostics_response = client.get("/api/v1/diagnostics")
            assert diagnostics_response.status_code == 200
            diagnostics = diagnostics_response.json()
            assert diagnostics["stale_worktree_count"] >= 1
            assert any(
                issue["worktree_id"] == worktree_id and issue["recommendation"] == "archive"
                for issue in diagnostics["stale_worktrees"]
            )
    finally:
        app.dependency_overrides.clear()

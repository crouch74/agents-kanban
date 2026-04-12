from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from git import Repo

from acp_core.db import SessionLocal
from acp_core.models import AgentSession
from acp_core.runtime import RuntimeSessionInfo
from acp_core.services import RecoveryService, ServiceContext
from app.bootstrap.dependencies import get_runtime_adapter
from app.main import app


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


def create_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.name", "ACP Test")
    repo.git.config("user.email", "acp@example.test")
    (path / "README.md").write_text("# temp repo\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("init")
    return path


def test_recovery_reconciles_missing_runtime_and_reports_orphans(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "recovery-repo")

    try:
        with TestClient(app) as client:
            project_id = client.post("/api/v1/projects", json={"name": "Recovery Ops"}).json()["id"]
            repository_id = client.post(
                "/api/v1/repositories",
                json={"project_id": project_id, "local_path": str(repo_path)},
            ).json()["id"]
            task_id = client.post(
                "/api/v1/tasks",
                json={"project_id": project_id, "title": "Recover session", "board_column_key": "ready"},
            ).json()["id"]
            session_id = client.post(
                "/api/v1/sessions",
                json={"task_id": task_id, "profile": "executor", "repository_id": repository_id},
            ).json()["id"]

        db = SessionLocal()
        try:
            session = db.get(AgentSession, session_id)
            assert session is not None
            fake_runtime.terminate_session(session.session_name)
            fake_runtime.sessions["acp-orphan-demo"] = {"working_directory": ".", "command": "executor"}

            report = RecoveryService(ServiceContext(db=db, actor_type="system", actor_name="test"), runtime=fake_runtime).reconcile_runtime_sessions()
            db.refresh(session)
            assert session.status == "failed"
            assert report["reconciled_session_count"] >= 1
            assert report["orphan_runtime_session_count"] == 1
            assert report["orphan_runtime_sessions"] == ["acp-orphan-demo"]
        finally:
            db.close()
    finally:
        app.dependency_overrides.clear()

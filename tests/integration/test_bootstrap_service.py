from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from git import Repo

from acp_core.runtime import RuntimeSessionInfo
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
            pane_id="%55",
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



def test_bootstrap_project_nonexistent_path_with_initialize_repo_creates_repo_and_uses_non_interactive_command(
    tmp_path: Path, monkeypatch
) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = tmp_path / "new" / "bootstrap-repo"
    monkeypatch.setenv("GIT_AUTHOR_NAME", "ACP Test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "acp@example.test")

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Missing Path",
                    "repo_path": str(repo_path),
                    "initialize_repo": True,
                    "stack_preset": "fastapi-service",
                    "initial_prompt": "Create initial ACP planning tasks and kickoff notes.",
                },
            )
            assert response.status_code == 201
            payload = response.json()

            assert repo_path.exists()
            assert repo_path.is_dir()
            assert Repo(repo_path).head.is_valid()
            assert payload["project"]["name"] == "Bootstrap Missing Path"
            assert payload["repo_initialized"] is True

            kickoff_command = payload["kickoff_session"]["runtime_metadata"]["command"]
            assert "codex mcp get" in kickoff_command
            assert "codex mcp add" in kickoff_command
            assert "codex exec --full-auto" in kickoff_command
            assert " - < " in kickoff_command
    finally:
        app.dependency_overrides.clear()



def test_bootstrap_project_nonexistent_path_without_initialize_repo_returns_validation_error(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = tmp_path / "missing" / "repo"

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Missing Path Error",
                    "repo_path": str(repo_path),
                    "initialize_repo": False,
                    "stack_preset": "fastapi-service",
                    "initial_prompt": "Attempt bootstrap without initializing repo.",
                },
            )
            assert response.status_code == 400
            assert (
                response.json()["detail"]
                == "Repo path must point to an existing directory or enable Initialize repo with git"
            )
    finally:
        app.dependency_overrides.clear()

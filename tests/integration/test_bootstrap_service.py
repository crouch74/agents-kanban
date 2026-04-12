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

    def spawn_session(self, *, session_name: str, working_directory: Path, profile: str, launch_spec=None, command: str | None = None):
        self.sessions[session_name] = {
            "working_directory": str(working_directory),
            "command": launch_spec.display_command if launch_spec else (command or profile),
        }
        return RuntimeSessionInfo(
            session_name=session_name,
            pane_id="%55",
            window_name="main",
            working_directory=str(launch_spec.working_directory) if launch_spec else str(working_directory),
            command=launch_spec.display_command if launch_spec else (command or profile),
        )

    def session_exists(self, session_name: str) -> bool:
        return session_name in self.sessions

    def capture_tail(self, session_name: str, *, lines: int = 120) -> str:
        return f"session={session_name}\nlines={lines}"

    def terminate_session(self, session_name: str) -> None:
        self.sessions.pop(session_name, None)


def create_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.name", "ACP Test")
    repo.git.config("user.email", "acp@example.test")
    (path / "README.md").write_text("# temp repo\n", encoding="utf-8")
    repo.git.add("--all")
    repo.index.commit("init")
    return path


def test_bootstrap_project_existing_repo_uses_repo_execution_path(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "existing")

    try:
        with TestClient(app) as client:
            preview_response = client.post(
                "/api/v1/projects/bootstrap/preview",
                json={
                    "name": "Bootstrap Existing Path",
                    "repo_path": str(repo_path),
                    "stack_preset": "node-library",
                    "initial_prompt": "Plan and create bootstrap tasks.",
                },
            )
            assert preview_response.status_code == 200
            preview_payload = preview_response.json()
            assert preview_payload["confirmation_required"] is True
            assert preview_payload["execution_path"] == str(repo_path)

            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Existing Path",
                    "repo_path": str(repo_path),
                    "stack_preset": "node-library",
                    "initial_prompt": "Plan and create bootstrap tasks.",
                    "confirm_existing_repo": True,
                },
            )
            assert response.status_code == 201
            payload = response.json()
            assert payload["repo_initialized"] is False
            assert payload["execution_path"] == str(repo_path)
            assert payload["kickoff_worktree"] is None
            assert payload["kickoff_session"]["repository_id"] == payload["repository"]["id"]
    finally:
        app.dependency_overrides.clear()



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
            assert "codex mcp get" not in kickoff_command
            assert "codex mcp add" not in kickoff_command
            assert "codex --dangerously-bypass-approvals-and-sandbox exec" in kickoff_command
            assert " - < " in kickoff_command
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_project_detached_head_without_worktree_fails(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "detached")
    repo = Repo(repo_path)
    repo.git.checkout(repo.head.commit.hexsha)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Detached Head",
                    "repo_path": str(repo_path),
                    "stack_preset": "python-package",
                    "initial_prompt": "Plan the board.",
                    "confirm_existing_repo": True,
                },
            )
            assert response.status_code == 400
            assert "detached HEAD" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_project_worktree_kickoff_uses_worktree_execution_path(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "worktree-enabled")

    try:
        with TestClient(app) as client:
            preview_response = client.post(
                "/api/v1/projects/bootstrap/preview",
                json={
                    "name": "Bootstrap Worktree Kickoff",
                    "repo_path": str(repo_path),
                    "stack_preset": "react-vite",
                    "initial_prompt": "Create initial tasks.",
                    "use_worktree": True,
                },
            )
            assert preview_response.status_code == 200
            preview_payload = preview_response.json()
            assert preview_payload["use_worktree"] is True
            assert preview_payload["execution_path"] != str(repo_path)

            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Worktree Kickoff",
                    "repo_path": str(repo_path),
                    "stack_preset": "react-vite",
                    "initial_prompt": "Create initial tasks.",
                    "use_worktree": True,
                    "confirm_existing_repo": True,
                },
            )
            assert response.status_code == 201
            payload = response.json()
            assert payload["use_worktree"] is True
            assert payload["kickoff_worktree"] is not None
            assert payload["execution_path"] == payload["kickoff_worktree"]["path"]
            assert payload["kickoff_session"]["worktree_id"] == payload["kickoff_worktree"]["id"]
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

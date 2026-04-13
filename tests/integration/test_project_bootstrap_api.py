from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from git import Repo

from app.bootstrap.dependencies import get_runtime_adapter
from app.main import app
from acp_core.runtime import RuntimeSessionInfo


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
            pane_id="%3",
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

    def list_sessions(self, *, prefix: str | None = None):
        names = sorted(self.sessions)
        if prefix is not None:
            names = [name for name in names if name.startswith(prefix)]
        return [
            type("RuntimeSessionSummary", (), {"session_name": name, "window_name": "main"})()
            for name in names
        ]


class FailingRuntime(FakeRuntime):
    def spawn_session(self, *, session_name: str, working_directory: Path, profile: str, launch_spec=None, command: str | None = None):
        raise RuntimeError("runtime unavailable")


def create_git_repo(path: Path, *, with_agents: bool = False) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.name", "ACP Test")
    repo.git.config("user.email", "acp@example.test")
    (path / "README.md").write_text("# temp repo\n", encoding="utf-8")
    if with_agents:
        (path / "AGENTS.md").write_text("# Existing\n\nKeep this note.\n", encoding="utf-8")
    repo.git.add("--all")
    repo.index.commit("init")
    return path


def test_bootstrap_existing_repo_in_repo_mode(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "existing-repo", with_agents=True)

    try:
        with TestClient(app) as client:
            preview_response = client.post(
                "/api/v1/projects/bootstrap/preview",
                json={
                    "name": "Bootstrap Existing Repo",
                    "repo_path": str(repo_path),
                    "stack_preset": "node-library",
                    "initial_prompt": "Plan the initial roadmap and create ACP tasks.",
                },
            )
            assert preview_response.status_code == 200
            preview = preview_response.json()
            assert preview["confirmation_required"] is True
            assert preview["has_existing_commits"] is True
            assert not (repo_path / ".gitignore").exists()
            assert not (repo_path / ".acp").exists()
            assert "<!-- acp-managed:start -->" not in (repo_path / "AGENTS.md").read_text(encoding="utf-8")

            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Existing Repo",
                    "repo_path": str(repo_path),
                    "stack_preset": "node-library",
                    "initial_prompt": "Plan the initial roadmap and create ACP tasks.",
                    "confirm_existing_repo": True,
                },
            )
            assert response.status_code == 201
            payload = response.json()

            assert payload["use_worktree"] is False
            assert payload["kickoff_worktree"] is None
            assert payload["execution_path"] == str(repo_path)
            assert payload["repo_initialized"] is False
            assert payload["scaffold_applied"] is False
            assert payload["kickoff_session"]["repository_id"] == payload["repository"]["id"]
            assert payload["kickoff_session"]["worktree_id"] is None
            assert "codex mcp add" not in payload["kickoff_session"]["runtime_metadata"]["command"]
            assert "agent-control-plane-api/SKILL.md" in (repo_path / ".acp" / "bootstrap-prompt.md").read_text(encoding="utf-8")

            assert "Keep this note." in (repo_path / "AGENTS.md").read_text(encoding="utf-8")
            assert "<!-- acp-managed:start -->" in (repo_path / "AGENTS.md").read_text(encoding="utf-8")
            assert ".acp/" in (repo_path / ".gitignore").read_text(encoding="utf-8")
            project_local = json.loads((repo_path / ".acp" / "project.local.json").read_text(encoding="utf-8"))
            assert project_local["project_id"] == payload["project"]["id"]
            assert project_local["kickoff_task_id"] == payload["kickoff_task"]["id"]
            assert project_local["api_base_url"].startswith("http://")
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_records_resolved_agent_in_session_metadata(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "agent-bootstrap", with_agents=True)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Agent Metadata",
                    "repo_path": str(repo_path),
                    "stack_preset": "node-library",
                    "initial_prompt": "Plan the execution and assign tasks.",
                    "agent_name": "claude-code",
                    "confirm_existing_repo": True,
                },
            )
            assert response.status_code == 201
            payload = response.json()

            assert payload["kickoff_session"]["runtime_metadata"]["agent_name"] == "claude_code"
            assert (
                payload["kickoff_session"]["runtime_metadata"]["launch_inputs"][
                    "agent_name"
                ]
                == "claude_code"
            )
            assert (
                payload["kickoff_session"]["runtime_metadata"]["agent_request"][
                    "agent_name"
                ]
                == "claude_code"
            )
            assert payload["kickoff_session"]["runtime_metadata"]["task_kind"] == "kickoff"
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_existing_repo_with_worktree(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "worktree-repo")

    try:
        with TestClient(app) as client:
            preview_response = client.post(
                "/api/v1/projects/bootstrap/preview",
                json={
                    "name": "Bootstrap Worktree Repo",
                    "repo_path": str(repo_path),
                    "stack_preset": "react-vite",
                    "initial_prompt": "Break the initial work into tasks and subtasks.",
                    "use_worktree": True,
                },
            )
            assert preview_response.status_code == 200
            assert preview_response.json()["confirmation_required"] is True

            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Worktree Repo",
                    "repo_path": str(repo_path),
                    "stack_preset": "react-vite",
                    "initial_prompt": "Break the initial work into tasks and subtasks.",
                    "use_worktree": True,
                    "confirm_existing_repo": True,
                },
            )
            assert response.status_code == 201
            payload = response.json()

            assert payload["use_worktree"] is True
            assert payload["kickoff_worktree"] is not None
            assert payload["kickoff_session"]["worktree_id"] == payload["kickoff_worktree"]["id"]
            assert payload["execution_path"] == payload["kickoff_worktree"]["path"]
            assert Path(payload["execution_path"]).exists()
            assert (Path(payload["execution_path"]) / ".acp" / "project.local.json").exists()
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_empty_folder_with_git_init_in_repo_mode(tmp_path: Path, monkeypatch) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = tmp_path / "new-repo"
    repo_path.mkdir()
    monkeypatch.setenv("GIT_AUTHOR_NAME", "ACP Test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "acp@example.test")

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Empty Repo",
                    "repo_path": str(repo_path),
                    "initialize_repo": True,
                    "stack_preset": "fastapi-service",
                    "initial_prompt": "Set up the first planning slice.",
                },
            )
            assert response.status_code == 201
            payload = response.json()

            repo = Repo(repo_path)
            assert repo.head.is_valid()
            assert payload["repo_initialized"] is True
            assert payload["scaffold_applied"] is True
            assert payload["execution_path"] == str(repo_path)
            assert (repo_path / "pyproject.toml").exists()
            assert (repo_path / "app" / "main.py").exists()
            assert (repo_path / "AGENTS.md").exists()
            assert (repo_path / ".acp" / "bootstrap-prompt.md").exists()
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_empty_folder_with_git_init_and_worktree(tmp_path: Path, monkeypatch) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = tmp_path / "new-worktree-repo"
    repo_path.mkdir()
    monkeypatch.setenv("GIT_AUTHOR_NAME", "ACP Test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "acp@example.test")

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Empty Worktree Repo",
                    "repo_path": str(repo_path),
                    "initialize_repo": True,
                    "stack_preset": "python-package",
                    "initial_prompt": "Create the initial ACP board layout for the package work.",
                    "use_worktree": True,
                },
            )
            assert response.status_code == 201
            payload = response.json()

            assert payload["repo_initialized"] is True
            assert payload["kickoff_worktree"] is not None
            assert Path(payload["kickoff_worktree"]["path"]).exists()
            assert Path(payload["execution_path"]) == Path(payload["kickoff_worktree"]["path"])
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_rejects_non_empty_non_repo_folder(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = tmp_path / "not-a-repo"
    repo_path.mkdir()
    (repo_path / "notes.txt").write_text("hello\n", encoding="utf-8")

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bad Bootstrap",
                    "repo_path": str(repo_path),
                    "initialize_repo": True,
                    "stack_preset": "nextjs",
                    "initial_prompt": "Do the work.",
                },
            )
            assert response.status_code == 400
            assert "empty directory" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_rejects_malformed_payload_with_validation_details(tmp_path: Path) -> None:
    repo_path = create_git_repo(tmp_path / "schema-repo")
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/projects/bootstrap",
            json={
                "name": "Bad",
                "repo_path": str(repo_path),
                "stack_preset": "node-library",
                "initial_prompt": "go",
            },
        )
        assert response.status_code == 422
        payload = response.json()
        assert isinstance(payload["detail"], list)
        assert payload["detail"][0]["loc"] == ["body", "initial_prompt"]
        assert payload["detail"][0]["type"] == "string_too_short"


def test_bootstrap_surfaces_runtime_adapter_failure(tmp_path: Path) -> None:
    app.dependency_overrides[get_runtime_adapter] = lambda: FailingRuntime()
    repo_path = create_git_repo(tmp_path / "runtime-failure-repo")

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Bootstrap Runtime Failure",
                    "repo_path": str(repo_path),
                    "stack_preset": "node-library",
                    "initial_prompt": "Create the first tasks.",
                    "confirm_existing_repo": True,
                },
            )
            assert response.status_code == 502
            payload = response.json()
            assert payload["error"]["code"] == "runtime_adapter_failure"
            assert payload["error"]["details"]["operation"] == "session_spawn"
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_rejects_detached_head_in_repo_mode(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "detached-repo")
    repo = Repo(repo_path)
    repo.git.checkout(repo.head.commit.hexsha)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/projects/bootstrap/preview",
                json={
                    "name": "Detached Repo",
                    "repo_path": str(repo_path),
                    "stack_preset": "node-library",
                    "initial_prompt": "Plan the work.",
                },
            )
            assert response.status_code == 400
            assert "detached HEAD" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_existing_repo_requires_explicit_confirmation(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "confirm-repo")

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/projects/bootstrap",
                json={
                    "name": "Needs Confirm",
                    "repo_path": str(repo_path),
                    "stack_preset": "node-library",
                    "initial_prompt": "Plan the work.",
                },
            )
            assert response.status_code == 400
            assert "preview confirmation" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_bootstrap_skill_guides_dynamic_api_discovery() -> None:
    skill_path = Path(__file__).resolve().parents[2] / "skills" / "agent-control-plane-api" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")

    assert "api_base_url" in content
    assert "/openapi.json" in content
    assert "127.0.0.1:8000/openapi.json" not in content

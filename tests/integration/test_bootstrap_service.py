from __future__ import annotations

from pathlib import Path

import pytest
from git import Repo

from acp_core.db import SessionLocal, init_db
from acp_core.runtime import RuntimeSessionInfo
from acp_core.schemas import ProjectBootstrapCreate, StackPreset
from acp_core.services import BootstrapService, ServiceContext


class FakeRuntime:
    def spawn_session(self, *, session_name: str, working_directory: Path, profile: str, command: str | None = None):
        return RuntimeSessionInfo(
            session_name=session_name,
            pane_id="%42",
            window_name="main",
            working_directory=str(working_directory),
            command=command or profile,
        )

    def session_exists(self, session_name: str) -> bool:
        return True

    def capture_tail(self, session_name: str, *, lines: int = 120) -> str:
        return ""

    def terminate_session(self, session_name: str) -> None:
        return None


def _payload(*, name: str, repo_path: Path, initialize_repo: bool) -> ProjectBootstrapCreate:
    return ProjectBootstrapCreate(
        name=name,
        repo_path=str(repo_path),
        initialize_repo=initialize_repo,
        stack_preset=StackPreset.FASTAPI_SERVICE,
        initial_prompt="Plan the first ACP tasks and backlog.",
    )


def test_build_session_command_uses_non_interactive_full_auto_exec(tmp_path: Path) -> None:
    init_db()
    db = SessionLocal()
    try:
        service = BootstrapService(ServiceContext(db=db, actor_type="system", actor_name="test"), runtime=FakeRuntime())
        command = service._build_session_command(tmp_path)

        assert "codex exec" in command
        assert "--full-auto" in command
    finally:
        db.close()


def test_bootstrap_project_creates_missing_directory_when_initialize_repo_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    init_db()
    db = SessionLocal()
    repo_path = tmp_path / "brand-new" / "project-repo"
    monkeypatch.setenv("GIT_AUTHOR_NAME", "ACP Test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "acp@example.test")

    try:
        service = BootstrapService(
            ServiceContext(db=db, actor_type="system", actor_name="test"),
            runtime=FakeRuntime(),
        )
        result = service.bootstrap_project(
            _payload(name="Bootstrap New Directory", repo_path=repo_path, initialize_repo=True)
        )

        assert repo_path.exists()
        assert repo_path.is_dir()
        assert Repo(repo_path).head.is_valid()
        assert result.project.name == "Bootstrap New Directory"
        assert result.repo_initialized is True
    finally:
        db.close()


def test_bootstrap_project_rejects_missing_directory_without_initialize_repo(tmp_path: Path) -> None:
    init_db()
    db = SessionLocal()
    repo_path = tmp_path / "missing" / "repo"

    try:
        service = BootstrapService(
            ServiceContext(db=db, actor_type="system", actor_name="test"),
            runtime=FakeRuntime(),
        )
        with pytest.raises(
            ValueError,
            match="Repo path must point to an existing directory or enable Initialize repo with git",
        ):
            service.bootstrap_project(_payload(name="Bootstrap Missing Directory", repo_path=repo_path, initialize_repo=False))
    finally:
        db.close()

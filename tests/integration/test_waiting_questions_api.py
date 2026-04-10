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
        return f"session={session_name}"


def create_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.name", "ACP Test")
    repo.git.config("user.email", "acp@example.test")
    (path / "README.md").write_text("# temp repo\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("init")
    return path


def test_waiting_question_blocks_and_resumes_session(tmp_path: Path) -> None:
    fake_runtime = FakeRuntime()
    app.dependency_overrides[get_runtime_adapter] = lambda: fake_runtime
    repo_path = create_git_repo(tmp_path / "waiting-repo")

    try:
        with TestClient(app) as client:
            project_id = client.post("/api/v1/projects", json={"name": "Waiting Ops"}).json()["id"]
            repository_id = client.post(
                "/api/v1/repositories",
                json={"project_id": project_id, "local_path": str(repo_path)},
            ).json()["id"]
            task_id = client.post(
                "/api/v1/tasks",
                json={"project_id": project_id, "title": "Need operator input", "board_column_key": "in_progress"},
            ).json()["id"]
            worktree_id = client.post(
                "/api/v1/worktrees",
                json={"repository_id": repository_id, "task_id": task_id},
            ).json()["id"]
            session_id = client.post(
                "/api/v1/sessions",
                json={"task_id": task_id, "profile": "executor", "worktree_id": worktree_id},
            ).json()["id"]

            question_response = client.post(
                "/api/v1/questions",
                json={
                    "task_id": task_id,
                    "session_id": session_id,
                    "prompt": "Which migration path should I choose?",
                    "blocked_reason": "Two valid implementation options remain.",
                    "urgency": "high",
                },
            )
            assert question_response.status_code == 201
            question = question_response.json()
            assert question["status"] == "open"

            session_response = client.get(f"/api/v1/sessions/{session_id}")
            assert session_response.status_code == 200
            assert session_response.json()["status"] == "waiting_human"

            task_response = client.get(f"/api/v1/tasks/{task_id}")
            assert task_response.status_code == 200
            assert task_response.json()["waiting_for_human"] is True

            answer_response = client.post(
                f"/api/v1/questions/{question['id']}/replies",
                json={"responder_name": "operator", "body": "Use the lower-risk path and document the tradeoff."},
            )
            assert answer_response.status_code == 200
            assert answer_response.json()["status"] == "answered"
            assert len(answer_response.json()["replies"]) == 1

            session_after_response = client.get(f"/api/v1/sessions/{session_id}")
            assert session_after_response.status_code == 200
            assert session_after_response.json()["status"] == "running"

            task_after_response = client.get(f"/api/v1/tasks/{task_id}")
            assert task_after_response.status_code == 200
            assert task_after_response.json()["waiting_for_human"] is False
    finally:
        app.dependency_overrides.clear()


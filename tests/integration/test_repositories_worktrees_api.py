from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from git import Repo

from app.main import app


def create_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.name", "ACP Test")
    repo.git.config("user.email", "acp@example.test")
    (path / "README.md").write_text("# temp repo\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("init")
    return path


def test_attach_repository_and_manage_worktree(tmp_path: Path) -> None:
    repo_path = create_git_repo(tmp_path / "attached-repo")

    with TestClient(app) as client:
        project_response = client.post("/api/v1/projects", json={"name": "Repo Ops"})
        project_id = project_response.json()["id"]

        repository_response = client.post(
            "/api/v1/repositories",
            json={"project_id": project_id, "local_path": str(repo_path)},
        )
        assert repository_response.status_code == 201
        repository = repository_response.json()
        assert repository["name"] == "attached-repo"
        assert repository["default_branch"] in {"master", "main"}

        task_response = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Allocate worktree", "board_column_key": "ready"},
        )
        task_id = task_response.json()["id"]

        worktree_response = client.post(
            "/api/v1/worktrees",
            json={"repository_id": repository["id"], "task_id": task_id},
        )
        assert worktree_response.status_code == 201
        worktree = worktree_response.json()
        assert worktree["status"] == "active"
        assert Path(worktree["path"]).exists()
        assert worktree["branch_name"].startswith("acp/repo-ops/")

        archive_response = client.patch(
            f"/api/v1/worktrees/{worktree['id']}",
            json={"status": "archived"},
        )
        assert archive_response.status_code == 200
        assert archive_response.json()["status"] == "archived"
        assert Path(worktree["path"]).exists()

        prune_response = client.patch(
            f"/api/v1/worktrees/{worktree['id']}",
            json={"status": "pruned"},
        )
        assert prune_response.status_code == 200
        assert prune_response.json()["status"] == "pruned"
        assert not Path(worktree["path"]).exists()


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


def test_create_repository_rejects_malformed_payload_with_validation_details(tmp_path: Path) -> None:
    repo_path = create_git_repo(tmp_path / "bad-repo")
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/repositories",
            json={"project_id": "proj-missing", "local_path": str(repo_path), "name": "x" * 300},
        )
        assert response.status_code == 422
        payload = response.json()
        assert isinstance(payload["detail"], list)
        assert payload["detail"][0]["loc"] == ["body", "name"]
        assert payload["detail"][0]["type"] == "string_too_long"


def test_create_repository_rejects_missing_project_foreign_key(tmp_path: Path) -> None:
    repo_path = create_git_repo(tmp_path / "missing-project-repo")
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/repositories",
            json={"project_id": "proj-missing", "local_path": str(repo_path)},
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Project not found"}


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


def test_worktree_mutations_validate_payload_foreign_keys_and_transitions(tmp_path: Path) -> None:
    repo_path = create_git_repo(tmp_path / "worktree-failure-repo")

    with TestClient(app) as client:
        project_id = client.post("/api/v1/projects", json={"name": "Worktree Failure Ops"}).json()["id"]
        repository_id = client.post(
            "/api/v1/repositories",
            json={"project_id": project_id, "local_path": str(repo_path)},
        ).json()["id"]
        task_id = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Worktree failure task", "board_column_key": "ready"},
        ).json()["id"]
        worktree_id = client.post(
            "/api/v1/worktrees",
            json={"repository_id": repository_id, "task_id": task_id},
        ).json()["id"]

        malformed_create = client.post("/api/v1/worktrees", json={"task_id": task_id})
        assert malformed_create.status_code == 422
        assert malformed_create.json()["detail"][0]["loc"] == ["body", "repository_id"]

        missing_fk_create = client.post(
            "/api/v1/worktrees",
            json={"repository_id": "repo-missing", "task_id": task_id},
        )
        assert missing_fk_create.status_code == 400
        assert missing_fk_create.json() == {"detail": "Repository not found"}

        malformed_patch = client.patch(f"/api/v1/worktrees/{worktree_id}", json={"status": "unknown"})
        assert malformed_patch.status_code == 422
        assert malformed_patch.json()["detail"][0]["loc"] == ["body", "status"]

        forbidden_transition = client.patch(f"/api/v1/worktrees/{worktree_id}", json={"status": "pruned"})
        assert forbidden_transition.status_code == 400
        assert forbidden_transition.json()["detail"].startswith("Invalid worktree transition")


def test_worktree_creation_rejects_cross_project_task(tmp_path: Path) -> None:
    repo_path = create_git_repo(tmp_path / "cross-project-worktree-repo")

    with TestClient(app) as client:
        project_a = client.post("/api/v1/projects", json={"name": "Repo Project"}).json()["id"]
        project_b = client.post("/api/v1/projects", json={"name": "Task Project"}).json()["id"]
        repository_id = client.post(
            "/api/v1/repositories",
            json={"project_id": project_a, "local_path": str(repo_path)},
        ).json()["id"]
        task_id = client.post(
            "/api/v1/tasks",
            json={"project_id": project_b, "title": "Cross-project task"},
        ).json()["id"]

        response = client.post(
            "/api/v1/worktrees",
            json={"repository_id": repository_id, "task_id": task_id},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Task must belong to the same project as the repository"

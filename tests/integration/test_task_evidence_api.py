from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_task_detail_includes_comments_checks_and_artifacts() -> None:
    with TestClient(app) as client:
        project_id = client.post("/api/v1/projects", json={"name": "Evidence Ops"}).json()["id"]
        blocker_task_id = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Prepare dependency", "board_column_key": "ready"},
        ).json()["id"]
        task_id = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Collect evidence", "board_column_key": "review"},
        ).json()["id"]

        dependency_response = client.post(
            f"/api/v1/tasks/{task_id}/dependencies",
            json={"depends_on_task_id": blocker_task_id, "relationship_type": "blocks"},
        )
        assert dependency_response.status_code == 201

        comment_response = client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"author_name": "operator", "body": "Needs a concise review note."},
        )
        assert comment_response.status_code == 201

        check_response = client.post(
            f"/api/v1/tasks/{task_id}/checks",
            json={"check_type": "review", "status": "passed", "summary": "Reviewed manually."},
        )
        assert check_response.status_code == 201

        artifact_response = client.post(
            f"/api/v1/tasks/{task_id}/artifacts",
            json={"artifact_type": "diff", "name": "Patch diff", "uri": "git:diff:HEAD~1..HEAD"},
        )
        assert artifact_response.status_code == 201

        detail_response = client.get(f"/api/v1/tasks/{task_id}/detail")
        assert detail_response.status_code == 200
        payload = detail_response.json()
        assert payload["title"] == "Collect evidence"
        assert len(payload["dependencies"]) == 1
        assert payload["dependencies"][0]["depends_on_task_id"] == blocker_task_id
        assert len(payload["comments"]) == 1
        assert payload["comments"][0]["body"] == "Needs a concise review note."
        assert len(payload["checks"]) == 1
        assert payload["checks"][0]["status"] == "passed"
        assert len(payload["artifacts"]) == 1
        assert payload["artifacts"][0]["uri"] == "git:diff:HEAD~1..HEAD"

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


def test_task_evidence_write_routes_reject_invalid_payloads_and_missing_foreign_keys() -> None:
    with TestClient(app) as client:
        project_id = client.post("/api/v1/projects", json={"name": "Evidence Failures"}).json()["id"]
        task_id = client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Evidence task"}).json()["id"]

        malformed_comment = client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"author_name": "a", "body": ""},
        )
        assert malformed_comment.status_code == 422
        assert malformed_comment.json()["detail"][0]["loc"] == ["body", "author_name"]

        missing_task_comment = client.post(
            "/api/v1/tasks/task-missing/comments",
            json={"author_name": "operator", "body": "note"},
        )
        assert missing_task_comment.status_code == 400
        assert missing_task_comment.json() == {"detail": "Task not found"}

        malformed_check = client.post(
            f"/api/v1/tasks/{task_id}/checks",
            json={"check_type": "a", "status": "passed", "summary": ""},
        )
        assert malformed_check.status_code == 422
        assert malformed_check.json()["detail"][0]["loc"] == ["body", "check_type"]

        missing_task_check = client.post(
            "/api/v1/tasks/task-missing/checks",
            json={"check_type": "review", "status": "passed", "summary": "ok"},
        )
        assert missing_task_check.status_code == 400
        assert missing_task_check.json() == {"detail": "Task not found"}

        malformed_artifact = client.post(
            f"/api/v1/tasks/{task_id}/artifacts",
            json={"artifact_type": "x", "name": "x", "uri": ""},
        )
        assert malformed_artifact.status_code == 422
        assert malformed_artifact.json()["detail"][0]["loc"] == ["body", "artifact_type"]

        missing_task_artifact = client.post(
            "/api/v1/tasks/task-missing/artifacts",
            json={"artifact_type": "diff", "name": "Patch", "uri": "git:diff"},
        )
        assert missing_task_artifact.status_code == 400
        assert missing_task_artifact.json() == {"detail": "Task not found"}

        malformed_dependency = client.post(
            f"/api/v1/tasks/{task_id}/dependencies",
            json={"relationship_type": "blocks"},
        )
        assert malformed_dependency.status_code == 422
        assert malformed_dependency.json()["detail"][0]["loc"] == ["body", "depends_on_task_id"]

        missing_foreign_key_dependency = client.post(
            f"/api/v1/tasks/{task_id}/dependencies",
            json={"depends_on_task_id": "task-missing", "relationship_type": "blocks"},
        )
        assert missing_foreign_key_dependency.status_code == 400
        assert missing_foreign_key_dependency.json() == {"detail": "Task not found"}

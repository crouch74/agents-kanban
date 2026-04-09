from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_create_and_move_task_through_valid_workflow() -> None:
    with TestClient(app) as client:
        project_response = client.post("/api/v1/projects", json={"name": "Task Flow"})
        project_id = project_response.json()["id"]

        task_response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": project_id,
                "title": "Create the first execution slice",
                "board_column_key": "ready",
            },
        )
        assert task_response.status_code == 201
        task = task_response.json()
        assert task["workflow_state"] == "ready"

        move_response = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"workflow_state": "in_progress"},
        )
        assert move_response.status_code == 200
        assert move_response.json()["workflow_state"] == "in_progress"

        invalid_response = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"workflow_state": "done"},
        )
        assert invalid_response.status_code == 400
        assert "Invalid workflow transition" in invalid_response.json()["detail"]


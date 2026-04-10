from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_websocket_broadcasts_committed_mutations() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws") as websocket:
            connected = websocket.receive_json()
            assert connected["type"] == "system.connected"

            project_response = client.post("/api/v1/projects", json={"name": "Realtime Ops"})
            assert project_response.status_code == 201
            project = project_response.json()

            project_event = websocket.receive_json()
            assert project_event["type"] == "mutation.committed"
            assert project_event["event_type"] == "project.created"
            assert project_event["project_id"] == project["id"]

            task_response = client.post(
                "/api/v1/tasks",
                json={"project_id": project["id"], "title": "Broadcast changes", "board_column_key": "ready"},
            )
            assert task_response.status_code == 201
            task = task_response.json()

            task_event = websocket.receive_json()
            assert task_event["event_type"] == "task.created"
            assert task_event["task_id"] == task["id"]
            assert task_event["project_id"] == project["id"]

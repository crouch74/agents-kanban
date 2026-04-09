from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_create_project_creates_default_board_columns() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/projects",
            json={"name": "Operator Console", "description": "Daily control plane"},
        )

        assert response.status_code == 201
        project = response.json()
        assert project["name"] == "Operator Console"
        assert project["slug"] == "operator-console"

        board_response = client.get(f"/api/v1/projects/{project['id']}")
        assert board_response.status_code == 200
        board = board_response.json()["board"]
        assert [column["key"] for column in board["columns"]] == [
            "backlog",
            "ready",
            "in_progress",
            "review",
            "done",
        ]


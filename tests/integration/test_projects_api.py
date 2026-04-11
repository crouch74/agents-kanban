from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from acp_core.db import SessionLocal
from acp_core.models import BoardColumn, Task
from app.main import app


def test_create_project_rejects_malformed_payload_with_validation_details() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/projects", json={"name": "x"})

        assert response.status_code == 422
        payload = response.json()
        assert isinstance(payload["detail"], list)
        assert payload["detail"][0]["loc"] == ["body", "name"]
        assert payload["detail"][0]["type"] == "string_too_short"


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


def test_project_board_load_repairs_missing_canonical_columns() -> None:
    with TestClient(app) as client:
        project_id = client.post(
            "/api/v1/projects",
            json={"name": "Legacy Board", "description": "Repair old board columns"},
        ).json()["id"]
        task_id = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Keep backlog task stable"},
        ).json()["id"]

        db = SessionLocal()
        try:
            columns = list(
                db.scalars(
                    select(BoardColumn)
                    .join(BoardColumn.board)
                    .where(BoardColumn.board.has(project_id=project_id))
                    .order_by(BoardColumn.position.asc())
                )
            )
            removed_keys = {"review", "done"}
            preserved_task = db.get(Task, task_id)
            assert preserved_task is not None
            original_column_id = preserved_task.board_column_id

            for column in columns:
                if column.key in removed_keys:
                    db.delete(column)
            db.commit()
        finally:
            db.close()

        board_response = client.get(f"/api/v1/projects/{project_id}")
        assert board_response.status_code == 200
        board = board_response.json()["board"]
        assert [column["key"] for column in board["columns"]] == [
            "backlog",
            "ready",
            "in_progress",
            "review",
            "done",
        ]

        db = SessionLocal()
        try:
            repaired_task = db.get(Task, task_id)
            assert repaired_task is not None
            assert repaired_task.board_column_id == original_column_id
        finally:
            db.close()

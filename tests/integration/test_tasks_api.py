from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _create_project(client: TestClient, name: str = "Task Flow") -> str:
    return client.post("/api/v1/projects", json={"name": name}).json()["id"]


def test_create_move_and_comment_task_lifecycle() -> None:
    with TestClient(app) as client:
        project_id = _create_project(client)
        board = client.get(f"/api/v1/projects/{project_id}/board").json()

        created = client.post(
            "/api/v1/tasks",
            json={
                "project_id": project_id,
                "title": "Implement parser",
                "board_column_key": "backlog",
                "source": "agent",
            },
        )
        assert created.status_code == 201
        task = created.json()
        assert task["workflow_state"] == "backlog"
        assert task["source"] == "agent"

        in_progress = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"workflow_state": "in_progress"},
        )
        assert in_progress.status_code == 200
        assert in_progress.json()["workflow_state"] == "in_progress"

        in_progress_column = next(column for column in board["columns"] if column["key"] == "in_progress")
        moved = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"board_column_id": in_progress_column["id"]},
        )
        assert moved.status_code == 200
        assert moved.json()["workflow_state"] == "in_progress"

        comment = client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={
                "author_type": "agent",
                "author_name": "codex",
                "source": "mcp",
                "body": "Parser implementation started.",
            },
        )
        assert comment.status_code == 201
        assert comment.json()["author_name"] == "codex"
        assert comment.json()["source"] == "mcp"

        detail = client.get(f"/api/v1/tasks/{task['id']}/detail")
        assert detail.status_code == 200
        assert detail.json()["comments"][0]["body"] == "Parser implementation started."


def test_task_search_and_events_reflect_updates() -> None:
    with TestClient(app) as client:
        project_id = _create_project(client, "Search Board")
        task = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Investigate flaky parser", "source": "operator"},
        ).json()

        client.patch(f"/api/v1/tasks/{task['id']}", json={"workflow_state": "in_progress"})

        search = client.get(
            "/api/v1/search",
            params={"q": "flaky", "project_id": project_id},
        )
        assert search.status_code == 200
        hits = search.json()["hits"]
        assert any(hit["entity_type"] == "task" and hit["entity_id"] == task["id"] for hit in hits)

        events = client.get("/api/v1/events", params={"project_id": project_id, "limit": 20})
        assert events.status_code == 200
        assert any(event["event_type"] == "task.updated" for event in events.json())

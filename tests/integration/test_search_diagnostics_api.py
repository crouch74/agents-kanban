from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_search_and_diagnostics_surface_operational_state() -> None:
    with TestClient(app) as client:
        project_id = client.post(
            "/api/v1/projects",
            json={"name": "Search Ops", "description": "Global search validation"},
        ).json()["id"]
        task_id = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Searchable task", "description": "contains alpha keyword"},
        ).json()["id"]
        client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"author_name": "operator", "body": "alpha comment evidence"},
        )
        client.post(
            "/api/v1/questions",
            json={"task_id": task_id, "prompt": "alpha question prompt", "blocked_reason": "Need alpha approval"},
        )

        search_response = client.get("/api/v1/search?q=alpha")
        assert search_response.status_code == 200
        payload = search_response.json()
        assert payload["query"] == "alpha"
        entity_types = {hit["entity_type"] for hit in payload["hits"]}
        assert "task" in entity_types
        assert "task_comment" in entity_types
        assert "waiting_question" in entity_types

        diagnostics_response = client.get("/api/v1/diagnostics")
        assert diagnostics_response.status_code == 200
        diagnostics = diagnostics_response.json()
        assert diagnostics["current_project_count"] >= 1
        assert diagnostics["current_task_count"] >= 1
        assert diagnostics["current_open_question_count"] >= 1
        assert "database_path" in diagnostics


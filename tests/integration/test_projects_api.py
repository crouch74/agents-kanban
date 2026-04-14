from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_create_project_and_fetch_overview() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/projects",
            json={"name": "Operator Console", "description": "Task board for migration"},
        )

        assert response.status_code == 201
        project = response.json()
        assert project["name"] == "Operator Console"
        assert project["slug"] == "operator-console"

        overview = client.get(f"/api/v1/projects/{project['id']}")
        assert overview.status_code == 200
        body = overview.json()
        assert body["project"]["id"] == project["id"]
        assert [column["key"] for column in body["board"]["columns"]] == [
            "backlog",
            "in_progress",
            "done",
        ]


def test_archive_project_hides_from_active_project_list() -> None:
    with TestClient(app) as client:
        project_id = client.post("/api/v1/projects", json={"name": "Archive Candidate"}).json()["id"]

        projects_before = client.get("/api/v1/projects").json()
        assert any(item["id"] == project_id for item in projects_before)

        archived = client.post(f"/api/v1/projects/{project_id}/archive")
        assert archived.status_code == 200
        assert archived.json()["archived"] is True

        projects_after = client.get("/api/v1/projects").json()
        assert all(item["id"] != project_id for item in projects_after)

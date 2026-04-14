from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_dashboard_endpoint_returns_task_counts() -> None:
    with TestClient(app) as client:
        project_id = client.post("/api/v1/projects", json={"name": "Dashboard Seed"}).json()["id"]
        client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Seed task"})

        response = client.get("/api/v1/dashboard")
        assert response.status_code == 200
        payload = response.json()
        assert "task_counts" in payload
        assert payload["task_counts"]["backlog"] >= 1


def test_settings_diagnostics_and_purge_db_endpoints() -> None:
    with TestClient(app) as client:
        project_id = client.post("/api/v1/projects", json={"name": "Purge Seed"}).json()["id"]
        client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Seed task"})

        diagnostics = client.get("/api/v1/settings/diagnostics")
        assert diagnostics.status_code == 200
        diagnostics_payload = diagnostics.json()
        assert diagnostics_payload["services"]["database"]["status"] == "ok"
        assert "database_path" in diagnostics_payload["paths"]
        assert diagnostics_payload["row_counts"]["tasks"] >= 1

        purge = client.post("/api/v1/settings/purge-db")
        assert purge.status_code == 200
        assert purge.json()["status"] == "ok"

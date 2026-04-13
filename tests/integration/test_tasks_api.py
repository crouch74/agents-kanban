from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_task_write_routes_reject_malformed_payloads_and_missing_foreign_keys() -> None:
    with TestClient(app) as client:
        malformed_create = client.post("/api/v1/tasks", json={"project_id": "proj", "title": "x"})
        assert malformed_create.status_code == 422
        assert malformed_create.json()["detail"][0]["loc"] == ["body", "title"]

        missing_fk_create = client.post(
            "/api/v1/tasks",
            json={"project_id": "proj-missing", "title": "Valid title"},
        )
        assert missing_fk_create.status_code == 400
        assert missing_fk_create.json() == {"detail": "Project board not found"}


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

        review_response = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"workflow_state": "review"},
        )
        assert review_response.status_code == 200
        assert review_response.json()["workflow_state"] == "review"

        evidence_missing_response = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"workflow_state": "done"},
        )
        assert evidence_missing_response.status_code == 400
        assert "passing check or artifact" in evidence_missing_response.json()["detail"]

        check_response = client.post(
            f"/api/v1/tasks/{task['id']}/checks",
            json={"check_type": "verification", "status": "passed", "summary": "Ready to complete."},
        )
        assert check_response.status_code == 201

        done_response = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"workflow_state": "done"},
        )
        assert done_response.status_code == 200
        assert done_response.json()["workflow_state"] == "done"

        malformed_patch = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"title": "x"},
        )
        assert malformed_patch.status_code == 422
        assert malformed_patch.json()["detail"][0]["loc"] == ["body", "title"]


def test_task_board_column_moves_are_authoritative_and_cancelled_tasks_can_reopen() -> None:
    with TestClient(app) as client:
        project_id = client.post("/api/v1/projects", json={"name": "Board Authority"}).json()["id"]
        board = client.get(f"/api/v1/projects/{project_id}/board").json()
        task = client.post(
            "/api/v1/tasks",
            json={
                "project_id": project_id,
                "title": "Jump straight to done",
                "board_column_key": "ready",
            },
        ).json()

        review_column = next(column for column in board["columns"] if column["key"] == "review")
        done_column = next(column for column in board["columns"] if column["key"] == "done")

        review_move = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"board_column_id": review_column["id"]},
        )
        assert review_move.status_code == 200
        assert review_move.json()["workflow_state"] == "review"

        done_without_evidence = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"board_column_id": done_column["id"]},
        )
        assert done_without_evidence.status_code == 400
        assert "passing check or artifact" in done_without_evidence.json()["detail"]

        client.post(
            f"/api/v1/tasks/{task['id']}/checks",
            json={"check_type": "verification", "status": "passed", "summary": "Ready to finish."},
        )
        done_with_evidence = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"board_column_id": done_column["id"]},
        )
        assert done_with_evidence.status_code == 200
        assert done_with_evidence.json()["workflow_state"] == "done"

        cancelled = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"workflow_state": "cancelled"},
        )
        assert cancelled.status_code == 200
        assert cancelled.json()["workflow_state"] == "cancelled"

        board_without_cancelled = client.get(f"/api/v1/projects/{project_id}/board")
        assert board_without_cancelled.status_code == 200
        assert all(candidate["id"] != task["id"] for candidate in board_without_cancelled.json()["tasks"])

        reopened = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"workflow_state": "backlog"},
        )
        assert reopened.status_code == 200
        assert reopened.json()["workflow_state"] == "backlog"

        board_with_reopened = client.get(f"/api/v1/projects/{project_id}/board")
        assert board_with_reopened.status_code == 200
        assert any(candidate["id"] == task["id"] for candidate in board_with_reopened.json()["tasks"])


def test_create_subtask_under_parent_task() -> None:
    with TestClient(app) as client:
        project_id = client.post("/api/v1/projects", json={"name": "Subtask Flow"}).json()["id"]
        parent_task = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Parent task", "board_column_key": "ready"},
        ).json()

        subtask_response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": project_id,
                "title": "Child subtask",
                "parent_task_id": parent_task["id"],
                "board_column_key": "backlog",
            },
        )
        assert subtask_response.status_code == 201
        subtask = subtask_response.json()
        assert subtask["parent_task_id"] == parent_task["id"]

        board_response = client.get(f"/api/v1/projects/{project_id}/board")
        assert board_response.status_code == 200
        board = board_response.json()
        assert any(task["id"] == subtask["id"] and task["parent_task_id"] == parent_task["id"] for task in board["tasks"])


def test_create_subtask_rejects_nested_subtask() -> None:
    with TestClient(app) as client:
        project_id = client.post("/api/v1/projects", json={"name": "Nested Subtasks"}).json()["id"]
        parent_task = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Parent task", "board_column_key": "ready"},
        ).json()
        child_task = client.post(
            "/api/v1/tasks",
            json={
                "project_id": project_id,
                "title": "Child task",
                "parent_task_id": parent_task["id"],
                "board_column_key": "ready",
            },
        ).json()

        nested_response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": project_id,
                "title": "Nested child",
                "parent_task_id": child_task["id"],
                "board_column_key": "ready",
            },
        )
        assert nested_response.status_code == 400
        assert (
            nested_response.json()["detail"]
            == "Nested subtasks beyond one level are not supported in v1"
        )

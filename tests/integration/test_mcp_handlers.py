from __future__ import annotations

from app.main import app
from acp_mcp_server import handlers


def test_mcp_handlers_expose_core_control_plane_workflows() -> None:
    project = handlers.project_create("MCP Ops", "Agent-facing surface", client_request_id="project-1")
    project_id = project["id"]
    project_replayed = handlers.project_create("MCP Ops", "Agent-facing surface", client_request_id="project-1")
    assert project_replayed["id"] == project_id

    board = handlers.board_get(project_id)
    assert board["project_id"] == project_id

    task = handlers.task_create(project_id=project_id, title="Ship MCP tools", client_request_id="task-1")
    task_id = task["id"]
    task_replayed = handlers.task_create(project_id=project_id, title="Ship MCP tools", client_request_id="task-1")
    assert task_replayed["id"] == task_id

    comment = handlers.task_comment_add(
        task_id=task_id,
        author_name="agent",
        body="starting work",
        client_request_id="comment-1",
    )
    assert comment["task_id"] == task_id
    comment_replayed = handlers.task_comment_add(
        task_id=task_id,
        author_name="agent",
        body="starting work",
        client_request_id="comment-1",
    )
    assert comment_replayed["id"] == comment["id"]

    check = handlers.task_check_add(
        task_id=task_id,
        check_type="self_check",
        status="passed",
        summary="looks good",
        client_request_id="check-1",
    )
    assert check["status"] == "passed"
    check_replayed = handlers.task_check_add(
        task_id=task_id,
        check_type="self_check",
        status="passed",
        summary="looks good",
        client_request_id="check-1",
    )
    assert check_replayed["id"] == check["id"]

    question = handlers.question_open(
        task_id=task_id,
        prompt="Need a final confirmation?",
        urgency="medium",
        client_request_id="question-1",
    )
    assert question["task_id"] == task_id
    question_replayed = handlers.question_open(
        task_id=task_id,
        prompt="Need a final confirmation?",
        urgency="medium",
        client_request_id="question-1",
    )
    assert question_replayed["id"] == question["id"]

    question_detail = handlers.question_answer_get(question["id"])
    assert question_detail["prompt"] == "Need a final confirmation?"

    search = handlers.context_search("confirmation", project_id=project_id)
    assert search["hits"]
    assert any(hit["entity_type"] == "waiting_question" for hit in search["hits"])

    events = handlers.recent_events_resource(task_id=task_id)
    assert events
    assert any(event["event_type"] == "task.created" for event in events)

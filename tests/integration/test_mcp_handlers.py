from __future__ import annotations

from app.main import app
from acp_mcp_server import handlers


def test_mcp_handlers_expose_core_control_plane_workflows() -> None:
    project = handlers.project_create("MCP Ops", "Agent-facing surface")
    project_id = project["id"]

    board = handlers.board_get(project_id)
    assert board["project_id"] == project_id

    task = handlers.task_create(project_id=project_id, title="Ship MCP tools")
    task_id = task["id"]

    comment = handlers.task_comment_add(task_id=task_id, author_name="agent", body="starting work")
    assert comment["task_id"] == task_id

    check = handlers.task_check_add(task_id=task_id, check_type="self_check", status="passed", summary="looks good")
    assert check["status"] == "passed"

    question = handlers.question_open(task_id=task_id, prompt="Need a final confirmation?", urgency="medium")
    assert question["task_id"] == task_id

    question_detail = handlers.question_answer_get(question["id"])
    assert question_detail["prompt"] == "Need a final confirmation?"

    search = handlers.context_search("confirmation", project_id=project_id)
    assert search["hits"]
    assert any(hit["entity_type"] == "waiting_question" for hit in search["hits"])


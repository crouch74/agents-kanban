from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from acp_core.models import Task
from acp_core.schemas import TaskPatch
from acp_core.services.base_service import ServiceContext
from acp_core.services.task_write_service import TaskWriteService


class ConcreteTaskWriteService(TaskWriteService):
    def __init__(self, context: ServiceContext) -> None:
        self.context = context


def test_patch_task_notifies_orchestrator_for_non_ready_updates(monkeypatch) -> None:
    db = MagicMock()
    context = ServiceContext(db=db, actor_type="human", actor_name="tester")
    context.record_event = MagicMock()
    task = Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Task",
        workflow_state="in_progress",
        priority="medium",
        waiting_for_human=False,
        metadata_json={},
    )
    service = ConcreteTaskWriteService(context)
    service.get_task = MagicMock(return_value=task)
    service._column_for_workflow_state = MagicMock(return_value=SimpleNamespace(id="review-col"))

    handled: list[str] = []

    class FakeTaskOrchestrationService:
        def __init__(self, inner_context: ServiceContext) -> None:
            self.context = inner_context

        def handle_task_updated(self, task_id: str) -> None:
            handled.append(task_id)

    monkeypatch.setattr(
        "acp_core.services.task_orchestration_service.TaskOrchestrationService",
        FakeTaskOrchestrationService,
    )

    patched = service.patch_task(task.id, TaskPatch(workflow_state="review"))

    assert patched.workflow_state == "review"
    assert patched.board_column_id == "review-col"
    assert handled == ["task-1"]
    db.commit.assert_called()
    db.refresh.assert_called_with(task)


def test_claim_task_persists_claim_metadata() -> None:
    db = MagicMock()
    context = ServiceContext(db=db, actor_type="system", actor_name="tester")
    context.record_event = MagicMock()
    task = Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Task",
        workflow_state="ready",
        priority="medium",
        waiting_for_human=False,
        metadata_json={"existing": True},
    )
    service = ConcreteTaskWriteService(context)
    service.get_task = MagicMock(return_value=task)

    claimed = service.claim_task("task-1", actor_name="executor", session_id="session-1")

    assert claimed.metadata_json["existing"] is True
    assert claimed.metadata_json["claimed_by"] == "executor"
    assert claimed.metadata_json["claimed_session_id"] == "session-1"
    context.record_event.assert_called_once_with(
        entity_type="task",
        entity_id="task-1",
        event_type="task.claimed",
        payload_json={"actor_name": "executor", "session_id": "session-1"},
    )

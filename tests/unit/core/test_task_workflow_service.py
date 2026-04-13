from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acp_core.services.base_service import ServiceContext
from acp_core.services.task_workflow_service import TaskWorkflowService


class ConcreteTaskWorkflowService(TaskWorkflowService):
    def __init__(self, context: ServiceContext) -> None:
        self.context = context


def test_ensure_completion_evidence_raises_with_missing_requirements() -> None:
    context = ServiceContext(db=MagicMock(), actor_type="human", actor_name="tester")
    service = ConcreteTaskWorkflowService(context)
    service.get_completion_readiness = MagicMock(
        return_value=SimpleNamespace(
            can_mark_done=False,
            missing_requirements=["attach at least one passing check or artifact"],
        )
    )

    with pytest.raises(ValueError, match="Task cannot move to done"):
        service._ensure_completion_evidence(SimpleNamespace(id="task-1"))


def test_auto_trigger_agent_session_delegates_to_task_orchestrator(monkeypatch) -> None:
    context = ServiceContext(db=MagicMock(), actor_type="human", actor_name="tester")
    service = ConcreteTaskWorkflowService(context)
    handled: list[str] = []

    class FakeTaskOrchestrationService:
        def __init__(self, inner_context: ServiceContext) -> None:
            self.context = inner_context

        def handle_task_ready(self, task_id: str) -> None:
            handled.append(task_id)

    monkeypatch.setattr(
        "acp_core.services.task_orchestration_service.TaskOrchestrationService",
        FakeTaskOrchestrationService,
    )

    service._auto_trigger_agent_session(SimpleNamespace(id="task-123"))

    assert handled == ["task-123"]

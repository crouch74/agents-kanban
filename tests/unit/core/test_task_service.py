from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from acp_core.models import Task
from acp_core.schemas import TaskPatch
from acp_core.services.base_service import ServiceContext
from acp_core.services.task_service import TaskService


@pytest.fixture
def db_session_mock() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.get = MagicMock()
    db.scalar = MagicMock(return_value=None)
    db.scalars = MagicMock(return_value=[])
    return db


@pytest.fixture
def service_context(db_session_mock: MagicMock) -> ServiceContext:
    return ServiceContext(db=db_session_mock, actor_type="human", actor_name="tester")


@pytest.fixture
def task_record() -> Task:
    return Task(
        id="task-1",
        project_id="proj-1",
        board_column_id="col-1",
        title="Task",
        workflow_state="review",
        priority="medium",
        waiting_for_human=False,
        metadata_json={},
    )


@pytest.mark.parametrize(
    ("current_state", "next_state"),
    [
        ("backlog", "done"),
        ("ready", "review"),
        ("in_progress", "done"),
        ("cancelled", "ready"),
    ],
)
def test_patch_task_rejects_invalid_workflow_transitions(
    service_context: ServiceContext,
    task_record: Task,
    current_state: str,
    next_state: str,
) -> None:
    task_record.workflow_state = current_state
    service = TaskService(service_context)
    service.get_task = MagicMock(return_value=task_record)

    with pytest.raises(ValueError, match="Invalid workflow transition"):
        service.patch_task(task_record.id, TaskPatch(workflow_state=next_state))


@pytest.mark.parametrize(
    "missing_requirements",
    [
        ["attach at least one passing check or artifact"],
        ["resolve blocking dependencies"],
        ["close open waiting questions"],
    ],
)
def test_patch_task_enforces_completion_gating(
    service_context: ServiceContext,
    task_record: Task,
    missing_requirements: list[str],
) -> None:
    service = TaskService(service_context)
    service.get_task = MagicMock(return_value=task_record)
    service.get_completion_readiness = MagicMock(
        return_value=SimpleNamespace(can_mark_done=False, missing_requirements=missing_requirements)
    )

    with pytest.raises(ValueError, match="Task cannot move to done"):
        service.patch_task(task_record.id, TaskPatch(workflow_state="done"))

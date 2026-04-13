from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from acp_core.services.base_service import ServiceContext
from acp_core.services.task_read_service import TaskReadService


class ConcreteTaskReadService(TaskReadService):
    def __init__(self, context: ServiceContext) -> None:
        self.context = context


def test_get_completion_readiness_reports_all_missing_requirements() -> None:
    db = MagicMock()
    db.scalar = MagicMock(side_effect=[0, 0, 1, 2])
    context = ServiceContext(db=db, actor_type="human", actor_name="tester")

    service = ConcreteTaskReadService(context)
    service.get_task = MagicMock(return_value=SimpleNamespace(id="task-1"))

    readiness = service.get_completion_readiness("task-1")

    assert readiness.can_mark_done is False
    assert readiness.missing_requirements == [
        "attach at least one passing check or artifact",
        "resolve blocking dependencies",
        "close open waiting questions",
    ]


def test_next_task_filters_to_top_level_ready_or_in_progress_tasks() -> None:
    db = MagicMock()
    captured: dict[str, object] = {}

    def _capture(stmt):
        captured["stmt"] = stmt
        return None

    db.scalar = MagicMock(side_effect=_capture)
    context = ServiceContext(db=db, actor_type="human", actor_name="tester")

    service = ConcreteTaskReadService(context)
    assert service.next_task(project_id="proj-1") is None

    where_clause = captured["stmt"].whereclause
    assert isinstance(where_clause, BooleanClauseList)
    clauses = tuple(where_clause.clauses)
    assert any(
        isinstance(clause, BinaryExpression)
        and getattr(getattr(clause, "left", None), "name", None) == "parent_task_id"
        for clause in clauses
    )
    assert any(
        isinstance(clause, BinaryExpression)
        and getattr(getattr(clause, "left", None), "name", None) == "project_id"
        and getattr(getattr(clause, "right", None), "value", None) == "proj-1"
        for clause in clauses
    )

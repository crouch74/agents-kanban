from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from acp_core.services.base_service import ServiceContext
from acp_core.services.project_service import ProjectService


def test_get_board_view_excludes_cancelled_tasks() -> None:
    db = MagicMock()
    db.scalars = MagicMock(return_value=[])
    context = ServiceContext(db=db, actor_type="human", actor_name="tester")

    board = SimpleNamespace(id="board-1", name="Board", columns=[])
    project = SimpleNamespace(id="proj-1", board=board)
    service = ProjectService(context)
    service.get_project = MagicMock(return_value=project)
    service._repair_board_columns = MagicMock()

    captured = {}

    def _capture(stmt):
        captured["stmt"] = stmt
        return []

    context.db.scalars.side_effect = _capture

    result = service.get_board_view("proj-1")

    assert result.tasks == []
    where_clause = captured["stmt"].whereclause
    assert isinstance(where_clause, BooleanClauseList)
    clauses = tuple(where_clause.clauses)
    assert any(
        isinstance(clause, BinaryExpression)
        and getattr(getattr(clause, "left", None), "name", None) == "workflow_state"
        and getattr(getattr(clause, "right", None), "value", None) == "cancelled"
        for clause in clauses
    )

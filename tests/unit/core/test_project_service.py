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


def test_archive_project_marks_project_archived_and_records_event() -> None:
    db = MagicMock()
    context = ServiceContext(db=db, actor_type="system", actor_name="unit-tests")
    context.record_event = MagicMock()

    project = SimpleNamespace(id="proj-archive", archived=False)
    service = ProjectService(context)
    service.get_project = MagicMock(return_value=project)

    archived = service.archive_project("proj-archive")

    assert archived is project
    assert project.archived is True
    context.record_event.assert_called_once_with(
        entity_type="project",
        entity_id="proj-archive",
        event_type="project.archived",
        payload_json={"archived": True},
    )
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(project)


def test_archive_project_is_idempotent_when_already_archived() -> None:
    db = MagicMock()
    context = ServiceContext(db=db, actor_type="system", actor_name="unit-tests")
    context.record_event = MagicMock()

    project = SimpleNamespace(id="proj-archive", archived=True)
    service = ProjectService(context)
    service.get_project = MagicMock(return_value=project)

    archived = service.archive_project("proj-archive")

    assert archived is project
    assert project.archived is True
    context.record_event.assert_not_called()
    db.commit.assert_not_called()
    db.refresh.assert_not_called()

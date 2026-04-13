from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from acp_core.services.base_service import ServiceContext
from acp_core.services.system_service import DashboardService


def test_dashboard_excludes_archived_projects() -> None:
    db = MagicMock()
    context = ServiceContext(db=db, actor_type="system", actor_name="unit-tests")

    captured = {}

    def _scalars(statement):
        statement_sql = str(statement)
        if statement_sql.startswith("SELECT projects.id"):
            if "IS true" in statement_sql:
                return []
            captured["project_ids_statement"] = statement
            return ["active-1"]
        if statement_sql.startswith(
            "SELECT projects.name, projects.slug, projects.description, projects.archived, projects.settings_json, projects.diagnostics_json, projects.id, projects.created_at, projects.updated_at"
        ):
            captured["projects_statement"] = statement
            return [
                SimpleNamespace(
                    id="active-1",
                    name="Active project",
                    slug="active-project",
                    archived=False,
                    description="Active project description",
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                    updated_at=datetime(2026, 1, 1, tzinfo=UTC),
                )
            ]
        return []

    db.scalars = MagicMock(side_effect=_scalars)

    service = DashboardService(context)
    dashboard = service.get_dashboard()

    assert dashboard.projects[0].id == "active-1"
    where_clause = captured["projects_statement"].whereclause
    assert where_clause is not None
    assert str(where_clause).find("archived") >= 0
    where_clause_sql = str(where_clause.compile(compile_kwargs={"literal_binds": True}))
    assert "projects.archived is false" in where_clause_sql.lower()


def test_dashboard_running_sessions_only_include_active_projects() -> None:
    db = MagicMock()
    context = ServiceContext(db=db, actor_type="system", actor_name="unit-tests")

    captured = {}

    def _scalars(statement):
        statement_sql = str(statement)
        if "SELECT projects.id" in statement_sql and "FROM projects" in statement_sql:
            if "IS true" in statement_sql:
                return []
            return ["project-active", "project-archived"]
        if "SELECT projects.name, projects.slug" in statement_sql:
            captured["projects_statement"] = statement
            return [
                SimpleNamespace(
                    id="project-active",
                    name="Active project",
                    slug="active-project",
                    archived=False,
                    description="Active project description",
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                    updated_at=datetime(2026, 1, 1, tzinfo=UTC),
                )
            ]
        if "FROM agent_sessions" in statement_sql:
            captured["active_sessions_statement"] = statement
            return []
        return []

    db.scalars = MagicMock(side_effect=_scalars)

    service = DashboardService(context)
    service.get_dashboard()

    active_sessions_stmt = captured["active_sessions_statement"]
    assert captured.get("active_sessions_statement") is not None
    # ensure statement for active sessions includes in_ on non-archived project IDs
    project_ids_filter = "agent_sessions.project_id IN"
    assert project_ids_filter in str(active_sessions_stmt)


def test_dashboard_activity_log_skips_events_from_archived_projects() -> None:
    db = MagicMock()
    context = ServiceContext(db=db, actor_type="unit-tests", actor_name="system")

    captured = {}

    active_project_id = "project-active"
    archived_project_id = "project-archived"

    active_event = SimpleNamespace(
        id="event-active",
        actor_type="system",
        actor_name="unit-tests",
        entity_type="project",
        entity_id=active_project_id,
        event_type="project.created",
        payload_json={},
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        updated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    archived_event = SimpleNamespace(
        id="event-archived",
        actor_type="system",
        actor_name="unit-tests",
        entity_type="project",
        entity_id=archived_project_id,
        event_type="project.created",
        payload_json={},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    def _scalars(statement):
        statement_sql = str(statement)
        if "SELECT projects.id" in statement_sql and "FROM projects" in statement_sql:
            if "IS true" in statement_sql:
                return [archived_project_id]
            return [active_project_id, archived_project_id]
        if "SELECT projects.name, projects.slug" in statement_sql:
            return [
                SimpleNamespace(
                    id=active_project_id,
                    name="Active project",
                    slug="active-project",
                    archived=False,
                    description="Active project description",
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                    updated_at=datetime(2026, 1, 1, tzinfo=UTC),
                )
            ]
        if "FROM events" in statement_sql:
            return [active_event, archived_event]
        return []

    db.scalars = MagicMock(side_effect=_scalars)

    service = DashboardService(context)
    dashboard = service.get_dashboard()

    assert len(dashboard.recent_events) == 1
    assert dashboard.recent_events[0].entity_id == active_project_id

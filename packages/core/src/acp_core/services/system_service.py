from __future__ import annotations

from sqlalchemy import String, cast, delete, func, or_, select, text

from acp_core.logging import logger
from acp_core.models import Base, Event, Project, Task, TaskComment
from acp_core.schemas import (
    DashboardRead,
    EventRecord,
    ProjectSummary,
    PurgeDatabaseRead,
    SearchHit,
    SearchResults,
    ServiceStatusRead,
    SystemDiagnosticsRead,
)
from acp_core.settings import settings
from acp_core.services.base_service import ServiceContext


class EventService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_events(
        self,
        *,
        project_id: str | None = None,
        task_id: str | None = None,
        limit: int = 50,
    ) -> list[EventRecord]:
        stmt = select(Event).order_by(Event.created_at.desc()).limit(limit)
        if project_id is not None:
            stmt = stmt.where(cast(Event.payload_json, String).like(f'%"{project_id}"%'))
        if task_id is not None:
            stmt = stmt.where(cast(Event.payload_json, String).like(f'%"{task_id}"%'))
        return [EventRecord.model_validate(item) for item in self.context.db.scalars(stmt)]


class DashboardService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def get_dashboard(self) -> DashboardRead:
        projects = [ProjectSummary.model_validate(project) for project in self.context.db.scalars(
            select(Project).where(Project.archived.is_(False)).order_by(Project.created_at.desc()).limit(20)
        )]
        recent_events = [EventRecord.model_validate(event) for event in self.context.db.scalars(
            select(Event).order_by(Event.created_at.desc()).limit(30)
        )]
        raw_counts = self.context.db.execute(
            select(Task.workflow_state, func.count(Task.id)).group_by(Task.workflow_state)
        )
        task_counts = {row[0]: int(row[1]) for row in raw_counts}
        return DashboardRead(projects=projects, recent_events=recent_events, task_counts=task_counts)


class SearchService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def search(
        self,
        *,
        query: str,
        project_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> SearchResults:
        needle = query.strip()
        if not needle:
            return SearchResults(query=query, hits=[])
        like = f"%{needle}%"

        task_stmt = select(Task).where(or_(Task.title.ilike(like), Task.description.ilike(like)))
        if project_id:
            task_stmt = task_stmt.where(Task.project_id == project_id)
        if status:
            task_stmt = task_stmt.where(Task.workflow_state == status)
        task_stmt = task_stmt.order_by(Task.updated_at.desc()).limit(limit)
        task_hits = [
            SearchHit(
                entity_type="task",
                entity_id=task.id,
                project_id=task.project_id,
                title=task.title,
                snippet=(task.description or task.title)[:240],
                secondary=task.workflow_state,
                created_at=task.updated_at,
            )
            for task in self.context.db.scalars(task_stmt)
        ]

        event_stmt = select(Event).where(cast(Event.payload_json, String).ilike(like)).order_by(Event.created_at.desc()).limit(limit)
        event_hits = [
            SearchHit(
                entity_type="event",
                entity_id=event.id,
                project_id=(event.payload_json.get("project_id") if isinstance(event.payload_json, dict) else None),
                title=event.event_type,
                snippet=str(event.payload_json)[:240],
                secondary=event.actor_name,
                created_at=event.created_at,
            )
            for event in self.context.db.scalars(event_stmt)
        ]

        hits = (task_hits + event_hits)[:limit]
        return SearchResults(query=query, hits=hits)


class SystemAdminService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def get_diagnostics(self) -> SystemDiagnosticsRead:
        row_counts = {
            "projects": int(self.context.db.scalar(select(func.count(Project.id))) or 0),
            "tasks": int(self.context.db.scalar(select(func.count(Task.id))) or 0),
            "task_comments": int(self.context.db.scalar(select(func.count(TaskComment.id))) or 0),
            "events": int(self.context.db.scalar(select(func.count(Event.id))) or 0),
        }
        return SystemDiagnosticsRead(
            app_name=settings.app_name,
            environment=settings.app_env,
            services={
                "api": ServiceStatusRead(status="ok", detail="FastAPI service online"),
                "database": ServiceStatusRead(status="ok", detail="SQLite connection healthy"),
                "mcp": ServiceStatusRead(status="external", detail="Served as an external task-board endpoint"),
            },
            paths={
                "runtime_home": str(settings.runtime_home),
                "database_path": str(settings.database_path),
                "artifacts_path": str(settings.artifacts_dir),
                "logs_path": str(settings.logs_dir),
            },
            row_counts=row_counts,
        )

    def purge_database(self) -> PurgeDatabaseRead:
        tables = list(reversed(Base.metadata.sorted_tables))
        rows_deleted = 0
        try:
            self.context.db.execute(text("PRAGMA foreign_keys=OFF"))
            for table in tables:
                rows_deleted += int(self.context.db.scalar(select(func.count()).select_from(table)) or 0)
                self.context.db.execute(delete(table))
            self.context.db.commit()
            logger.info("🧹 database purged", rows_deleted=rows_deleted, purged_tables=len(tables))
            return PurgeDatabaseRead(
                status="ok",
                purged_tables=len(tables),
                rows_deleted=rows_deleted,
                database_path=str(settings.database_path),
            )
        except Exception as exc:
            self.context.db.rollback()
            logger.exception("⚠️ failed to purge database", error=str(exc))
            raise ValueError(f"Failed to purge database: {exc}") from exc
        finally:
            self.context.db.execute(text("PRAGMA foreign_keys=ON"))

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from acp_core.models import Event
from acp_core.schemas import EventRecord, RepositoryRead, WorktreeRead
from acp_core.services.base_service import ServiceContext
from acp_core.services.repository_service import RepositoryService
from acp_core.services.system_service import DiagnosticsService, SearchService
from acp_core.services.worktree_service import WorktreeService

from acp_mcp_server.idempotency import run_read_operation


def context_search(
    query: str, project_id: str | None = None, limit: int = 20
) -> dict[str, Any]:
    return run_read_operation(
        lambda context: SearchService(context)
        .search(query=query, project_id=project_id, limit=limit)
        .model_dump()
    )


def diagnostics_get() -> dict[str, Any]:
    return run_read_operation(
        lambda context: DiagnosticsService(context).get_diagnostics().model_dump(),
        actor_type="system",
        actor_name="mcp",
    )


def repo_inventory_resource(project_id: str) -> dict[str, Any]:
    def _load_inventory(context: ServiceContext) -> dict[str, Any]:
        repositories = RepositoryService(context).list_repositories(
            project_id=project_id
        )
        worktrees = WorktreeService(context).list_worktrees(project_id=project_id)
        return {
            "repositories": [
                RepositoryRead.model_validate(item).model_dump()
                for item in repositories
            ],
            "worktrees": [
                WorktreeRead.model_validate(item).model_dump() for item in worktrees
            ],
        }

    return run_read_operation(_load_inventory)


def diagnostics_resource() -> dict[str, Any]:
    return diagnostics_get()


def recent_events_resource(
    project_id: str | None = None, task_id: str | None = None
) -> list[dict[str, Any]]:
    def _load_events(context: ServiceContext) -> list[dict[str, Any]]:
        stmt = select(Event).order_by(Event.created_at.desc()).limit(30)
        if project_id is not None:
            stmt = stmt.where(
                (Event.entity_type == "project") & (Event.entity_id == project_id)
            )
        if task_id is not None:
            stmt = stmt.where(
                (Event.entity_type == "task") & (Event.entity_id == task_id)
            )
        return [
            EventRecord.model_validate(item).model_dump()
            for item in context.db.scalars(stmt)
        ]

    return run_read_operation(_load_events)

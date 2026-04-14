from __future__ import annotations

from typing import Any

from acp_core.services.system_service import DashboardService, EventService, SearchService

from acp_mcp_server.idempotency import run_read_operation


def context_search(
    query: str,
    project_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    return run_read_operation(
        lambda context: SearchService(context)
        .search(query=query, project_id=project_id, status=status, limit=limit)
        .model_dump()
    )


def dashboard_get() -> dict[str, Any]:
    return run_read_operation(
        lambda context: DashboardService(context).get_dashboard().model_dump(),
        actor_type="system",
        actor_name="mcp",
    )


def recent_events_resource(
    project_id: str | None = None, task_id: str | None = None
) -> list[dict[str, Any]]:
    return run_read_operation(
        lambda context: [
            item.model_dump()
            for item in EventService(context).list_events(project_id=project_id, task_id=task_id, limit=30)
        ]
    )

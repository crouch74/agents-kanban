from __future__ import annotations

from typing import Any

from acp_core.schemas import ProjectCreate, ProjectSummary
from acp_core.services.project_service import ProjectService

from acp_mcp_server.idempotency import (
    IDEMPOTENT_EVENT_TYPES,
    run_idempotent_write,
    run_read_operation,
)


def project_list() -> list[dict[str, Any]]:
    return run_read_operation(
        lambda context: [
            ProjectSummary.model_validate(item).model_dump()
            for item in ProjectService(context).list_projects()
        ]
    )


def project_create(
    name: str,
    description: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["project_create"],
        client_request_id=client_request_id,
        write_fn=lambda context: ProjectService(context).create_project(
            ProjectCreate(name=name, description=description)
        ),
        serialize_fn=lambda _context, project: ProjectSummary.model_validate(
            project
        ).model_dump(),
    )


def project_get(project_id: str) -> dict[str, Any]:
    return run_read_operation(
        lambda context: ProjectService(context)
        .get_project_overview(project_id)
        .model_dump()
    )


def board_get(project_id: str) -> dict[str, Any]:
    return run_read_operation(
        lambda context: ProjectService(context).get_board_view(project_id).model_dump()
    )


def project_board_resource(project_id: str) -> dict[str, Any]:
    return board_get(project_id)

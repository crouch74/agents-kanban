from __future__ import annotations

from typing import Any

from acp_core.schemas import (
    ProjectBootstrapCreate,
    ProjectCreate,
    ProjectSummary,
    StackPreset,
)
from acp_core.services.bootstrap_service import BootstrapService
from acp_core.services.project_service import ProjectService

from acp_mcp_server.idempotency import (
    IDEMPOTENT_EVENT_TYPES,
    run_idempotent_write,
    run_read_operation,
)


def project_list() -> list[ProjectSummary]:
    return run_read_operation(
        lambda context: [
            ProjectSummary.model_validate(item)
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


def project_bootstrap(
    name: str,
    repo_path: str,
    stack_preset: str,
    initial_prompt: str,
    description: str | None = None,
    initialize_repo: bool = False,
    stack_notes: str | None = None,
    use_worktree: bool = False,
    confirm_existing_repo: bool = False,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["project_bootstrap"],
        client_request_id=client_request_id,
        write_fn=lambda context: BootstrapService(context).bootstrap_project(
            ProjectBootstrapCreate(
                name=name,
                description=description,
                repo_path=repo_path,
                initialize_repo=initialize_repo,
                stack_preset=StackPreset(stack_preset),
                stack_notes=stack_notes,
                initial_prompt=initial_prompt,
                use_worktree=use_worktree,
                confirm_existing_repo=confirm_existing_repo,
            )
        ),
        serialize_fn=lambda _context, result: result.model_dump(),
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

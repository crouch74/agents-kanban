from __future__ import annotations

from typing import Any

from acp_core.schemas import WorktreeCreate, WorktreeRead
from acp_core.services.worktree_service import WorktreeHygieneService, WorktreeService

from acp_mcp_server.idempotency import (
    IDEMPOTENT_EVENT_TYPES,
    run_idempotent_write,
    run_read_operation,
)


def worktree_create(
    repository_id: str,
    task_id: str | None = None,
    label: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["worktree_create"],
        client_request_id=client_request_id,
        write_fn=lambda context: WorktreeService(context).create_worktree(
            WorktreeCreate(repository_id=repository_id, task_id=task_id, label=label)
        ),
        serialize_fn=lambda _context, worktree: WorktreeRead.model_validate(
            worktree
        ).model_dump(),
    )


def worktree_list(project_id: str | None = None) -> list[dict[str, Any]]:
    return run_read_operation(
        lambda context: [
            WorktreeRead.model_validate(item).model_dump()
            for item in WorktreeService(context).list_worktrees(project_id=project_id)
        ]
    )


def worktree_get(worktree_id: str) -> dict[str, Any]:
    return run_read_operation(
        lambda context: WorktreeRead.model_validate(
            WorktreeService(context).get_worktree(worktree_id)
        ).model_dump()
    )


def worktree_hygiene_list(
    project_id: str | None = None, task_id: str | None = None
) -> list[dict[str, Any]]:
    return run_read_operation(
        lambda context: [
            item.model_dump()
            for item in WorktreeHygieneService(context).list_issues(
                project_id=project_id, task_id=task_id
            )
        ]
    )

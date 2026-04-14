from __future__ import annotations

from typing import Any

from acp_core.enums import AuthorType, TaskPriority, WorkflowState
from acp_core.schemas import TaskCommentCreate, TaskCommentRead, TaskCreate, TaskPatch, TaskRead
from acp_core.services.task_service import TaskService, comment_to_read, task_to_read

from acp_mcp_server.idempotency import (
    IDEMPOTENT_EVENT_TYPES,
    run_idempotent_write,
    run_read_operation,
)


def task_get(task_id: str) -> dict[str, Any]:
    return run_read_operation(
        lambda context: TaskService(context).get_task_detail(task_id).model_dump()
    )


def task_create(
    project_id: str,
    title: str,
    description: str | None = None,
    priority: str = TaskPriority.MEDIUM.value,
    assignee: str | None = None,
    source: str | None = "mcp",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_create"],
        client_request_id=client_request_id,
        write_fn=lambda context: TaskService(context).create_task(
            TaskCreate(
                project_id=project_id,
                title=title,
                description=description,
                priority=priority,
                assignee=assignee,
                source=source,
            )
        ),
        serialize_fn=lambda _context, task: TaskRead(**task_to_read(task)).model_dump(),
    )


def task_update(
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    workflow_state: WorkflowState | None = None,
    board_column_id: str | None = None,
    priority: TaskPriority | None = None,
    assignee: str | None = None,
    tags: list[str] | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_update"],
        client_request_id=client_request_id,
        write_fn=lambda context: TaskService(context).patch_task(
            task_id,
            TaskPatch(
                title=title,
                description=description,
                workflow_state=workflow_state,
                board_column_id=board_column_id,
                priority=priority,
                assignee=assignee,
                tags=tags,
            ),
        ),
        serialize_fn=lambda _context, task: TaskRead(**task_to_read(task)).model_dump(),
    )


def task_comment_add(
    task_id: str,
    author_name: str,
    body: str,
    author_type: str | AuthorType = AuthorType.AGENT.value,
    source: str | None = "mcp",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_comment_add"],
        client_request_id=client_request_id,
        actor_name=author_name,
        write_fn=lambda context: TaskService(context).add_comment(
            task_id,
            TaskCommentCreate(
                author_type=author_type,
                author_name=author_name,
                source=source,
                body=body,
            ),
        ),
        serialize_fn=lambda _context, comment: TaskCommentRead.model_validate(comment_to_read(comment)).model_dump(),
    )


def task_list(
    project_id: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    return run_read_operation(
        lambda context: [
            TaskRead(**task_to_read(task)).model_dump()
            for task in TaskService(context).list_tasks(project_id=project_id, status=status, q=q)
        ]
    )


def task_detail_resource(task_id: str) -> dict[str, Any]:
    return task_get(task_id)

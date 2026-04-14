from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select

from acp_core.models import Event, Project, Task, TaskComment
from acp_core.schemas import ProjectSummary, TaskCommentRead, TaskRead
from acp_core.services.base_service import ServiceContext
from acp_core.services.task_service import comment_to_read, task_to_read

from acp_mcp_server.runtime_context import service_context

IDEMPOTENT_EVENT_TYPES: dict[str, str] = {
    "project_create": "project.created",
    "task_create": "task.created",
    "task_update": "task.updated",
    "task_comment_add": "task.comment_added",
}


def _load_idempotent_result(context: ServiceContext, event: Event) -> dict[str, Any]:
    if event.event_type == "project.created":
        project = context.db.get(Project, event.entity_id)
        if project is None:
            raise ValueError("Project not found")
        return ProjectSummary.model_validate(project).model_dump()
    if event.event_type in {"task.created", "task.updated"}:
        task = context.db.get(Task, event.entity_id)
        if task is None:
            raise ValueError("Task not found")
        return TaskRead(**task_to_read(task)).model_dump()
    if event.event_type == "task.comment_added":
        comment = context.db.get(TaskComment, event.entity_id)
        if comment is None:
            raise ValueError("Task comment not found")
        return TaskCommentRead.model_validate(comment_to_read(comment)).model_dump()
    raise ValueError(f"Unsupported idempotent event type: {event.event_type}")


def replay_if_exists(
    context: ServiceContext, event_type: str, client_request_id: str | None
) -> dict[str, Any] | None:
    if not client_request_id:
        return None
    event = context.db.scalar(
        select(Event)
        .where(
            Event.correlation_id == client_request_id, Event.event_type == event_type
        )
        .order_by(Event.created_at.desc())
    )
    if event is None:
        return None
    return _load_idempotent_result(context, event)


def run_read_operation(
    read_fn: Callable[[ServiceContext], Any],
    *,
    actor_type: str = "agent",
    actor_name: str = "mcp",
) -> Any:
    with service_context(actor_type=actor_type, actor_name=actor_name) as context:
        return read_fn(context)


def run_idempotent_write(
    *,
    event_type: str,
    client_request_id: str | None,
    write_fn: Callable[[ServiceContext], Any],
    serialize_fn: Callable[[ServiceContext, Any], dict[str, Any]],
    actor_type: str = "agent",
    actor_name: str = "mcp",
) -> dict[str, Any]:
    with service_context(
        actor_type=actor_type, actor_name=actor_name, correlation_id=client_request_id
    ) as context:
        replay = replay_if_exists(context, event_type, client_request_id)
        if replay is not None:
            return replay
        result = write_fn(context)
        return serialize_fn(context, result)

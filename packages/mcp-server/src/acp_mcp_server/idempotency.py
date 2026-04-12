from __future__ import annotations

from typing import Any, Callable

from sqlalchemy import select

from acp_core.models import (
    AgentSession,
    Event,
    TaskArtifact,
    TaskCheck,
    TaskComment,
    TaskDependency,
)
from acp_core.schemas import (
    AgentSessionRead,
    ProjectSummary,
    TaskRead,
    WaitingQuestionRead,
    WorktreeRead,
)
from acp_core.services.base_service import ServiceContext
from acp_core.services.project_service import ProjectService
from acp_core.services.task_service import TaskService
from acp_core.services.waiting_service import WaitingService
from acp_core.services.worktree_service import WorktreeService

from acp_mcp_server.runtime_context import service_context
from acp_mcp_server.serializers import (
    _serialize_bootstrap_result,
    _serialize_task_artifact,
    _serialize_task_check,
    _serialize_task_comment,
    _serialize_task_dependency,
)

IDEMPOTENT_EVENT_TYPES: dict[str, str] = {
    "project_create": "project.created",
    "project_bootstrap": "project.bootstrapped",
    "task_create": "task.created",
    "subtask_create": "task.created",
    "task_update": "task.updated",
    "task_claim": "task.claimed",
    "task_comment_add": "task.comment_added",
    "task_check_add": "task.check_added",
    "task_artifact_add": "task.artifact_added",
    "task_dependency_add": "task.dependency_added",
    "session_spawn": "session.spawned",
    "session_follow_up": "session.follow_up_spawned",
    "question_open": "waiting_question.opened",
    "worktree_create": "worktree.created",
}


def _load_idempotent_result(context: ServiceContext, event: Event) -> dict[str, Any]:
    event_type = event.event_type
    entity_id = event.entity_id
    if event_type == "project.created":
        return ProjectSummary.model_validate(
            ProjectService(context).get_project(entity_id)
        ).model_dump()
    if event_type == "project.bootstrapped":
        return _serialize_bootstrap_result(context, event)
    if event_type in {"task.created", "task.updated", "task.claimed"}:
        return TaskRead.model_validate(
            TaskService(context).get_task(entity_id)
        ).model_dump()
    if event_type == "task.comment_added":
        comment = context.db.get(TaskComment, entity_id)
        if comment is None:
            raise ValueError("Task comment not found")
        return _serialize_task_comment(comment)
    if event_type == "task.check_added":
        check = context.db.get(TaskCheck, entity_id)
        if check is None:
            raise ValueError("Task check not found")
        return _serialize_task_check(check)
    if event_type == "task.artifact_added":
        artifact = context.db.get(TaskArtifact, entity_id)
        if artifact is None:
            raise ValueError("Task artifact not found")
        return _serialize_task_artifact(artifact)
    if event_type == "task.dependency_added":
        dependency = context.db.get(TaskDependency, entity_id)
        if dependency is None:
            raise ValueError("Task dependency not found")
        return _serialize_task_dependency(dependency)
    if event_type in {"session.spawned", "session.follow_up_spawned"}:
        session = context.db.get(AgentSession, entity_id)
        if session is None:
            raise ValueError("Session not found")
        return AgentSessionRead.model_validate(session).model_dump()
    if event_type == "waiting_question.opened":
        return WaitingQuestionRead.model_validate(
            WaitingService(context).get_question(entity_id)
        ).model_dump()
    if event_type == "worktree.created":
        return WorktreeRead.model_validate(
            WorktreeService(context).get_worktree(entity_id)
        ).model_dump()
    raise ValueError(f"Unsupported idempotent event type: {event_type}")


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

from __future__ import annotations

from typing import Any

from acp_core.schemas import (
    TaskArtifactCreate,
    TaskCheckCreate,
    TaskCommentCreate,
    TaskCreate,
    TaskDependencyCreate,
    TaskPatch,
    TaskRead,
)
from acp_core.services.base_service import ServiceContext
from acp_core.services.task_service import TaskService

from acp_mcp_server.idempotency import (
    IDEMPOTENT_EVENT_TYPES,
    run_idempotent_write,
    run_read_operation,
)
from acp_mcp_server.serializers import (
    _serialize_task_artifact,
    _serialize_task_check,
    _serialize_task_comment,
    _serialize_task_dependency,
)


def task_get(task_id: str) -> dict[str, Any]:
    return run_read_operation(
        lambda context: TaskService(context).get_task_detail(task_id).model_dump()
    )


def task_create(
    project_id: str,
    title: str,
    description: str | None = None,
    priority: str = "medium",
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
            )
        ),
        serialize_fn=lambda _context, task: TaskRead.model_validate(task).model_dump(),
    )


def subtask_create(
    parent_task_id: str,
    title: str,
    description: str | None = None,
    priority: str = "medium",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    def _create_subtask(context: ServiceContext) -> Any:
        parent = TaskService(context).get_task(parent_task_id)
        return TaskService(context).create_task(
            TaskCreate(
                project_id=parent.project_id,
                title=title,
                description=description,
                priority=priority,
                parent_task_id=parent_task_id,
            )
        )

    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["subtask_create"],
        client_request_id=client_request_id,
        write_fn=_create_subtask,
        serialize_fn=lambda _context, task: TaskRead.model_validate(task).model_dump(),
    )


def task_update(
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    workflow_state: str | None = None,
    blocked_reason: str | None = None,
    waiting_for_human: bool | None = None,
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
                blocked_reason=blocked_reason,
                waiting_for_human=waiting_for_human,
            ),
        ),
        serialize_fn=lambda _context, task: TaskRead.model_validate(task).model_dump(),
    )


def task_claim(
    task_id: str,
    actor_name: str,
    session_id: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_claim"],
        client_request_id=client_request_id,
        actor_name=actor_name,
        write_fn=lambda context: TaskService(context).claim_task(
            task_id, actor_name=actor_name, session_id=session_id
        ),
        serialize_fn=lambda _context, task: TaskRead.model_validate(task).model_dump(),
    )


def task_comment_add(
    task_id: str,
    author_name: str,
    body: str,
    author_type: str = "agent",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_comment_add"],
        client_request_id=client_request_id,
        actor_name=author_name,
        write_fn=lambda context: TaskService(context).add_comment(
            task_id,
            TaskCommentCreate(
                author_type=author_type, author_name=author_name, body=body
            ),
        ),
        serialize_fn=lambda _context, comment: _serialize_task_comment(comment),
    )


def task_check_add(
    task_id: str,
    check_type: str,
    status: str,
    summary: str,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_check_add"],
        client_request_id=client_request_id,
        write_fn=lambda context: TaskService(context).add_check(
            task_id,
            TaskCheckCreate(check_type=check_type, status=status, summary=summary),
        ),
        serialize_fn=lambda _context, check: _serialize_task_check(check),
    )


def task_artifact_add(
    task_id: str,
    artifact_type: str,
    name: str,
    uri: str,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_artifact_add"],
        client_request_id=client_request_id,
        write_fn=lambda context: TaskService(context).add_artifact(
            task_id,
            TaskArtifactCreate(artifact_type=artifact_type, name=name, uri=uri),
        ),
        serialize_fn=lambda _context, artifact: _serialize_task_artifact(artifact),
    )


def task_next(project_id: str | None = None) -> dict[str, Any] | None:
    return run_read_operation(
        lambda context: (
            TaskRead.model_validate(task).model_dump()
            if (task := TaskService(context).next_task(project_id=project_id))
            else None
        )
    )


def task_dependencies_get(task_id: str) -> list[dict[str, Any]]:
    return run_read_operation(
        lambda context: [
            item.model_dump() for item in TaskService(context).get_dependencies(task_id)
        ]
    )


def task_dependency_add(
    task_id: str,
    depends_on_task_id: str,
    relationship_type: str = "blocks",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_dependency_add"],
        client_request_id=client_request_id,
        write_fn=lambda context: TaskService(context).add_dependency(
            task_id,
            TaskDependencyCreate(
                depends_on_task_id=depends_on_task_id,
                relationship_type=relationship_type,
            ),
        ),
        serialize_fn=lambda _context, dependency: _serialize_task_dependency(
            dependency
        ),
    )


def task_completion_readiness(task_id: str) -> dict[str, Any]:
    return run_read_operation(
        lambda context: TaskService(context)
        .get_completion_readiness(task_id)
        .model_dump()
    )


def task_detail_resource(task_id: str) -> dict[str, Any]:
    return task_get(task_id)


def task_completion_resource(task_id: str) -> dict[str, Any]:
    return task_completion_readiness(task_id)

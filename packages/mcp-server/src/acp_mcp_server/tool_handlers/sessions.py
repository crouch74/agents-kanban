from __future__ import annotations

from typing import Any

from acp_core.schemas import (
    AgentSessionCreate,
    AgentSessionFollowUpCreate,
    AgentSessionRead,
    RuntimeLaunchSpecCreate,
)
from acp_core.services.session_service import SessionService

from acp_mcp_server.idempotency import (
    IDEMPOTENT_EVENT_TYPES,
    run_idempotent_write,
    run_read_operation,
)


def session_spawn(
    task_id: str,
    profile: str = "executor",
    repository_id: str | None = None,
    worktree_id: str | None = None,
    launch_input: dict[str, Any] | None = None,
    launch_spec: dict[str, Any] | None = None,
    command: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["session_spawn"],
        client_request_id=client_request_id,
        write_fn=lambda context: SessionService(context).spawn_session(
            AgentSessionCreate(
                task_id=task_id,
                profile=profile,
                repository_id=repository_id,
                worktree_id=worktree_id,
                launch_input=launch_input,
                launch_spec=RuntimeLaunchSpecCreate.model_validate(launch_spec) if launch_spec else None,
                command=command,
            )
        ),
        serialize_fn=lambda _context, session: AgentSessionRead.model_validate(
            session
        ).model_dump(),
    )


def session_follow_up(
    session_id: str,
    profile: str = "verifier",
    follow_up_type: str | None = None,
    reuse_worktree: bool = True,
    reuse_repository: bool = True,
    launch_input: dict[str, Any] | None = None,
    launch_spec: dict[str, Any] | None = None,
    command: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["session_follow_up"],
        client_request_id=client_request_id,
        write_fn=lambda context: SessionService(context).spawn_follow_up_session(
            session_id,
            AgentSessionFollowUpCreate(
                profile=profile,
                follow_up_type=follow_up_type,
                reuse_worktree=reuse_worktree,
                reuse_repository=reuse_repository,
                launch_input=launch_input,
                launch_spec=RuntimeLaunchSpecCreate.model_validate(launch_spec) if launch_spec else None,
                command=command,
            ),
        ),
        serialize_fn=lambda _context, session: AgentSessionRead.model_validate(
            session
        ).model_dump(),
    )


def session_status(session_id: str) -> dict[str, Any]:
    return run_read_operation(
        lambda context: AgentSessionRead.model_validate(
            SessionService(context).refresh_session_status(session_id)
        ).model_dump()
    )


def session_tail(session_id: str, lines: int = 80) -> dict[str, Any]:
    return run_read_operation(
        lambda context: SessionService(context)
        .tail_session(session_id, lines=lines)
        .model_dump()
    )


def session_list(
    project_id: str | None = None, task_id: str | None = None
) -> list[dict[str, Any]]:
    return run_read_operation(
        lambda context: [
            AgentSessionRead.model_validate(item).model_dump()
            for item in SessionService(context).list_sessions(
                project_id=project_id, task_id=task_id
            )
        ]
    )


def session_timeline_resource(session_id: str) -> dict[str, Any]:
    return run_read_operation(
        lambda context: SessionService(context)
        .get_session_timeline(session_id)
        .model_dump()
    )

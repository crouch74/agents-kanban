from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Any

from sqlalchemy import select

from acp_core.db import SessionLocal, init_db
from acp_core.models import AgentSession, Event, TaskCheck, TaskComment, Worktree
from acp_core.schemas import (
    AgentSessionCreate,
    AgentSessionRead,
    EventRecord,
    ProjectCreate,
    ProjectSummary,
    RepositoryRead,
    TaskCheckCreate,
    TaskCommentCreate,
    TaskCreate,
    TaskPatch,
    TaskRead,
    WaitingQuestionCreate,
    WaitingQuestionDetail,
    WaitingQuestionRead,
    WorktreeCreate,
    WorktreeRead,
)
from acp_core.services import (
    ProjectService,
    RepositoryService,
    SearchService,
    ServiceContext,
    SessionService,
    TaskService,
    WaitingService,
    WorktreeService,
)


_BOOTSTRAP_LOCK = Lock()
_BOOTSTRAPPED = False


def ensure_runtime_ready() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    with _BOOTSTRAP_LOCK:
        if _BOOTSTRAPPED:
            return
        init_db()
        _BOOTSTRAPPED = True


@contextmanager
def service_context(
    actor_type: str = "agent",
    actor_name: str = "mcp",
    correlation_id: str | None = None,
) -> ServiceContext:
    ensure_runtime_ready()
    db = SessionLocal()
    try:
        yield ServiceContext(
            db=db,
            actor_type=actor_type,
            actor_name=actor_name,
            correlation_id=correlation_id,
        )
    finally:
        db.close()


def _serialize_task_comment(comment: TaskComment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "task_id": comment.task_id,
        "author_type": comment.author_type,
        "author_name": comment.author_name,
        "body": comment.body,
        "metadata_json": comment.metadata_json,
        "created_at": comment.created_at,
    }


def _serialize_task_check(check: TaskCheck) -> dict[str, Any]:
    return {
        "id": check.id,
        "task_id": check.task_id,
        "check_type": check.check_type,
        "status": check.status,
        "summary": check.summary,
        "payload_json": check.payload_json,
        "created_at": check.created_at,
    }


def _load_idempotent_result(context: ServiceContext, event_type: str, entity_id: str) -> dict[str, Any]:
    if event_type == "project.created":
        return ProjectSummary.model_validate(ProjectService(context).get_project(entity_id)).model_dump()
    if event_type in {"task.created", "task.updated", "task.claimed"}:
        return TaskRead.model_validate(TaskService(context).get_task(entity_id)).model_dump()
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
    if event_type == "session.spawned":
        session = context.db.get(AgentSession, entity_id)
        if session is None:
            raise ValueError("Session not found")
        return AgentSessionRead.model_validate(session).model_dump()
    if event_type == "waiting_question.opened":
        return WaitingQuestionRead.model_validate(WaitingService(context).get_question(entity_id)).model_dump()
    if event_type == "worktree.created":
        return WorktreeRead.model_validate(WorktreeService(context).get_worktree(entity_id)).model_dump()
    raise ValueError(f"Unsupported idempotent event type: {event_type}")


def _replay_if_exists(context: ServiceContext, event_type: str, client_request_id: str | None) -> dict[str, Any] | None:
    if not client_request_id:
        return None
    event = context.db.scalar(
        select(Event)
        .where(Event.correlation_id == client_request_id, Event.event_type == event_type)
        .order_by(Event.created_at.desc())
    )
    if event is None:
        return None
    return _load_idempotent_result(context, event_type, event.entity_id)


def project_list() -> list[ProjectSummary]:
    with service_context() as context:
        return [ProjectSummary.model_validate(item) for item in ProjectService(context).list_projects()]


def project_create(
    name: str,
    description: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "project.created", client_request_id)
        if replay is not None:
            return replay
        project = ProjectService(context).create_project(ProjectCreate(name=name, description=description))
        return ProjectSummary.model_validate(project).model_dump()


def project_get(project_id: str) -> dict[str, Any]:
    with service_context() as context:
        overview = ProjectService(context).get_project_overview(project_id)
        return overview.model_dump()


def board_get(project_id: str) -> dict[str, Any]:
    with service_context() as context:
        board = ProjectService(context).get_board_view(project_id)
        return board.model_dump()


def task_get(task_id: str) -> dict[str, Any]:
    with service_context() as context:
        detail = TaskService(context).get_task_detail(task_id)
        return detail.model_dump()


def task_create(
    project_id: str,
    title: str,
    description: str | None = None,
    priority: str = "medium",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "task.created", client_request_id)
        if replay is not None:
            return replay
        task = TaskService(context).create_task(
            TaskCreate(project_id=project_id, title=title, description=description, priority=priority)
        )
        return TaskRead.model_validate(task).model_dump()


def subtask_create(
    parent_task_id: str,
    title: str,
    description: str | None = None,
    priority: str = "medium",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "task.created", client_request_id)
        if replay is not None:
            return replay
        parent = TaskService(context).get_task(parent_task_id)
        task = TaskService(context).create_task(
            TaskCreate(
                project_id=parent.project_id,
                title=title,
                description=description,
                priority=priority,
                parent_task_id=parent_task_id,
            )
        )
        return TaskRead.model_validate(task).model_dump()


def task_update(
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    workflow_state: str | None = None,
    blocked_reason: str | None = None,
    waiting_for_human: bool | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "task.updated", client_request_id)
        if replay is not None:
            return replay
        task = TaskService(context).patch_task(
            task_id,
            TaskPatch(
                title=title,
                description=description,
                workflow_state=workflow_state,
                blocked_reason=blocked_reason,
                waiting_for_human=waiting_for_human,
            ),
        )
        return TaskRead.model_validate(task).model_dump()


def task_claim(
    task_id: str,
    actor_name: str,
    session_id: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(actor_name=actor_name, correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "task.claimed", client_request_id)
        if replay is not None:
            return replay
        task = TaskService(context).claim_task(task_id, actor_name=actor_name, session_id=session_id)
        return TaskRead.model_validate(task).model_dump()


def task_comment_add(
    task_id: str,
    author_name: str,
    body: str,
    author_type: str = "agent",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(actor_name=author_name, correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "task.comment_added", client_request_id)
        if replay is not None:
            return replay
        comment = TaskService(context).add_comment(
            task_id,
            TaskCommentCreate(author_type=author_type, author_name=author_name, body=body),
        )
        return _serialize_task_comment(comment)


def task_check_add(
    task_id: str,
    check_type: str,
    status: str,
    summary: str,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "task.check_added", client_request_id)
        if replay is not None:
            return replay
        check = TaskService(context).add_check(
            task_id,
            TaskCheckCreate(check_type=check_type, status=status, summary=summary),
        )
        return _serialize_task_check(check)


def task_next(project_id: str | None = None) -> dict[str, Any] | None:
    with service_context() as context:
        task = TaskService(context).next_task(project_id=project_id)
        return TaskRead.model_validate(task).model_dump() if task else None


def task_dependencies_get(task_id: str) -> list[dict[str, Any]]:
    with service_context() as context:
        dependencies = TaskService(context).get_dependencies(task_id)
        return [item.model_dump() for item in dependencies]


def session_spawn(
    task_id: str,
    profile: str = "executor",
    repository_id: str | None = None,
    worktree_id: str | None = None,
    command: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "session.spawned", client_request_id)
        if replay is not None:
            return replay
        session = SessionService(context).spawn_session(
            AgentSessionCreate(
                task_id=task_id,
                profile=profile,
                repository_id=repository_id,
                worktree_id=worktree_id,
                command=command,
            )
        )
        return AgentSessionRead.model_validate(session).model_dump()


def session_status(session_id: str) -> dict[str, Any]:
    with service_context() as context:
        session = SessionService(context).refresh_session_status(session_id)
        return AgentSessionRead.model_validate(session).model_dump()


def session_tail(session_id: str, lines: int = 80) -> dict[str, Any]:
    with service_context() as context:
        tail = SessionService(context).tail_session(session_id, lines=lines)
        return tail.model_dump()


def session_list(project_id: str | None = None, task_id: str | None = None) -> list[dict[str, Any]]:
    with service_context() as context:
        sessions = SessionService(context).list_sessions(project_id=project_id, task_id=task_id)
        return [AgentSessionRead.model_validate(item).model_dump() for item in sessions]


def question_open(
    task_id: str,
    prompt: str,
    session_id: str | None = None,
    blocked_reason: str | None = None,
    urgency: str | None = None,
    options_json: list[dict[str, Any]] | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "waiting_question.opened", client_request_id)
        if replay is not None:
            return replay
        question = WaitingService(context).open_question(
            WaitingQuestionCreate(
                task_id=task_id,
                session_id=session_id,
                prompt=prompt,
                blocked_reason=blocked_reason,
                urgency=urgency,
                options_json=options_json or [],
            )
        )
        return WaitingQuestionRead.model_validate(question).model_dump()


def question_answer_get(question_id: str) -> dict[str, Any]:
    with service_context() as context:
        question = WaitingService(context).get_question_detail(question_id)
        return question.model_dump()


def worktree_create(
    repository_id: str,
    task_id: str | None = None,
    label: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    with service_context(correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, "worktree.created", client_request_id)
        if replay is not None:
            return replay
        worktree = WorktreeService(context).create_worktree(
            WorktreeCreate(repository_id=repository_id, task_id=task_id, label=label)
        )
        return WorktreeRead.model_validate(worktree).model_dump()


def worktree_list(project_id: str | None = None) -> list[dict[str, Any]]:
    with service_context() as context:
        worktrees = WorktreeService(context).list_worktrees(project_id=project_id)
        return [WorktreeRead.model_validate(item).model_dump() for item in worktrees]


def worktree_get(worktree_id: str) -> dict[str, Any]:
    with service_context() as context:
        worktree = WorktreeService(context).get_worktree(worktree_id)
        return WorktreeRead.model_validate(worktree).model_dump()


def context_search(query: str, project_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    with service_context() as context:
        results = SearchService(context).search(query=query, project_id=project_id, limit=limit)
        return results.model_dump()


def project_board_resource(project_id: str) -> dict[str, Any]:
    return board_get(project_id)


def task_detail_resource(task_id: str) -> dict[str, Any]:
    return task_get(task_id)


def session_timeline_resource(session_id: str) -> dict[str, Any]:
    with service_context() as context:
        timeline = SessionService(context).get_session_timeline(session_id)
        return timeline.model_dump()


def question_resource(question_id: str) -> dict[str, Any]:
    return question_answer_get(question_id)


def repo_inventory_resource(project_id: str) -> dict[str, Any]:
    with service_context() as context:
        repositories = RepositoryService(context).list_repositories(project_id=project_id)
        worktrees = WorktreeService(context).list_worktrees(project_id=project_id)
        return {
            "repositories": [RepositoryRead.model_validate(item).model_dump() for item in repositories],
            "worktrees": [WorktreeRead.model_validate(item).model_dump() for item in worktrees],
        }


def recent_events_resource(project_id: str | None = None, task_id: str | None = None) -> list[dict[str, Any]]:
    with service_context() as context:
        stmt = select(Event).order_by(Event.created_at.desc()).limit(30)
        if project_id is not None:
            stmt = stmt.where((Event.entity_type == "project") & (Event.entity_id == project_id))
        if task_id is not None:
            stmt = stmt.where((Event.entity_type == "task") & (Event.entity_id == task_id))
        return [EventRecord.model_validate(item).model_dump() for item in context.db.scalars(stmt)]

from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Any

from sqlalchemy import select

from acp_core.db import SessionLocal, init_db
from acp_core.models import Event, HumanReply, WaitingQuestion, Worktree
from acp_core.schemas import (
    AgentSessionCreate,
    AgentSessionRead,
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
def service_context(actor_type: str = "agent", actor_name: str = "mcp") -> ServiceContext:
    ensure_runtime_ready()
    db = SessionLocal()
    try:
        yield ServiceContext(db=db, actor_type=actor_type, actor_name=actor_name)
    finally:
        db.close()


def project_list() -> list[ProjectSummary]:
    with service_context() as context:
        return [ProjectSummary.model_validate(item) for item in ProjectService(context).list_projects()]


def project_create(name: str, description: str | None = None) -> dict[str, Any]:
    with service_context() as context:
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


def task_create(project_id: str, title: str, description: str | None = None, priority: str = "medium") -> dict[str, Any]:
    with service_context() as context:
        task = TaskService(context).create_task(
            TaskCreate(project_id=project_id, title=title, description=description, priority=priority)
        )
        return TaskRead.model_validate(task).model_dump()


def subtask_create(parent_task_id: str, title: str, description: str | None = None, priority: str = "medium") -> dict[str, Any]:
    with service_context() as context:
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
) -> dict[str, Any]:
    with service_context() as context:
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


def task_claim(task_id: str, actor_name: str, session_id: str | None = None) -> dict[str, Any]:
    with service_context(actor_name=actor_name) as context:
        task = TaskService(context).claim_task(task_id, actor_name=actor_name, session_id=session_id)
        return TaskRead.model_validate(task).model_dump()


def task_comment_add(task_id: str, author_name: str, body: str, author_type: str = "agent") -> dict[str, Any]:
    with service_context(actor_name=author_name) as context:
        comment = TaskService(context).add_comment(
            task_id,
            TaskCommentCreate(author_type=author_type, author_name=author_name, body=body),
        )
        return {
            "id": comment.id,
            "task_id": comment.task_id,
            "author_type": comment.author_type,
            "author_name": comment.author_name,
            "body": comment.body,
            "metadata_json": comment.metadata_json,
            "created_at": comment.created_at,
        }


def task_check_add(task_id: str, check_type: str, status: str, summary: str) -> dict[str, Any]:
    with service_context() as context:
        check = TaskService(context).add_check(
            task_id,
            TaskCheckCreate(check_type=check_type, status=status, summary=summary),
        )
        return {
            "id": check.id,
            "task_id": check.task_id,
            "check_type": check.check_type,
            "status": check.status,
            "summary": check.summary,
            "payload_json": check.payload_json,
            "created_at": check.created_at,
        }


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
) -> dict[str, Any]:
    with service_context() as context:
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
) -> dict[str, Any]:
    with service_context() as context:
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


def worktree_create(repository_id: str, task_id: str | None = None, label: str | None = None) -> dict[str, Any]:
    with service_context() as context:
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
    return session_tail(session_id)


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
        return [
            {
                "id": item.id,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "event_type": item.event_type,
                "payload_json": item.payload_json,
                "created_at": item.created_at,
            }
            for item in context.db.scalars(stmt)
        ]

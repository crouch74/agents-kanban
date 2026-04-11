from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Any, Callable

from sqlalchemy import select

from acp_core.db import SessionLocal, init_db
from acp_core.models import AgentSession, Event, TaskArtifact, TaskCheck, TaskComment, TaskDependency
from acp_core.schemas import (
    AgentSessionCreate,
    AgentSessionFollowUpCreate,
    AgentSessionRead,
    EventRecord,
    ProjectBootstrapCreate,
    ProjectBootstrapRead,
    ProjectCreate,
    ProjectSummary,
    RepositoryRead,
    StackPreset,
    TaskArtifactCreate,
    TaskCheckCreate,
    TaskCommentCreate,
    TaskDependencyCreate,
    TaskCreate,
    TaskPatch,
    TaskRead,
    WaitingQuestionCreate,
    WaitingQuestionRead,
    WorktreeCreate,
    WorktreeRead,
)
from acp_core.services import (
    BootstrapService,
    DiagnosticsService,
    ProjectService,
    RepositoryService,
    SearchService,
    ServiceContext,
    SessionService,
    TaskService,
    WaitingService,
    WorktreeHygieneService,
    WorktreeService,
)


_BOOTSTRAP_LOCK = Lock()
_BOOTSTRAPPED = False

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


def _serialize_task_artifact(artifact: TaskArtifact) -> dict[str, Any]:
    return {
        "id": artifact.id,
        "task_id": artifact.task_id,
        "artifact_type": artifact.artifact_type,
        "name": artifact.name,
        "uri": artifact.uri,
        "payload_json": artifact.payload_json,
        "created_at": artifact.created_at,
    }


def _serialize_task_dependency(dependency: TaskDependency) -> dict[str, Any]:
    return {
        "id": dependency.id,
        "task_id": dependency.task_id,
        "depends_on_task_id": dependency.depends_on_task_id,
        "relationship_type": dependency.relationship_type,
        "created_at": dependency.created_at,
    }


def _serialize_bootstrap_result(context: ServiceContext, event: Event) -> dict[str, Any]:
    project = ProjectService(context).get_project(event.entity_id)
    repository_id = event.payload_json["repository_id"]
    kickoff_task_id = event.payload_json["kickoff_task_id"]
    kickoff_session_id = event.payload_json["kickoff_session_id"]
    kickoff_worktree_id = event.payload_json.get("kickoff_worktree_id")
    repository = RepositoryService(context).get_repository(repository_id)
    kickoff_task = TaskService(context).get_task(kickoff_task_id)
    kickoff_session = SessionService(context).get_session(kickoff_session_id)
    kickoff_worktree = WorktreeService(context).get_worktree(kickoff_worktree_id) if kickoff_worktree_id else None
    return ProjectBootstrapRead(
        project=ProjectSummary.model_validate(project),
        repository=RepositoryRead.model_validate(repository),
        kickoff_task=TaskRead.model_validate(kickoff_task),
        kickoff_session=AgentSessionRead.model_validate(kickoff_session),
        kickoff_worktree=WorktreeRead.model_validate(kickoff_worktree) if kickoff_worktree else None,
        execution_path=event.payload_json["execution_path"],
        execution_branch=event.payload_json["execution_branch"],
        stack_preset=StackPreset(event.payload_json["stack_preset"]),
        stack_notes=event.payload_json.get("stack_notes"),
        use_worktree=bool(event.payload_json["use_worktree"]),
        repo_initialized=bool(event.payload_json["repo_initialized"]),
        scaffold_applied=bool(event.payload_json["scaffold_applied"]),
    ).model_dump()


def _load_idempotent_result(context: ServiceContext, event: Event) -> dict[str, Any]:
    event_type = event.event_type
    entity_id = event.entity_id
    if event_type == "project.created":
        return ProjectSummary.model_validate(ProjectService(context).get_project(entity_id)).model_dump()
    if event_type == "project.bootstrapped":
        return _serialize_bootstrap_result(context, event)
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
    return _load_idempotent_result(context, event)


def _run_read_operation(
    read_fn: Callable[[ServiceContext], Any],
    *,
    actor_type: str = "agent",
    actor_name: str = "mcp",
) -> Any:
    with service_context(actor_type=actor_type, actor_name=actor_name) as context:
        return read_fn(context)


def _run_idempotent_write(
    *,
    event_type: str,
    client_request_id: str | None,
    write_fn: Callable[[ServiceContext], Any],
    serialize_fn: Callable[[ServiceContext, Any], dict[str, Any]],
    actor_type: str = "agent",
    actor_name: str = "mcp",
) -> dict[str, Any]:
    with service_context(actor_type=actor_type, actor_name=actor_name, correlation_id=client_request_id) as context:
        replay = _replay_if_exists(context, event_type, client_request_id)
        if replay is not None:
            return replay
        result = write_fn(context)
        return serialize_fn(context, result)


def project_list() -> list[ProjectSummary]:
    return _run_read_operation(
        lambda context: [ProjectSummary.model_validate(item) for item in ProjectService(context).list_projects()]
    )


def project_create(
    name: str,
    description: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["project_create"],
        client_request_id=client_request_id,
        write_fn=lambda context: ProjectService(context).create_project(ProjectCreate(name=name, description=description)),
        serialize_fn=lambda _context, project: ProjectSummary.model_validate(project).model_dump(),
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
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return _run_idempotent_write(
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
            )
        ),
        serialize_fn=lambda _context, result: result.model_dump(),
    )


def project_get(project_id: str) -> dict[str, Any]:
    return _run_read_operation(lambda context: ProjectService(context).get_project_overview(project_id).model_dump())


def board_get(project_id: str) -> dict[str, Any]:
    return _run_read_operation(lambda context: ProjectService(context).get_board_view(project_id).model_dump())


def task_get(task_id: str) -> dict[str, Any]:
    return _run_read_operation(lambda context: TaskService(context).get_task_detail(task_id).model_dump())


def task_create(
    project_id: str,
    title: str,
    description: str | None = None,
    priority: str = "medium",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_create"],
        client_request_id=client_request_id,
        write_fn=lambda context: TaskService(context).create_task(
            TaskCreate(project_id=project_id, title=title, description=description, priority=priority)
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

    return _run_idempotent_write(
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
    return _run_idempotent_write(
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
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_claim"],
        client_request_id=client_request_id,
        actor_name=actor_name,
        write_fn=lambda context: TaskService(context).claim_task(task_id, actor_name=actor_name, session_id=session_id),
        serialize_fn=lambda _context, task: TaskRead.model_validate(task).model_dump(),
    )


def task_comment_add(
    task_id: str,
    author_name: str,
    body: str,
    author_type: str = "agent",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_comment_add"],
        client_request_id=client_request_id,
        actor_name=author_name,
        write_fn=lambda context: TaskService(context).add_comment(
            task_id,
            TaskCommentCreate(author_type=author_type, author_name=author_name, body=body),
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
    return _run_idempotent_write(
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
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_artifact_add"],
        client_request_id=client_request_id,
        write_fn=lambda context: TaskService(context).add_artifact(
            task_id,
            TaskArtifactCreate(artifact_type=artifact_type, name=name, uri=uri),
        ),
        serialize_fn=lambda _context, artifact: _serialize_task_artifact(artifact),
    )


def task_next(project_id: str | None = None) -> dict[str, Any] | None:
    return _run_read_operation(
        lambda context: (
            TaskRead.model_validate(task).model_dump()
            if (task := TaskService(context).next_task(project_id=project_id))
            else None
        )
    )


def task_dependencies_get(task_id: str) -> list[dict[str, Any]]:
    return _run_read_operation(
        lambda context: [item.model_dump() for item in TaskService(context).get_dependencies(task_id)]
    )


def task_dependency_add(
    task_id: str,
    depends_on_task_id: str,
    relationship_type: str = "blocks",
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["task_dependency_add"],
        client_request_id=client_request_id,
        write_fn=lambda context: TaskService(context).add_dependency(
            task_id,
            TaskDependencyCreate(depends_on_task_id=depends_on_task_id, relationship_type=relationship_type),
        ),
        serialize_fn=lambda _context, dependency: _serialize_task_dependency(dependency),
    )


def task_completion_readiness(task_id: str) -> dict[str, Any]:
    return _run_read_operation(lambda context: TaskService(context).get_completion_readiness(task_id).model_dump())


def session_spawn(
    task_id: str,
    profile: str = "executor",
    repository_id: str | None = None,
    worktree_id: str | None = None,
    command: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["session_spawn"],
        client_request_id=client_request_id,
        write_fn=lambda context: SessionService(context).spawn_session(
            AgentSessionCreate(
                task_id=task_id,
                profile=profile,
                repository_id=repository_id,
                worktree_id=worktree_id,
                command=command,
            )
        ),
        serialize_fn=lambda _context, session: AgentSessionRead.model_validate(session).model_dump(),
    )


def session_follow_up(
    session_id: str,
    profile: str = "verifier",
    follow_up_type: str | None = None,
    reuse_worktree: bool = True,
    reuse_repository: bool = True,
    command: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["session_follow_up"],
        client_request_id=client_request_id,
        write_fn=lambda context: SessionService(context).spawn_follow_up_session(
            session_id,
            AgentSessionFollowUpCreate(
                profile=profile,
                follow_up_type=follow_up_type,
                reuse_worktree=reuse_worktree,
                reuse_repository=reuse_repository,
                command=command,
            ),
        ),
        serialize_fn=lambda _context, session: AgentSessionRead.model_validate(session).model_dump(),
    )


def session_status(session_id: str) -> dict[str, Any]:
    return _run_read_operation(
        lambda context: AgentSessionRead.model_validate(SessionService(context).refresh_session_status(session_id)).model_dump()
    )


def session_tail(session_id: str, lines: int = 80) -> dict[str, Any]:
    return _run_read_operation(lambda context: SessionService(context).tail_session(session_id, lines=lines).model_dump())


def session_list(project_id: str | None = None, task_id: str | None = None) -> list[dict[str, Any]]:
    return _run_read_operation(
        lambda context: [
            AgentSessionRead.model_validate(item).model_dump()
            for item in SessionService(context).list_sessions(project_id=project_id, task_id=task_id)
        ]
    )


def question_open(
    task_id: str,
    prompt: str,
    session_id: str | None = None,
    blocked_reason: str | None = None,
    urgency: str | None = None,
    options_json: list[dict[str, Any]] | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["question_open"],
        client_request_id=client_request_id,
        write_fn=lambda context: WaitingService(context).open_question(
            WaitingQuestionCreate(
                task_id=task_id,
                session_id=session_id,
                prompt=prompt,
                blocked_reason=blocked_reason,
                urgency=urgency,
                options_json=options_json or [],
            )
        ),
        serialize_fn=lambda _context, question: WaitingQuestionRead.model_validate(question).model_dump(),
    )


def question_answer_get(question_id: str) -> dict[str, Any]:
    return _run_read_operation(lambda context: WaitingService(context).get_question_detail(question_id).model_dump())


def worktree_create(
    repository_id: str,
    task_id: str | None = None,
    label: str | None = None,
    client_request_id: str | None = None,
) -> dict[str, Any]:
    return _run_idempotent_write(
        event_type=IDEMPOTENT_EVENT_TYPES["worktree_create"],
        client_request_id=client_request_id,
        write_fn=lambda context: WorktreeService(context).create_worktree(
            WorktreeCreate(repository_id=repository_id, task_id=task_id, label=label)
        ),
        serialize_fn=lambda _context, worktree: WorktreeRead.model_validate(worktree).model_dump(),
    )


def worktree_list(project_id: str | None = None) -> list[dict[str, Any]]:
    return _run_read_operation(
        lambda context: [
            WorktreeRead.model_validate(item).model_dump()
            for item in WorktreeService(context).list_worktrees(project_id=project_id)
        ]
    )


def worktree_get(worktree_id: str) -> dict[str, Any]:
    return _run_read_operation(
        lambda context: WorktreeRead.model_validate(WorktreeService(context).get_worktree(worktree_id)).model_dump()
    )


def context_search(query: str, project_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    return _run_read_operation(
        lambda context: SearchService(context).search(query=query, project_id=project_id, limit=limit).model_dump()
    )


def diagnostics_get() -> dict[str, Any]:
    return _run_read_operation(
        lambda context: DiagnosticsService(context).get_diagnostics().model_dump(),
        actor_type="system",
        actor_name="mcp",
    )


def worktree_hygiene_list(project_id: str | None = None, task_id: str | None = None) -> list[dict[str, Any]]:
    return _run_read_operation(
        lambda context: [
            item.model_dump() for item in WorktreeHygieneService(context).list_issues(project_id=project_id, task_id=task_id)
        ]
    )


def project_board_resource(project_id: str) -> dict[str, Any]:
    return board_get(project_id)


def task_detail_resource(task_id: str) -> dict[str, Any]:
    return task_get(task_id)


def task_completion_resource(task_id: str) -> dict[str, Any]:
    return task_completion_readiness(task_id)


def session_timeline_resource(session_id: str) -> dict[str, Any]:
    return _run_read_operation(lambda context: SessionService(context).get_session_timeline(session_id).model_dump())


def question_resource(question_id: str) -> dict[str, Any]:
    return question_answer_get(question_id)


def repo_inventory_resource(project_id: str) -> dict[str, Any]:
    def _load_inventory(context: ServiceContext) -> dict[str, Any]:
        repositories = RepositoryService(context).list_repositories(project_id=project_id)
        worktrees = WorktreeService(context).list_worktrees(project_id=project_id)
        return {
            "repositories": [RepositoryRead.model_validate(item).model_dump() for item in repositories],
            "worktrees": [WorktreeRead.model_validate(item).model_dump() for item in worktrees],
        }

    return _run_read_operation(_load_inventory)


def diagnostics_resource() -> dict[str, Any]:
    return diagnostics_get()


def recent_events_resource(project_id: str | None = None, task_id: str | None = None) -> list[dict[str, Any]]:
    def _load_events(context: ServiceContext) -> list[dict[str, Any]]:
        stmt = select(Event).order_by(Event.created_at.desc()).limit(30)
        if project_id is not None:
            stmt = stmt.where((Event.entity_type == "project") & (Event.entity_id == project_id))
        if task_id is not None:
            stmt = stmt.where((Event.entity_type == "task") & (Event.entity_id == task_id))
        return [EventRecord.model_validate(item).model_dump() for item in context.db.scalars(stmt)]

    return _run_read_operation(_load_events)

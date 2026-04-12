from __future__ import annotations

from pathlib import Path

from sqlalchemy import String, cast, func, or_, select

from acp_core.infrastructure.runtime_adapter import DefaultRuntimeAdapter, RuntimeAdapterProtocol
from acp_core.models import AgentSession, Event, Project, Repository, Task, WaitingQuestion, Worktree
from acp_core.schemas import DashboardRead, DiagnosticsRead, EventRecord, SearchHit, SearchResults
from acp_core.services.base_service import ServiceContext
from acp_core.services.session_service import SessionService


class EventService:
    """Read service for append-only event streams."""
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_events(
        self,
        *,
        project_id: str | None = None,
        task_id: str | None = None,
        session_id: str | None = None,
        limit: int = 50,
    ) -> list[EventRecord]:
        """Purpose: list events.

        Args:
            project_id: Input parameter.; task_id: Input parameter.; session_id: Input parameter.; limit: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        stmt = select(Event).order_by(Event.created_at.desc()).limit(limit)
        if project_id is not None:
            stmt = stmt.where(
                or_(
                    (Event.entity_type == "project") & (Event.entity_id == project_id),
                    cast(Event.payload_json, String).like(f'%"{project_id}"%'),
                )
            )
        if task_id is not None:
            stmt = stmt.where(
                or_(
                    (Event.entity_type == "task") & (Event.entity_id == task_id),
                    cast(Event.payload_json, String).like(f'%"{task_id}"%'),
                )
            )
        if session_id is not None:
            stmt = stmt.where(
                or_(
                    (Event.entity_type == "session") & (Event.entity_id == session_id),
                    cast(Event.payload_json, String).like(f'%"{session_id}"%'),
                )
            )
        return [EventRecord.model_validate(item) for item in self.context.db.scalars(stmt)]


class RecoveryService:
    """Runtime reconciliation service between DB state and tmux state.

    WHY:
        Detects drift and reconciles stale session statuses so operators see
        durable truth even when external runtime state changes unexpectedly.
    """
    def __init__(self, context: ServiceContext, runtime: RuntimeAdapterProtocol | None = None) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()

    def reconcile_runtime_sessions(self) -> dict[str, Any]:
        """Purpose: reconcile runtime sessions.

        Args:
            None.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
        tracked_runtime_sessions = {
            session.session_name: session
            for session in self.context.db.scalars(
                select(AgentSession).where(AgentSession.status.in_(["running", "waiting_human", "blocked"]))
            )
        }
        try:
            runtime_sessions = self.runtime.list_sessions(prefix="acp-")
        except Exception as exc:
            raise build_runtime_service_error(operation="runtime_reconcile", exc=exc) from exc
        runtime_session_names = {item.session_name for item in runtime_sessions}
        reconciled = 0

        for session_name, session in tracked_runtime_sessions.items():
            next_status = None
            if session_name in runtime_session_names:
                next_status = SessionService(self.context, runtime=self.runtime)._runtime_session_status(
                    session,
                    exists=True,
                )
            elif session.status != "cancelled":
                next_status = "failed"

            if next_status is not None and session.status != next_status:
                session.status = next_status
                self.context.record_event(
                    entity_type="session",
                    entity_id=session.id,
                    event_type="session.reconciled",
                    payload_json={"status": next_status, "session_name": session.session_name},
                )
                reconciled += 1

        if reconciled:
            self.context.db.commit()

        orphan_runtime_sessions = sorted(runtime_session_names.difference(tracked_runtime_sessions.keys()))
        return {
            "reconciled_session_count": reconciled,
            "runtime_managed_session_count": len(runtime_sessions),
            "orphan_runtime_session_count": len(orphan_runtime_sessions),
            "orphan_runtime_sessions": orphan_runtime_sessions,
        }


class WorktreeHygieneService:
    """Detect stale or drifted worktrees and suggest recovery actions."""
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_issues(self, *, project_id: str | None = None, task_id: str | None = None) -> list[WorktreeHygieneIssueRead]:
        """Purpose: list issues.

        Args:
            project_id: Input parameter.; task_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        stmt = select(Worktree).order_by(Worktree.updated_at.desc())
        if project_id is not None:
            stmt = stmt.join(Repository, Repository.id == Worktree.repository_id).where(Repository.project_id == project_id)
        if task_id is not None:
            stmt = stmt.where(Worktree.task_id == task_id)

        issues: list[WorktreeHygieneIssueRead] = []
        for worktree in self.context.db.scalars(stmt):
            if worktree.status == "pruned":
                continue

            repository = self.context.db.get(Repository, worktree.repository_id)
            task = self.context.db.get(Task, worktree.task_id) if worktree.task_id else None
            session = self.context.db.get(AgentSession, worktree.session_id) if worktree.session_id else None
            reasons: list[str] = []
            recommendation: str | None = None

            if not Path(worktree.path).exists():
                reasons.append("worktree_path_missing")
                recommendation = "inspect"

            if session is not None and session.status in {"done", "failed", "cancelled"}:
                reasons.append(f"session_{session.status}")
                recommendation = "archive" if worktree.status == "active" else "prune"

            if task is not None and task.workflow_state in {"done", "cancelled"}:
                reasons.append(f"task_{task.workflow_state}")
                if recommendation is None:
                    recommendation = "archive" if worktree.status == "active" else "prune"

            if worktree.status == "archived" and not reasons:
                continue

            if reasons and recommendation is not None:
                issues.append(
                    WorktreeHygieneIssueRead(
                        worktree_id=worktree.id,
                        project_id=repository.project_id if repository else None,
                        task_id=worktree.task_id,
                        session_id=worktree.session_id,
                        branch_name=worktree.branch_name,
                        path=worktree.path,
                        status=worktree.status,
                        recommendation=recommendation,
                        reasons=reasons,
                    )
                )

        return issues


class DiagnosticsService:
    """System diagnostics and health summary service.

    WHY:
        Aggregates counts plus reconciliation/hygiene outputs so operators can
        quickly diagnose runtime and persistence drift from one read model.
    """
    def __init__(self, context: ServiceContext, runtime: RuntimeAdapterProtocol | None = None) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()

    def get_diagnostics(self) -> DiagnosticsRead:
        """Purpose: get diagnostics.

        Args:
            None.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        project_count = self.context.db.scalar(select(func.count(Project.id))) or 0
        repository_count = self.context.db.scalar(select(func.count(Repository.id))) or 0
        task_count = self.context.db.scalar(select(func.count(Task.id))) or 0
        worktree_count = self.context.db.scalar(select(func.count(Worktree.id))) or 0
        session_count = self.context.db.scalar(select(func.count(AgentSession.id))) or 0
        open_question_count = (
            self.context.db.scalar(select(func.count(WaitingQuestion.id)).where(WaitingQuestion.status == "open")) or 0
        )
        event_count = self.context.db.scalar(select(func.count(Event.id))) or 0
        tmux_server_running = False
        if which("tmux") is not None:
            try:
                self.runtime.list_sessions()
                tmux_server_running = True
            except Exception:
                tmux_server_running = False
        recovery = RecoveryService(self.context, runtime=self.runtime).reconcile_runtime_sessions()
        stale_worktrees = WorktreeHygieneService(self.context).list_issues()
        return DiagnosticsRead(
            app_name=settings.app_name,
            environment=settings.app_env,
            database_path=str(settings.database_path),
            runtime_home=str(settings.runtime_home),
            tmux_available=which("tmux") is not None,
            tmux_server_running=tmux_server_running,
            runtime_managed_session_count=recovery["runtime_managed_session_count"],
            orphan_runtime_session_count=recovery["orphan_runtime_session_count"],
            orphan_runtime_sessions=recovery["orphan_runtime_sessions"],
            reconciled_session_count=recovery["reconciled_session_count"],
            stale_worktree_count=len(stale_worktrees),
            stale_worktrees=stale_worktrees,
            git_available=which("git") is not None,
            current_project_count=project_count,
            current_repository_count=repository_count,
            current_task_count=task_count,
            current_worktree_count=worktree_count,
            current_session_count=session_count,
            current_open_question_count=open_question_count,
            current_event_count=event_count,
        )


class DashboardService:
    """Operator dashboard read-model service for glanceable control-plane state."""
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def get_dashboard(self) -> DashboardRead:
        """Purpose: get dashboard.

        Args:
            None.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        projects = list(self.context.db.scalars(select(Project).order_by(Project.created_at.desc()).limit(8)))
        events = list(self.context.db.scalars(select(Event).order_by(Event.created_at.desc()).limit(12)))
        waiting_questions = list(
            self.context.db.scalars(
                select(WaitingQuestion)
                .where(WaitingQuestion.status == "open")
                .order_by(WaitingQuestion.created_at.desc())
                .limit(8)
            )
        )
        blocked_tasks = list(
            self.context.db.scalars(
                select(Task)
                .where(Task.blocked_reason.is_not(None))
                .order_by(Task.updated_at.desc())
                .limit(8)
            )
        )
        active_sessions = list(
            self.context.db.scalars(
                select(AgentSession)
                .where(AgentSession.status == "running")
                .order_by(AgentSession.updated_at.desc())
                .limit(8)
            )
        )
        waiting_count = len(waiting_questions)
        blocked_count = len(blocked_tasks)
        running_sessions = len(active_sessions)
        return DashboardRead(
            projects=[ProjectSummary.model_validate(project) for project in projects],
            recent_events=[EventRecord.model_validate(event) for event in events],
            waiting_questions=[WaitingQuestionRead.model_validate(question) for question in waiting_questions],
            blocked_tasks=[TaskRead.model_validate(task) for task in blocked_tasks],
            active_sessions=[AgentSessionRead.model_validate(session) for session in active_sessions],
            waiting_count=waiting_count,
            blocked_count=blocked_count,
            running_sessions=running_sessions,
        )


class SearchService:
    """Cross-entity search service over project control-plane records.

    WHY:
        Builds structured hits server-side to avoid UI scraping and to preserve
        parity for REST/MCP consumers using the same relevance rules.
    """
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def search(self, query: str, project_id: str | None = None, limit: int = 20) -> SearchResults:
        """Purpose: search.

        Args:
            query: Input parameter.; project_id: Input parameter.; limit: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        needle = query.strip()
        if not needle:
            return SearchResults(query=query, hits=[])

        pattern = f"%{needle.lower()}%"
        hits: list[SearchHit] = []

        project_stmt = select(Project).where(
            or_(
                func.lower(Project.name).like(pattern),
                func.lower(func.coalesce(Project.description, "")).like(pattern),
                func.lower(Project.slug).like(pattern),
            )
        )
        if project_id is not None:
            project_stmt = project_stmt.where(Project.id == project_id)
        for project in self.context.db.scalars(project_stmt.limit(5)):
            hits.append(
                SearchHit(
                    entity_type="project",
                    entity_id=project.id,
                    project_id=project.id,
                    title=project.name,
                    snippet=project.description or project.slug,
                    secondary="project",
                    created_at=project.created_at,
                )
            )

        task_stmt = select(Task).where(
            or_(
                func.lower(Task.title).like(pattern),
                func.lower(func.coalesce(Task.description, "")).like(pattern),
                func.lower(cast(Task.tags, String)).like(pattern),
            )
        )
        if project_id is not None:
            task_stmt = task_stmt.where(Task.project_id == project_id)
        for task in self.context.db.scalars(task_stmt.limit(8)):
            hits.append(
                SearchHit(
                    entity_type="task",
                    entity_id=task.id,
                    project_id=task.project_id,
                    title=task.title,
                    snippet=task.description or task.workflow_state,
                    secondary=task.priority,
                    created_at=task.created_at,
                )
            )

        comment_stmt = (
            select(TaskComment, Task.project_id, Task.title)
            .join(Task, Task.id == TaskComment.task_id)
            .where(func.lower(TaskComment.body).like(pattern))
        )
        if project_id is not None:
            comment_stmt = comment_stmt.where(Task.project_id == project_id)
        for comment, comment_project_id, task_title in self.context.db.execute(comment_stmt.limit(5)):
            hits.append(
                SearchHit(
                    entity_type="task_comment",
                    entity_id=comment.id,
                    project_id=comment_project_id,
                    title=f"Comment on {task_title}",
                    snippet=comment.body,
                    secondary=comment.author_name,
                    created_at=comment.created_at,
                )
            )

        question_stmt = select(WaitingQuestion).where(
            or_(
                func.lower(WaitingQuestion.prompt).like(pattern),
                func.lower(func.coalesce(WaitingQuestion.blocked_reason, "")).like(pattern),
            )
        )
        if project_id is not None:
            question_stmt = question_stmt.where(WaitingQuestion.project_id == project_id)
        for question in self.context.db.scalars(question_stmt.limit(5)):
            hits.append(
                SearchHit(
                    entity_type="waiting_question",
                    entity_id=question.id,
                    project_id=question.project_id,
                    title=question.prompt,
                    snippet=question.blocked_reason or question.status,
                    secondary=question.urgency,
                    created_at=question.created_at,
                )
            )

        session_stmt = select(AgentSession).where(
            or_(
                func.lower(AgentSession.session_name).like(pattern),
                func.lower(AgentSession.profile).like(pattern),
                func.lower(cast(AgentSession.runtime_metadata, String)).like(pattern),
            )
        )
        if project_id is not None:
            session_stmt = session_stmt.where(AgentSession.project_id == project_id)
        for session in self.context.db.scalars(session_stmt.limit(5)):
            hits.append(
                SearchHit(
                    entity_type="session",
                    entity_id=session.id,
                    project_id=session.project_id,
                    title=session.session_name,
                    snippet=session.runtime_metadata.get("working_directory", session.status),
                    secondary=session.profile,
                    created_at=session.created_at,
                )
            )

        event_stmt = select(Event).where(
            or_(
                func.lower(Event.event_type).like(pattern),
                func.lower(cast(Event.payload_json, String)).like(pattern),
            )
        )
        if project_id is not None:
            event_stmt = event_stmt.where(
                or_(
                    Event.entity_id == project_id,
                    cast(Event.payload_json, String).like(f'%"{project_id}"%'),
                )
            )
        for event in self.context.db.scalars(event_stmt.limit(5)):
            inferred_project_id = None
            if event.entity_type == "project":
                inferred_project_id = event.entity_id
            hits.append(
                SearchHit(
                    entity_type="event",
                    entity_id=event.id,
                    project_id=inferred_project_id,
                    title=event.event_type,
                    snippet=str(event.payload_json),
                    secondary=event.actor_name,
                    created_at=event.created_at,
                )
            )

        ordered = sorted(hits, key=lambda item: item.created_at, reverse=True)[:limit]
        return SearchResults(query=query, hits=ordered)


# Deferred imports to keep the module order straightforward.
from acp_core.schemas import ProjectSummary, TaskRead  # noqa: E402

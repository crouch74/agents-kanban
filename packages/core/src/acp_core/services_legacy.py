from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from re import sub
from shutil import which
import textwrap
from typing import Any

from git import InvalidGitRepositoryError, NoSuchPathError
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from acp_core.constants import DEFAULT_BOARD_COLUMNS, TASK_TRANSITIONS, WORKFLOW_BY_COLUMN_KEY
from acp_core.logging import logger
from acp_core.infrastructure.git_repository_adapter import GitRepositoryAdapter, GitRepositoryAdapterProtocol
from acp_core.infrastructure.runtime_adapter import DefaultRuntimeAdapter, RuntimeAdapterProtocol
from acp_core.infrastructure.scaffold_writer import ScaffoldWriter, ScaffoldWriterProtocol
from acp_core.models import (
    AgentRun,
    AgentSession,
    Board,
    BoardColumn,
    Event,
    HumanReply,
    Project,
    Repository,
    SessionMessage,
    TaskArtifact,
    TaskCheck,
    Task,
    TaskComment,
    TaskDependency,
    WaitingQuestion,
    Worktree,
)
from acp_core.runtime import safe_tmux_name
from acp_core.schemas import (
    AgentRunRead,
    AgentSessionCreate,
    AgentSessionFollowUpCreate,
    AgentSessionRead,
    BoardColumnRead,
    BoardView,
    DashboardRead,
    DiagnosticsRead,
    EventRecord,
    HumanReplyCreate,
    HumanReplyRead,
    ProjectBootstrapCreate,
    ProjectBootstrapRead,
    ProjectCreate,
    ProjectOverview,
    ProjectSummary,
    RepositoryCreate,
    RepositoryRead,
    SearchHit,
    SearchResults,
    StackPreset,
    TaskArtifactCreate,
    TaskArtifactRead,
    TaskCheckCreate,
    TaskCheckRead,
    TaskCommentCreate,
    TaskCommentRead,
    TaskCompletionReadinessRead,
    TaskDependencyCreate,
    TaskDependencyRead,
    TaskRead,
    WaitingQuestionCreate,
    WaitingQuestionDetail,
    WaitingQuestionRead,
    TaskCreate,
    TaskDetail,
    TaskPatch,
    SessionTailRead,
    SessionTimelineRead,
    SessionMessageRead,
    WorktreeCreate,
    WorktreeHygieneIssueRead,
    WorktreePatch,
    WorktreeRead,
)
from acp_core.settings import settings


def slugify(value: str) -> str:
    normalized = sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "project"


def task_slug(value: str) -> str:
    return slugify(value)[:32]


@dataclass
class ServiceContext:
    db: Session
    actor_type: str = "human"
    actor_name: str = "operator"
    correlation_id: str | None = None

    def record_event(
        self,
        *,
        entity_type: str,
        entity_id: str,
        event_type: str,
        payload_json: dict[str, Any],
        correlation_id: str | None = None,
    ) -> Event:
        event = Event(
            actor_type=self.actor_type,
            actor_name=self.actor_name,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            correlation_id=correlation_id or self.correlation_id,
            payload_json=payload_json,
        )
        self.db.add(event)
        return event


class ProjectService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_projects(self) -> list[Project]:
        stmt = select(Project).where(Project.archived.is_(False)).order_by(Project.created_at.desc())
        return list(self.context.db.scalars(stmt))

    def _repair_board_columns(self, board: Board) -> None:
        existing_keys = {column.key for column in board.columns}
        missing_columns = [column for column in DEFAULT_BOARD_COLUMNS if column["key"] not in existing_keys]
        if not missing_columns:
            return

        for column_data in missing_columns:
            board.columns.append(BoardColumn(**column_data))

        self.context.record_event(
            entity_type="board",
            entity_id=board.id,
            event_type="board.columns_repaired",
            payload_json={
                "project_id": board.project_id,
                "added_column_keys": [str(column["key"]) for column in missing_columns],
            },
        )
        self.context.db.flush()
        self.context.db.commit()
        logger.info(
            "🗂️ board columns repaired",
            board_id=board.id,
            project_id=board.project_id,
            added_column_keys=[str(column["key"]) for column in missing_columns],
        )

    def get_project(self, project_id: str) -> Project:
        project = self.context.db.get(Project, project_id)
        if project is None:
            raise ValueError("Project not found")
        return project

    def create_project(self, payload: ProjectCreate) -> Project:
        slug = slugify(payload.name)
        suffix = 1
        while self.context.db.scalar(select(Project.id).where(Project.slug == slug)) is not None:
            suffix += 1
            slug = f"{slugify(payload.name)}-{suffix}"

        project = Project(name=payload.name, slug=slug, description=payload.description)
        board = Board(name="Main Board", project=project)
        self.context.db.add(project)
        self.context.db.add(board)

        for column_data in DEFAULT_BOARD_COLUMNS:
            board.columns.append(BoardColumn(**column_data))

        self.context.db.flush()

        self.context.record_event(
            entity_type="project",
            entity_id=project.id,
            event_type="project.created",
            payload_json={"name": project.name, "slug": project.slug},
        )
        self.context.db.commit()
        self.context.db.refresh(project)

        logger.info("🗂️ project created", project_id=project.id, slug=project.slug)
        return project

    def get_board_view(self, project_id: str) -> BoardView:
        project = self.get_project(project_id)
        if project.board is None:
            raise ValueError("Board not found")
        self._repair_board_columns(project.board)

        tasks_stmt = (
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.parent_task_id.is_not(None), Task.created_at.asc())
        )
        tasks = list(self.context.db.scalars(tasks_stmt))
        return BoardView(
            id=project.board.id,
            project_id=project.id,
            name=project.board.name,
            columns=[BoardColumnRead.model_validate(column) for column in project.board.columns],
            tasks=[TaskRead.model_validate(task) for task in tasks],
        )

    def get_project_overview(self, project_id: str) -> ProjectOverview:
        project = self.get_project(project_id)
        board = self.get_board_view(project_id)
        repositories = list(
            self.context.db.scalars(
                select(Repository).where(Repository.project_id == project_id).order_by(Repository.created_at.asc())
            )
        )
        worktrees = list(
            self.context.db.scalars(
                select(Worktree)
                .join(Repository, Repository.id == Worktree.repository_id)
                .where(Repository.project_id == project_id)
                .order_by(Worktree.created_at.desc())
            )
        )
        sessions = list(
            self.context.db.scalars(
                select(AgentSession).where(AgentSession.project_id == project_id).order_by(AgentSession.created_at.desc())
            )
        )
        waiting_questions = list(
            self.context.db.scalars(
                select(WaitingQuestion)
                .where(WaitingQuestion.project_id == project_id, WaitingQuestion.status == "open")
                .order_by(WaitingQuestion.created_at.desc())
            )
        )
        return ProjectOverview(
            project=ProjectSummary.model_validate(project),
            board=board,
            repositories=[RepositoryRead.model_validate(item) for item in repositories],
            worktrees=[WorktreeRead.model_validate(item) for item in worktrees],
            sessions=[AgentSessionRead.model_validate(item) for item in sessions],
            waiting_questions=[WaitingQuestionRead.model_validate(item) for item in waiting_questions],
        )


class TaskService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        stmt = select(Task).order_by(Task.created_at.desc())
        if project_id is not None:
            stmt = stmt.where(Task.project_id == project_id)
        return list(self.context.db.scalars(stmt))

    def get_task(self, task_id: str) -> Task:
        task = self.context.db.get(Task, task_id)
        if task is None:
            raise ValueError("Task not found")
        return task

    def get_task_detail(self, task_id: str) -> TaskDetail:
        task = self.get_task(task_id)
        dependencies = list(
            self.context.db.scalars(
                select(TaskDependency).where(TaskDependency.task_id == task.id).order_by(TaskDependency.created_at.asc())
            )
        )
        comments = list(
            self.context.db.scalars(
                select(TaskComment).where(TaskComment.task_id == task.id).order_by(TaskComment.created_at.asc())
            )
        )
        checks = list(
            self.context.db.scalars(
                select(TaskCheck).where(TaskCheck.task_id == task.id).order_by(TaskCheck.created_at.asc())
            )
        )
        artifacts = list(
            self.context.db.scalars(
                select(TaskArtifact).where(TaskArtifact.task_id == task.id).order_by(TaskArtifact.created_at.asc())
            )
        )
        waiting_questions = list(
            self.context.db.scalars(
                select(WaitingQuestion).where(WaitingQuestion.task_id == task.id).order_by(WaitingQuestion.created_at.desc())
            )
        )
        return TaskDetail(
            **TaskRead.model_validate(task).model_dump(),
            dependencies=[TaskDependencyRead.model_validate(item) for item in dependencies],
            comments=[TaskCommentRead.model_validate(item) for item in comments],
            checks=[TaskCheckRead.model_validate(item) for item in checks],
            artifacts=[TaskArtifactRead.model_validate(item) for item in artifacts],
            waiting_questions=[WaitingQuestionRead.model_validate(item) for item in waiting_questions],
        )

    def create_task(self, payload: TaskCreate) -> Task:
        board_stmt = select(Board).where(Board.project_id == payload.project_id)
        board = self.context.db.scalar(board_stmt)
        if board is None:
            raise ValueError("Project board not found")

        column = next((item for item in board.columns if item.key == payload.board_column_key), None)
        if column is None:
            raise ValueError("Board column not found")

        if payload.parent_task_id is not None:
            parent = self.get_task(payload.parent_task_id)
            if parent.parent_task_id is not None:
                raise ValueError("Nested subtasks beyond one level are not supported in v1")

        task = Task(
            project_id=payload.project_id,
            board_column_id=column.id,
            parent_task_id=payload.parent_task_id,
            title=payload.title,
            description=payload.description,
            workflow_state=WORKFLOW_BY_COLUMN_KEY[column.key],
            priority=payload.priority,
            tags=payload.tags,
        )

        active_wip = self.context.db.scalar(
            select(func.count(Task.id)).where(
                Task.board_column_id == column.id,
                Task.parent_task_id.is_(None),
            )
        )
        if column.wip_limit is not None and active_wip is not None and active_wip >= column.wip_limit:
            raise ValueError(f"Column '{column.name}' is at its WIP limit")

        self.context.db.add(task)
        self.context.db.flush()
        self.context.record_event(
            entity_type="task",
            entity_id=task.id,
            event_type="task.created",
            payload_json={"title": task.title, "project_id": task.project_id},
        )
        self.context.db.commit()
        self.context.db.refresh(task)

        logger.info("🗂️ task created", task_id=task.id, project_id=task.project_id)
        return task

    def _ensure_completion_evidence(self, task: Task) -> None:
        readiness = self.get_completion_readiness(task.id)
        if not readiness.can_mark_done:
            raise ValueError(
                "Task cannot move to done: " + ", ".join(readiness.missing_requirements)
            )

    def get_completion_readiness(self, task_id: str) -> TaskCompletionReadinessRead:
        task = self.get_task(task_id)
        passing_check_count = self.context.db.scalar(
            select(func.count(TaskCheck.id)).where(
                TaskCheck.task_id == task.id,
                TaskCheck.status.in_(["passed", "warning"]),
            )
        ) or 0
        artifact_count = self.context.db.scalar(
            select(func.count(TaskArtifact.id)).where(TaskArtifact.task_id == task.id)
        ) or 0
        blocking_dependency_count = self.context.db.scalar(
            select(func.count(TaskDependency.id))
            .join(Task, Task.id == TaskDependency.depends_on_task_id)
            .where(
                TaskDependency.task_id == task.id,
                Task.workflow_state.not_in(["done", "cancelled"]),
            )
        ) or 0
        open_waiting_question_count = self.context.db.scalar(
            select(func.count(WaitingQuestion.id)).where(
                WaitingQuestion.task_id == task.id,
                WaitingQuestion.status == "open",
            )
        ) or 0

        missing_requirements: list[str] = []
        if passing_check_count == 0 and artifact_count == 0:
            missing_requirements.append("attach at least one passing check or artifact")
        if blocking_dependency_count:
            missing_requirements.append("resolve blocking dependencies")
        if open_waiting_question_count:
            missing_requirements.append("close open waiting questions")

        return TaskCompletionReadinessRead(
            task_id=task.id,
            can_mark_done=not missing_requirements,
            passing_check_count=passing_check_count,
            artifact_count=artifact_count,
            blocking_dependency_count=blocking_dependency_count,
            open_waiting_question_count=open_waiting_question_count,
            missing_requirements=missing_requirements,
        )

    def patch_task(self, task_id: str, payload: TaskPatch) -> Task:
        task = self.get_task(task_id)
        provided = payload.model_fields_set
        next_workflow_state = task.workflow_state

        if "title" in provided and payload.title is not None:
            task.title = payload.title

        if "description" in provided:
            task.description = payload.description

        if "blocked_reason" in provided:
            task.blocked_reason = payload.blocked_reason

        if "waiting_for_human" in provided and payload.waiting_for_human is not None:
            task.waiting_for_human = payload.waiting_for_human

        if "workflow_state" in provided and payload.workflow_state is not None:
            allowed = TASK_TRANSITIONS[task.workflow_state]
            if payload.workflow_state not in allowed:
                raise ValueError(
                    f"Invalid workflow transition from {task.workflow_state} to {payload.workflow_state}"
                )
            next_workflow_state = payload.workflow_state

        if "board_column_id" in provided and payload.board_column_id is not None:
            column = self.context.db.get(BoardColumn, payload.board_column_id)
            if column is None:
                raise ValueError("Board column not found")
            task.board_column_id = column.id
            next_workflow_state = WORKFLOW_BY_COLUMN_KEY.get(column.key, next_workflow_state)

        if task.workflow_state != "done" and next_workflow_state == "done":
            self._ensure_completion_evidence(task)

        task.workflow_state = next_workflow_state

        self.context.record_event(
            entity_type="task",
            entity_id=task.id,
            event_type="task.updated",
            payload_json={
                "workflow_state": task.workflow_state,
                "waiting_for_human": task.waiting_for_human,
                "blocked_reason": task.blocked_reason,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(task)

        logger.info("🗂️ task updated", task_id=task.id, workflow_state=task.workflow_state)
        return task

    def add_comment(self, task_id: str, payload: TaskCommentCreate) -> TaskComment:
        task = self.get_task(task_id)
        comment = TaskComment(
            task_id=task.id,
            author_type=payload.author_type,
            author_name=payload.author_name,
            body=payload.body,
            metadata_json=payload.metadata_json,
        )
        self.context.db.add(comment)
        self.context.db.flush()
        self.context.record_event(
            entity_type="task_comment",
            entity_id=comment.id,
            event_type="task.comment_added",
            payload_json={"task_id": task.id, "author_name": comment.author_name},
        )
        self.context.db.commit()
        self.context.db.refresh(comment)
        logger.info("🗂️ task comment added", task_id=task.id, comment_id=comment.id)
        return comment

    def add_check(self, task_id: str, payload: TaskCheckCreate) -> TaskCheck:
        task = self.get_task(task_id)
        check = TaskCheck(
            task_id=task.id,
            check_type=payload.check_type,
            status=payload.status,
            summary=payload.summary,
            payload_json=payload.payload_json,
        )
        self.context.db.add(check)
        self.context.db.flush()
        self.context.record_event(
            entity_type="task_check",
            entity_id=check.id,
            event_type="task.check_added",
            payload_json={"task_id": task.id, "check_type": check.check_type, "status": check.status},
        )
        self.context.db.commit()
        self.context.db.refresh(check)
        logger.info("✅ task check added", task_id=task.id, check_id=check.id, status=check.status)
        return check

    def add_artifact(self, task_id: str, payload: TaskArtifactCreate) -> TaskArtifact:
        task = self.get_task(task_id)
        artifact = TaskArtifact(
            task_id=task.id,
            artifact_type=payload.artifact_type,
            name=payload.name,
            uri=payload.uri,
            payload_json=payload.payload_json,
        )
        self.context.db.add(artifact)
        self.context.db.flush()
        self.context.record_event(
            entity_type="task_artifact",
            entity_id=artifact.id,
            event_type="task.artifact_added",
            payload_json={"task_id": task.id, "artifact_type": artifact.artifact_type, "uri": artifact.uri},
        )
        self.context.db.commit()
        self.context.db.refresh(artifact)
        logger.info("✅ task artifact added", task_id=task.id, artifact_id=artifact.id)
        return artifact

    def add_dependency(self, task_id: str, payload: TaskDependencyCreate) -> TaskDependency:
        task = self.get_task(task_id)
        depends_on = self.get_task(payload.depends_on_task_id)
        if depends_on.id == task.id:
            raise ValueError("Task cannot depend on itself")
        if depends_on.project_id != task.project_id:
            raise ValueError("Dependencies must stay within the same project")

        duplicate = self.context.db.scalar(
            select(TaskDependency.id).where(
                TaskDependency.task_id == task.id,
                TaskDependency.depends_on_task_id == depends_on.id,
                TaskDependency.relationship_type == payload.relationship_type,
            )
        )
        if duplicate is not None:
            raise ValueError("Dependency already exists")

        dependency = TaskDependency(
            task_id=task.id,
            depends_on_task_id=depends_on.id,
            relationship_type=payload.relationship_type,
        )
        self.context.db.add(dependency)
        self.context.db.flush()
        self.context.record_event(
            entity_type="task_dependency",
            entity_id=dependency.id,
            event_type="task.dependency_added",
            payload_json={
                "task_id": task.id,
                "depends_on_task_id": depends_on.id,
                "relationship_type": dependency.relationship_type,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(dependency)
        logger.info("🗂️ task dependency added", task_id=task.id, depends_on_task_id=depends_on.id)
        return dependency

    def claim_task(self, task_id: str, *, actor_name: str, session_id: str | None = None) -> Task:
        task = self.get_task(task_id)
        metadata = dict(task.metadata_json)
        metadata["claimed_by"] = actor_name
        metadata["claimed_session_id"] = session_id
        task.metadata_json = metadata
        self.context.record_event(
            entity_type="task",
            entity_id=task.id,
            event_type="task.claimed",
            payload_json={"actor_name": actor_name, "session_id": session_id},
        )
        self.context.db.commit()
        self.context.db.refresh(task)
        logger.info("🗂️ task claimed", task_id=task.id, actor_name=actor_name)
        return task

    def get_dependencies(self, task_id: str) -> list[TaskDependencyRead]:
        self.get_task(task_id)
        dependencies = list(
            self.context.db.scalars(
                select(TaskDependency)
                .where(TaskDependency.task_id == task_id)
                .order_by(TaskDependency.created_at.asc())
            )
        )
        return [TaskDependencyRead.model_validate(item) for item in dependencies]

    def next_task(self, project_id: str | None = None) -> Task | None:
        stmt = (
            select(Task)
            .where(
                Task.parent_task_id.is_(None),
                Task.workflow_state.in_(["ready", "in_progress"]),
                Task.waiting_for_human.is_(False),
            )
            .order_by(
                Task.priority.desc(),
                Task.created_at.asc(),
            )
        )
        if project_id is not None:
            stmt = stmt.where(Task.project_id == project_id)
        return self.context.db.scalar(stmt.limit(1))


class RepositoryService:
    def __init__(self, context: ServiceContext, git: GitRepositoryAdapterProtocol | None = None) -> None:
        self.context = context
        self.git = git or GitRepositoryAdapter()

    def list_repositories(self, project_id: str | None = None) -> list[Repository]:
        stmt = select(Repository).order_by(Repository.created_at.asc())
        if project_id is not None:
            stmt = stmt.where(Repository.project_id == project_id)
        return list(self.context.db.scalars(stmt))

    def get_repository(self, repository_id: str) -> Repository:
        repository = self.context.db.get(Repository, repository_id)
        if repository is None:
            raise ValueError("Repository not found")
        return repository

    @staticmethod
    def inspect_git_repository(repo_path: Path) -> tuple[str | None, dict[str, Any]]:
        details = GitRepositoryAdapter().inspect_repository(repo_path)
        return details.default_branch, details.metadata_json

    def create_repository(self, payload: RepositoryCreate) -> Repository:
        project = self.context.db.get(Project, payload.project_id)
        if project is None:
            raise ValueError("Project not found")

        repo_path = Path(payload.local_path).expanduser().resolve()
        try:
            self.git.validate_repository(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise ValueError("Local path must point to a git repository") from exc

        details = self.git.inspect_repository(repo_path)

        repository = Repository(
            project_id=payload.project_id,
            name=payload.name or repo_path.name,
            local_path=str(repo_path),
            default_branch=details.default_branch,
            metadata_json=details.metadata_json,
        )
        self.context.db.add(repository)
        self.context.db.flush()
        self.context.record_event(
            entity_type="repository",
            entity_id=repository.id,
            event_type="repository.created",
            payload_json={"project_id": project.id, "local_path": repository.local_path},
        )
        self.context.db.commit()
        self.context.db.refresh(repository)

        logger.info("🌿 repository registered", repository_id=repository.id, path=repository.local_path)
        return repository


class WorktreeService:
    def __init__(self, context: ServiceContext, git: GitRepositoryAdapterProtocol | None = None) -> None:
        self.context = context
        self.git = git or GitRepositoryAdapter()

    def list_worktrees(self, project_id: str | None = None) -> list[Worktree]:
        stmt = select(Worktree).order_by(Worktree.created_at.desc())
        if project_id is not None:
            stmt = stmt.join(Repository, Repository.id == Worktree.repository_id).where(Repository.project_id == project_id)
        return list(self.context.db.scalars(stmt))

    def get_worktree(self, worktree_id: str) -> Worktree:
        worktree = self.context.db.get(Worktree, worktree_id)
        if worktree is None:
            raise ValueError("Worktree not found")
        return worktree

    def create_worktree(self, payload: WorktreeCreate) -> Worktree:
        repository = self.context.db.get(Repository, payload.repository_id)
        if repository is None:
            raise ValueError("Repository not found")

        task = None
        branch_suffix = "workspace"
        if payload.task_id is not None:
            task = self.context.db.get(Task, payload.task_id)
            if task is None:
                raise ValueError("Task not found")
            branch_suffix = f"{task_slug(task.title)}-{task.id[:8]}"
        elif payload.label:
            branch_suffix = task_slug(payload.label)

        repo_path = Path(repository.local_path)
        project = self.context.db.get(Project, repository.project_id)
        if project is None:
            raise ValueError("Project not found")

        branch_name = f"acp/{project.slug}/{branch_suffix}"
        root_path = settings.runtime_home / "worktrees" / project.slug
        root_path.mkdir(parents=True, exist_ok=True)
        worktree_path = root_path / branch_suffix

        if self.context.db.scalar(select(Worktree.id).where(Worktree.path == str(worktree_path))) is not None:
            raise ValueError("Worktree path already allocated")

        if worktree_path.exists():
            raise ValueError("Worktree directory already exists on disk")

        branch_exists = self.git.branch_exists(repo_path, branch_name)
        if branch_exists:
            source_ref = branch_name
            self.git.add_worktree(
                repo_path,
                worktree_path,
                branch_name=branch_name,
                source_ref=source_ref,
                create_branch=False,
            )
        else:
            active_branch = self.git.current_branch_name(repo_path) or "HEAD"
            source_ref = repository.default_branch or active_branch
            self.git.add_worktree(
                repo_path,
                worktree_path,
                branch_name=branch_name,
                source_ref=source_ref,
                create_branch=True,
            )

        worktree = Worktree(
            repository_id=repository.id,
            task_id=task.id if task else None,
            branch_name=branch_name,
            path=str(worktree_path),
            status="active",
            metadata_json={
                "project_slug": project.slug,
                "source_ref": source_ref,
                "label": payload.label,
            },
        )
        self.context.db.add(worktree)
        self.context.db.flush()
        self.context.record_event(
            entity_type="worktree",
            entity_id=worktree.id,
            event_type="worktree.created",
            payload_json={
                "repository_id": repository.id,
                "task_id": task.id if task else None,
                "branch_name": branch_name,
                "path": worktree.path,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(worktree)

        logger.info("🌿 worktree allocated", worktree_id=worktree.id, branch=worktree.branch_name, path=worktree.path)
        return worktree

    def patch_worktree(self, worktree_id: str, payload: WorktreePatch) -> Worktree:
        worktree = self.get_worktree(worktree_id)
        repository = self.context.db.get(Repository, worktree.repository_id)
        if repository is None:
            raise ValueError("Repository not found")

        next_status = payload.status
        if next_status is None:
            raise ValueError("No worktree change requested")

        allowed = {
            "active": {"locked", "archived"},
            "locked": {"archived"},
            "archived": {"pruned"},
        }
        if next_status not in allowed.get(worktree.status, set()):
            raise ValueError(f"Invalid worktree transition from {worktree.status} to {next_status}")

        repo_path = Path(repository.local_path)
        worktree_path = Path(worktree.path)

        if next_status == "locked":
            worktree.status = "locked"
            worktree.lock_reason = payload.lock_reason or "Locked by operator"
        elif next_status == "archived":
            worktree.status = "archived"
        elif next_status == "pruned":
            self.git.remove_worktree(repo_path, worktree_path)
            worktree.status = "pruned"

        self.context.record_event(
            entity_type="worktree",
            entity_id=worktree.id,
            event_type="worktree.updated",
            payload_json={"status": worktree.status, "lock_reason": worktree.lock_reason},
        )
        self.context.db.commit()
        self.context.db.refresh(worktree)

        logger.info("🌿 worktree updated", worktree_id=worktree.id, status=worktree.status)
        return worktree


class SessionService:
    def __init__(self, context: ServiceContext, runtime: RuntimeAdapterProtocol | None = None) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()

    def list_sessions(self, project_id: str | None = None, task_id: str | None = None) -> list[AgentSession]:
        stmt = select(AgentSession).order_by(AgentSession.created_at.desc())
        if project_id is not None:
            stmt = stmt.where(AgentSession.project_id == project_id)
        if task_id is not None:
            stmt = stmt.where(AgentSession.task_id == task_id)
        return list(self.context.db.scalars(stmt))

    def get_session(self, session_id: str) -> AgentSession:
        session = self.context.db.get(AgentSession, session_id)
        if session is None:
            raise ValueError("Session not found")
        return session

    @staticmethod
    def _session_family_id(session: AgentSession) -> str:
        family_id = session.runtime_metadata.get("session_family_id")
        if isinstance(family_id, str) and family_id:
            return family_id
        return session.id

    def _resolve_session_target(
        self,
        *,
        repository_id: str | None,
        worktree_id: str | None,
    ) -> tuple[str | None, Worktree | None, Path]:
        resolved_repository_id = repository_id
        worktree = None
        working_directory = settings.runtime_home

        if worktree_id is not None:
            worktree = self.context.db.get(Worktree, worktree_id)
            if worktree is None:
                raise ValueError("Worktree not found")
            resolved_repository_id = worktree.repository_id
            working_directory = Path(worktree.path)
        elif resolved_repository_id is not None:
            repository = self.context.db.get(Repository, resolved_repository_id)
            if repository is None:
                raise ValueError("Repository not found")
            working_directory = Path(repository.local_path)

        return resolved_repository_id, worktree, working_directory

    def _next_attempt_number(self, task_id: str) -> int:
        existing = self.list_sessions(task_id=task_id)
        if existing:
            return len(existing) + 1
        return 1

    def _spawn_session_record(
        self,
        *,
        task: Task,
        profile: str,
        repository_id: str | None = None,
        worktree_id: str | None = None,
        command: str | None = None,
        runtime_metadata_extra: dict[str, Any] | None = None,
        run_summary: str | None = None,
        message_body: str | None = None,
    ) -> AgentSession:
        repository_id, worktree, working_directory = self._resolve_session_target(
            repository_id=repository_id,
            worktree_id=worktree_id,
        )
        attempt_number = self._next_attempt_number(task.id)
        session_name = safe_tmux_name(f"acp-{task.project_id[:6]}-{task.id[:8]}-{profile}-{attempt_number}")
        runtime_info = self.runtime.spawn_session(
            session_name=session_name,
            working_directory=working_directory,
            profile=profile,
            command=command,
        )

        runtime_metadata = {
            "pane_id": runtime_info.pane_id,
            "window_name": runtime_info.window_name,
            "working_directory": runtime_info.working_directory,
            "command": runtime_info.command,
        }
        if runtime_metadata_extra:
            runtime_metadata.update(runtime_metadata_extra)

        session = AgentSession(
            project_id=task.project_id,
            task_id=task.id,
            repository_id=repository_id,
            worktree_id=worktree_id,
            profile=profile,
            status="running",
            session_name=runtime_info.session_name,
            runtime_metadata=runtime_metadata,
        )
        self.context.db.add(session)
        self.context.db.flush()

        self.context.db.add(
            AgentRun(
                session_id=session.id,
                attempt_number=attempt_number,
                status="running",
                summary=run_summary or f"{profile} session launched",
                runtime_metadata=runtime_metadata,
            )
        )
        self.context.db.add(
            SessionMessage(
                session_id=session.id,
                message_type="system",
                source="control-plane",
                body=message_body or f"📡 Spawned {profile} session in {runtime_info.working_directory}",
                payload_json={"session_name": runtime_info.session_name},
            )
        )

        if worktree is not None:
            worktree.session_id = session.id

        return session

    def spawn_session(self, payload: AgentSessionCreate) -> AgentSession:
        task = self.context.db.get(Task, payload.task_id)
        if task is None:
            raise ValueError("Task not found")

        session = self._spawn_session_record(
            task=task,
            profile=payload.profile,
            repository_id=payload.repository_id,
            worktree_id=payload.worktree_id,
            command=payload.command,
            runtime_metadata_extra={"session_family_id": None},
        )
        session.runtime_metadata = {**session.runtime_metadata, "session_family_id": session.id}

        self.context.record_event(
            entity_type="session",
            entity_id=session.id,
            event_type="session.spawned",
            payload_json={
                "task_id": task.id,
                "profile": payload.profile,
                "session_name": session.session_name,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(session)

        logger.info("📡 session spawned", session_id=session.id, session_name=session.session_name)
        return session

    def spawn_follow_up_session(self, source_session_id: str, payload: AgentSessionFollowUpCreate) -> AgentSession:
        source = self.get_session(source_session_id)
        task = self.context.db.get(Task, source.task_id)
        if task is None:
            raise ValueError("Task not found")

        follow_up_type = payload.follow_up_type
        if follow_up_type is None:
            if payload.profile == source.profile:
                follow_up_type = "retry"
            elif payload.profile == "reviewer":
                follow_up_type = "review"
            elif payload.profile == "verifier":
                follow_up_type = "verify"
            else:
                follow_up_type = "handoff"

        repository_id = source.repository_id if payload.reuse_repository else None
        worktree_id = source.worktree_id if payload.reuse_worktree else None
        family_id = self._session_family_id(source)
        session = self._spawn_session_record(
            task=task,
            profile=payload.profile,
            repository_id=repository_id,
            worktree_id=worktree_id,
            command=payload.command,
            runtime_metadata_extra={
                "session_family_id": family_id,
                "follow_up_of_session_id": source.id,
                "follow_up_type": follow_up_type,
                "source_profile": source.profile,
            },
            run_summary=f"{payload.profile} {follow_up_type} session launched from {source.profile}",
            message_body=(
                f"🧭 Spawned {payload.profile} {follow_up_type} session from {source.session_name}"
            ),
        )

        self.context.db.add(
            SessionMessage(
                session_id=source.id,
                message_type="system",
                source="control-plane",
                body=f"🧭 Follow-up {payload.profile} session queued as {session.session_name}",
                payload_json={"follow_up_session_id": session.id, "follow_up_type": follow_up_type},
            )
        )
        self.context.record_event(
            entity_type="session",
            entity_id=source.id,
            event_type="session.follow_up_requested",
            payload_json={
                "follow_up_session_id": session.id,
                "follow_up_type": follow_up_type,
                "profile": payload.profile,
            },
        )
        self.context.record_event(
            entity_type="session",
            entity_id=session.id,
            event_type="session.follow_up_spawned",
            payload_json={
                "task_id": task.id,
                "source_session_id": source.id,
                "follow_up_type": follow_up_type,
                "profile": payload.profile,
                "session_family_id": family_id,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(session)

        logger.info(
            "🧭 session follow-up spawned",
            session_id=session.id,
            source_session_id=source.id,
            follow_up_type=follow_up_type,
        )
        return session

    def refresh_session_status(self, session_id: str) -> AgentSession:
        session = self.get_session(session_id)
        if session.status in {"cancelled", "failed"}:
            return session
        exists = self.runtime.session_exists(session.session_name)
        if session.status == "waiting_human" and exists:
            next_status = "waiting_human"
        else:
            next_status = "running" if exists else "done"
        if session.status != next_status:
            session.status = next_status
            self.context.record_event(
                entity_type="session",
                entity_id=session.id,
                event_type="session.status_refreshed",
                payload_json={"status": next_status},
            )
            self.context.db.commit()
            self.context.db.refresh(session)
        return session

    def tail_session(self, session_id: str, *, lines: int = 80) -> SessionTailRead:
        session = self.refresh_session_status(session_id)
        capture_lines: list[str]
        if session.status == "running":
            capture_lines = self.runtime.capture_tail(session.session_name, lines=lines).splitlines()
        else:
            capture_lines = ["📡 Session is not currently running."]

        recent_messages = list(
            self.context.db.scalars(
                select(SessionMessage)
                .where(SessionMessage.session_id == session.id)
                .order_by(SessionMessage.created_at.desc())
                .limit(12)
            )
        )
        return SessionTailRead(
            session=AgentSessionRead.model_validate(session),
            lines=capture_lines[-lines:],
            recent_messages=[SessionMessageRead.model_validate(item) for item in recent_messages],
        )

    def get_session_timeline(self, session_id: str, *, message_limit: int = 40, event_limit: int = 20) -> SessionTimelineRead:
        session = self.refresh_session_status(session_id)
        family_id = self._session_family_id(session)
        runs = list(
            self.context.db.scalars(
                select(AgentRun)
                .where(AgentRun.session_id == session.id)
                .order_by(AgentRun.attempt_number.asc(), AgentRun.created_at.asc())
            )
        )
        messages = list(
            self.context.db.scalars(
                select(SessionMessage)
                .where(SessionMessage.session_id == session.id)
                .order_by(SessionMessage.created_at.desc())
                .limit(message_limit)
            )
        )
        waiting_questions = list(
            self.context.db.scalars(
                select(WaitingQuestion)
                .where(WaitingQuestion.session_id == session.id)
                .order_by(WaitingQuestion.created_at.desc())
            )
        )
        events = list(
            self.context.db.scalars(
                select(Event)
                .where(
                    or_(
                        (Event.entity_type == "session") & (Event.entity_id == session.id),
                        cast(Event.payload_json, String).like(f'%"{session.id}"%'),
                    )
                )
                .order_by(Event.created_at.desc())
                .limit(event_limit)
            )
        )
        related_sessions = [
            item
            for item in self.context.db.scalars(
                select(AgentSession)
                .where(AgentSession.task_id == session.task_id)
                .order_by(AgentSession.created_at.asc())
            )
            if self._session_family_id(item) == family_id
        ]
        return SessionTimelineRead(
            session=AgentSessionRead.model_validate(session),
            runs=[AgentRunRead.model_validate(item) for item in runs],
            messages=[SessionMessageRead.model_validate(item) for item in messages],
            waiting_questions=[WaitingQuestionRead.model_validate(item) for item in waiting_questions],
            events=[EventRecord.model_validate(item) for item in events],
            related_sessions=[AgentSessionRead.model_validate(item) for item in related_sessions],
        )

    def cancel_session(self, session_id: str) -> AgentSession:
        session = self.get_session(session_id)
        if session.status in {"done", "failed", "cancelled"}:
            return session

        self.runtime.terminate_session(session.session_name)
        session.status = "cancelled"

        latest_run = self.context.db.scalar(
            select(AgentRun)
            .where(AgentRun.session_id == session.id)
            .order_by(AgentRun.attempt_number.desc(), AgentRun.created_at.desc())
        )
        if latest_run is not None:
            latest_run.status = "cancelled"
            latest_run.summary = "Session cancelled by operator"

        self.context.db.add(
            SessionMessage(
                session_id=session.id,
                message_type="system",
                source="control-plane",
                body="⚠️ Session cancelled by operator",
                payload_json={},
            )
        )
        self.context.record_event(
            entity_type="session",
            entity_id=session.id,
            event_type="session.cancelled",
            payload_json={"task_id": session.task_id, "session_name": session.session_name},
        )
        self.context.db.commit()
        self.context.db.refresh(session)

        logger.info("⚠️ session cancelled", session_id=session.id, session_name=session.session_name)
        return session


class BootstrapService:
    def __init__(
        self,
        context: ServiceContext,
        runtime: RuntimeAdapterProtocol | None = None,
        git: GitRepositoryAdapterProtocol | None = None,
        scaffold_writer: ScaffoldWriterProtocol | None = None,
    ) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()
        self.git = git or GitRepositoryAdapter()
        self.scaffold_writer = scaffold_writer or ScaffoldWriter()

    @staticmethod
    def _repo_has_user_files(repo_path: Path) -> bool:
        for entry in repo_path.iterdir():
            if entry.name == ".git":
                continue
            return True
        return False

    def _git_identity(self, repo_path: Path) -> tuple[str, str]:
        return self.git.ensure_identity(repo_path)

    def _ensure_line(self, path: Path, line: str) -> None:
        self.scaffold_writer.ensure_line(path, line)

    def _ensure_agents_file(self, repo_path: Path) -> None:
        self.scaffold_writer.ensure_agents_file(repo_path)

    def _scaffold_repo(
        self,
        repo_path: Path,
        *,
        project_name: str,
        description: str | None,
        stack_preset: StackPreset,
    ) -> bool:
        return self.scaffold_writer.scaffold_repo(
            repo_path,
            project_name=project_name,
            description=description,
            stack_preset=stack_preset,
        )

    def _commit_initial_state(self, repo_path: Path) -> None:
        self._git_identity(repo_path)
        self.git.commit_all_if_needed(repo_path, "chore: bootstrap project")

    def _default_repo_branch(self, repo_path: Path) -> str:
        branch_name = self.git.current_branch_name(repo_path)
        if branch_name:
            return branch_name
        raise ValueError("Repository is in detached HEAD; check out a branch or enable worktree kickoff")

    def _write_project_local_files(
        self,
        *,
        repository_root: Path,
        execution_root: Path,
        project: Project,
        repository: Repository,
        kickoff_task: Task,
        payload: ProjectBootstrapCreate,
    ) -> None:
        local_payload = {
            "project_id": project.id,
            "api_base_url": settings.api_base_url,
            "stack_preset": payload.stack_preset.value,
            "stack_notes": payload.stack_notes,
            "repo_path": str(repository_root),
            "kickoff_task_id": kickoff_task.id,
            "use_worktree": payload.use_worktree,
            "execution_path": str(execution_root),
        }
        prompt_body = textwrap.dedent(
            f"""
            You are the kickoff coding agent for the project "{project.name}".

            Start by reading `AGENTS.md` and `.acp/project.local.json`.

            The Agent Control Plane MCP server named `{settings.bootstrap_agent_mcp_name}` is available for board updates.
            Use it to:
            - inspect project and board state
            - create top-level tasks and one-level subtasks
            - open waiting questions when requirements are unclear
            - add comments, checks, and artifacts as planning evidence
            - keep the kickoff task updated while you break down the work

            Focus on planning first:
            - inspect the repository and scaffold
            - clarify missing requirements with the operator through ACP waiting questions
            - create or refine the ACP task tree for the initial scope
            - keep the board aligned with the real work

            Operator kickoff prompt:
            {payload.initial_prompt}

            Stack preset: {payload.stack_preset.value}
            Stack notes: {payload.stack_notes or "None"}
            Kickoff task id: {kickoff_task.id}
            """
        ).strip() + "\n"

        targets = {repository_root}
        if execution_root != repository_root:
            targets.add(execution_root)
        self.scaffold_writer.write_project_local_files(
            targets=targets,
            local_payload=local_payload,
            prompt_body=prompt_body,
        )

    def _build_session_command(self, execution_root: Path) -> str:
        return self.scaffold_writer.build_bootstrap_command(execution_root)

    def bootstrap_project(self, payload: ProjectBootstrapCreate) -> ProjectBootstrapRead:
        repo_path = Path(payload.repo_path).expanduser().resolve()
        if not repo_path.exists():
            if not payload.initialize_repo:
                raise ValueError("Repo path must point to an existing directory or enable Initialize repo with git")
            repo_path.mkdir(parents=True, exist_ok=True)
        elif not repo_path.is_dir():
            raise ValueError("Repo path must point to a directory")

        repo_initialized = False
        try:
            repo_details = self.git.inspect_repository(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError):
            if not payload.initialize_repo:
                raise ValueError("Repo path must already be a git repository or enable Initialize repo with git")
            if any(repo_path.iterdir()):
                raise ValueError("Initialize repo with git is only available for an empty directory")
            self.git.init_repository(repo_path)
            repo_details = self.git.inspect_repository(repo_path)
            repo_initialized = True

        has_commits = bool(repo_details.metadata_json.get("has_commits"))
        is_detached = bool(repo_details.metadata_json.get("is_detached"))
        if has_commits and not payload.use_worktree and is_detached:
            raise ValueError("Repository is in detached HEAD; check out a branch or enable worktree kickoff")

        project = ProjectService(self.context).create_project(
            ProjectCreate(name=payload.name, description=payload.description)
        )

        scaffold_applied = False
        if not has_commits:
            scaffold_applied = self._scaffold_repo(
                repo_path,
                project_name=payload.name,
                description=payload.description,
                stack_preset=payload.stack_preset,
            )
            self._ensure_line(repo_path / ".gitignore", ".acp/")
            self._ensure_agents_file(repo_path)
            self._commit_initial_state(repo_path)
        else:
            self._ensure_line(repo_path / ".gitignore", ".acp/")
            self._ensure_agents_file(repo_path)

        repository = RepositoryService(self.context).create_repository(
            RepositoryCreate(project_id=project.id, local_path=str(repo_path), name=repo_path.name)
        )

        task_description = textwrap.dedent(
            f"""
            Initial operator prompt:

            {payload.initial_prompt}

            Stack preset: {payload.stack_preset.value}
            Stack notes: {payload.stack_notes or "None"}
            """
        ).strip()
        kickoff_task = TaskService(self.context).create_task(
            TaskCreate(
                project_id=project.id,
                title="Kick off planning and board setup",
                description=task_description,
                board_column_key="in_progress",
            )
        )

        kickoff_worktree = None
        execution_path = repo_path
        execution_branch = ""
        if payload.use_worktree:
            kickoff_worktree = WorktreeService(self.context).create_worktree(
                WorktreeCreate(repository_id=repository.id, task_id=kickoff_task.id)
            )
            execution_path = Path(kickoff_worktree.path)
            execution_branch = kickoff_worktree.branch_name
        else:
            execution_branch = self._default_repo_branch(repo_path)

        self._write_project_local_files(
            repository_root=repo_path,
            execution_root=execution_path,
            project=project,
            repository=repository,
            kickoff_task=kickoff_task,
            payload=payload,
        )
        session = SessionService(self.context, runtime=self.runtime).spawn_session(
            AgentSessionCreate(
                task_id=kickoff_task.id,
                profile="executor",
                repository_id=repository.id if not payload.use_worktree else None,
                worktree_id=kickoff_worktree.id if kickoff_worktree else None,
                command=self._build_session_command(execution_path),
            )
        )

        project.settings_json = {
            **project.settings_json,
            "bootstrap": {
                "stack_preset": payload.stack_preset.value,
                "stack_notes": payload.stack_notes,
                "repository_id": repository.id,
                "kickoff_task_id": kickoff_task.id,
                "kickoff_session_id": session.id,
                "kickoff_worktree_id": kickoff_worktree.id if kickoff_worktree else None,
                "use_worktree": payload.use_worktree,
                "execution_path": str(execution_path),
            },
        }
        self.context.record_event(
            entity_type="project",
            entity_id=project.id,
            event_type="project.bootstrapped",
            payload_json={
                "repository_id": repository.id,
                "kickoff_task_id": kickoff_task.id,
                "kickoff_session_id": session.id,
                "kickoff_worktree_id": kickoff_worktree.id if kickoff_worktree else None,
                "execution_path": str(execution_path),
                "execution_branch": execution_branch,
                "stack_preset": payload.stack_preset.value,
                "stack_notes": payload.stack_notes,
                "use_worktree": payload.use_worktree,
                "repo_initialized": repo_initialized,
                "scaffold_applied": scaffold_applied,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(project)
        self.context.db.refresh(repository)
        self.context.db.refresh(kickoff_task)
        self.context.db.refresh(session)
        if kickoff_worktree is not None:
            self.context.db.refresh(kickoff_worktree)

        logger.info(
            "🧭 project bootstrapped",
            project_id=project.id,
            repository_id=repository.id,
            kickoff_task_id=kickoff_task.id,
            session_id=session.id,
            use_worktree=payload.use_worktree,
        )
        return ProjectBootstrapRead(
            project=ProjectSummary.model_validate(project),
            repository=RepositoryRead.model_validate(repository),
            kickoff_task=TaskRead.model_validate(kickoff_task),
            kickoff_session=AgentSessionRead.model_validate(session),
            kickoff_worktree=WorktreeRead.model_validate(kickoff_worktree) if kickoff_worktree else None,
            execution_path=str(execution_path),
            execution_branch=execution_branch,
            stack_preset=payload.stack_preset,
            stack_notes=payload.stack_notes,
            use_worktree=payload.use_worktree,
            repo_initialized=repo_initialized,
            scaffold_applied=scaffold_applied,
        )


class WaitingService:
    def __init__(self, context: ServiceContext, runtime: RuntimeAdapterProtocol | None = None) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()

    def list_questions(self, project_id: str | None = None, status: str | None = None) -> list[WaitingQuestion]:
        stmt = select(WaitingQuestion).order_by(WaitingQuestion.created_at.desc())
        if project_id is not None:
            stmt = stmt.where(WaitingQuestion.project_id == project_id)
        if status is not None:
            stmt = stmt.where(WaitingQuestion.status == status)
        return list(self.context.db.scalars(stmt))

    def get_question(self, question_id: str) -> WaitingQuestion:
        question = self.context.db.get(WaitingQuestion, question_id)
        if question is None:
            raise ValueError("Waiting question not found")
        return question

    def open_question(self, payload: WaitingQuestionCreate) -> WaitingQuestion:
        task = self.context.db.get(Task, payload.task_id)
        if task is None:
            raise ValueError("Task not found")

        session = None
        if payload.session_id is not None:
            session = self.context.db.get(AgentSession, payload.session_id)
            if session is None:
                raise ValueError("Session not found")
            if session.task_id != task.id:
                raise ValueError("Session must belong to the same task")

        question = WaitingQuestion(
            project_id=task.project_id,
            task_id=task.id,
            session_id=session.id if session else None,
            status="open",
            prompt=payload.prompt,
            blocked_reason=payload.blocked_reason,
            urgency=payload.urgency,
            options_json=payload.options_json,
        )
        task.waiting_for_human = True
        if session is not None:
            session.status = "waiting_human"
            self.context.db.add(
                SessionMessage(
                    session_id=session.id,
                    message_type="waiting_question",
                    source="control-plane",
                    body=f"💬 Waiting for human input: {payload.prompt}",
                    payload_json={"urgency": payload.urgency},
                )
            )

        self.context.db.add(question)
        self.context.db.flush()
        self.context.record_event(
            entity_type="waiting_question",
            entity_id=question.id,
            event_type="waiting_question.opened",
            payload_json={
                "task_id": task.id,
                "session_id": session.id if session else None,
                "urgency": payload.urgency,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(question)

        logger.info("💬 waiting question opened", question_id=question.id, task_id=task.id)
        return question

    def answer_question(self, question_id: str, payload: HumanReplyCreate) -> WaitingQuestion:
        question = self.get_question(question_id)
        if question.status != "open":
            raise ValueError("Question is not open")

        reply = HumanReply(
            question_id=question.id,
            responder_name=payload.responder_name,
            body=payload.body,
            payload_json=payload.payload_json,
        )
        self.context.db.add(reply)

        task = self.context.db.get(Task, question.task_id)
        if task is not None:
            task.waiting_for_human = False

        if question.session_id is not None:
            session = self.context.db.get(AgentSession, question.session_id)
            if session is not None:
                session_exists = self.runtime.session_exists(session.session_name)
                session.status = "running" if session_exists else "done"
                self.context.db.add(
                    SessionMessage(
                        session_id=session.id,
                        message_type="human_reply",
                        source=payload.responder_name,
                        body=f"💬 Human replied: {payload.body}",
                        payload_json=payload.payload_json,
                    )
                )

        question.status = "answered"
        self.context.db.flush()
        self.context.record_event(
            entity_type="waiting_question",
            entity_id=question.id,
            event_type="waiting_question.answered",
            payload_json={"responder_name": payload.responder_name},
        )
        self.context.db.commit()
        self.context.db.refresh(question)

        logger.info("💬 waiting question answered", question_id=question.id, responder=payload.responder_name)
        return question

    def get_question_detail(self, question_id: str) -> WaitingQuestionDetail:
        question = self.get_question(question_id)
        replies = list(
            self.context.db.scalars(
                select(HumanReply).where(HumanReply.question_id == question.id).order_by(HumanReply.created_at.asc())
            )
        )
        detail = WaitingQuestionDetail.model_validate(question)
        detail.replies = [HumanReplyRead.model_validate(item) for item in replies]
        return detail


class EventService:
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
    def __init__(self, context: ServiceContext, runtime: RuntimeAdapterProtocol | None = None) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()

    def reconcile_runtime_sessions(self) -> dict[str, Any]:
        tracked_runtime_sessions = {
            session.session_name: session
            for session in self.context.db.scalars(
                select(AgentSession).where(AgentSession.status.in_(["running", "waiting_human", "blocked"]))
            )
        }
        runtime_sessions = self.runtime.list_sessions(prefix="acp-")
        runtime_session_names = {item.session_name for item in runtime_sessions}
        reconciled = 0

        for session_name, session in tracked_runtime_sessions.items():
            next_status = None
            if session.status == "waiting_human" and session_name in runtime_session_names:
                next_status = "waiting_human"
            elif session_name in runtime_session_names:
                next_status = "running"
            elif session.status != "cancelled":
                next_status = "done"

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
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_issues(self, *, project_id: str | None = None, task_id: str | None = None) -> list[WorktreeHygieneIssueRead]:
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
    def __init__(self, context: ServiceContext, runtime: RuntimeAdapterProtocol | None = None) -> None:
        self.context = context
        self.runtime = runtime or DefaultRuntimeAdapter()

    def get_diagnostics(self) -> DiagnosticsRead:
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
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def get_dashboard(self) -> DashboardRead:
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
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def search(self, query: str, project_id: str | None = None, limit: int = 20) -> SearchResults:
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
from acp_core.schemas import BoardColumnRead, EventRecord, ProjectOverview, ProjectSummary, TaskRead  # noqa: E402

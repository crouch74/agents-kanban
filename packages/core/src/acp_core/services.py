from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from re import sub
from shutil import which
import subprocess
from typing import Any

from git import InvalidGitRepositoryError, NoSuchPathError, Repo
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from acp_core.constants import DEFAULT_BOARD_COLUMNS, TASK_TRANSITIONS, WORKFLOW_BY_COLUMN_KEY
from acp_core.logging import logger
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
from acp_core.runtime import TmuxRuntimeAdapter, safe_tmux_name
from acp_core.schemas import (
    AgentSessionCreate,
    AgentSessionRead,
    BoardView,
    DashboardRead,
    DiagnosticsRead,
    HumanReplyCreate,
    HumanReplyRead,
    ProjectCreate,
    RepositoryCreate,
    RepositoryRead,
    SearchHit,
    SearchResults,
    TaskArtifactCreate,
    TaskArtifactRead,
    TaskCheckCreate,
    TaskCheckRead,
    TaskCommentCreate,
    TaskCommentRead,
    TaskDependencyRead,
    WaitingQuestionCreate,
    WaitingQuestionDetail,
    WaitingQuestionRead,
    TaskCreate,
    TaskDetail,
    TaskPatch,
    SessionTailRead,
    SessionMessageRead,
    WorktreeCreate,
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

    def record_event(
        self,
        *,
        entity_type: str,
        entity_id: str,
        event_type: str,
        payload_json: dict[str, Any],
    ) -> Event:
        event = Event(
            actor_type=self.actor_type,
            actor_name=self.actor_name,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
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

    def patch_task(self, task_id: str, payload: TaskPatch) -> Task:
        task = self.get_task(task_id)
        provided = payload.model_fields_set

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
            task.workflow_state = payload.workflow_state

        if "board_column_id" in provided and payload.board_column_id is not None:
            column = self.context.db.get(BoardColumn, payload.board_column_id)
            if column is None:
                raise ValueError("Board column not found")
            task.board_column_id = column.id
            task.workflow_state = WORKFLOW_BY_COLUMN_KEY.get(column.key, task.workflow_state)

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
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

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

    def create_repository(self, payload: RepositoryCreate) -> Repository:
        project = self.context.db.get(Project, payload.project_id)
        if project is None:
            raise ValueError("Project not found")

        repo_path = Path(payload.local_path).expanduser().resolve()
        try:
            git_repo = Repo(repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise ValueError("Local path must point to a git repository") from exc

        default_branch = None
        if git_repo.head.is_valid():
            try:
                default_branch = git_repo.active_branch.name
            except TypeError:
                default_branch = git_repo.head.reference.name

        remotes = [remote.name for remote in git_repo.remotes]
        metadata_json = {
            "is_dirty": git_repo.is_dirty(untracked_files=True),
            "head_commit": git_repo.head.commit.hexsha if git_repo.head.is_valid() else None,
            "remotes": remotes,
            "working_dir": str(git_repo.working_tree_dir or repo_path),
        }

        repository = Repository(
            project_id=payload.project_id,
            name=payload.name or repo_path.name,
            local_path=str(repo_path),
            default_branch=default_branch,
            metadata_json=metadata_json,
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
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

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
        git_repo = Repo(repo_path)
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

        branch_exists = branch_name in [head.name for head in git_repo.heads]
        if branch_exists:
            source_ref = branch_name
            git_repo.git.worktree("add", str(worktree_path), source_ref)
        else:
            try:
                active_branch = git_repo.active_branch.name if git_repo.head.is_valid() else "HEAD"
            except TypeError:
                active_branch = git_repo.head.reference.name if git_repo.head.is_valid() else "HEAD"
            source_ref = repository.default_branch or active_branch
            git_repo.git.worktree("add", "-b", branch_name, str(worktree_path), source_ref)

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

        git_repo = Repo(Path(repository.local_path))
        worktree_path = Path(worktree.path)

        if next_status == "locked":
            worktree.status = "locked"
            worktree.lock_reason = payload.lock_reason or "Locked by operator"
        elif next_status == "archived":
            worktree.status = "archived"
        elif next_status == "pruned":
            git_repo.git.worktree("remove", "--force", str(worktree_path))
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
    def __init__(self, context: ServiceContext, runtime: TmuxRuntimeAdapter | None = None) -> None:
        self.context = context
        self.runtime = runtime or TmuxRuntimeAdapter()

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

    def spawn_session(self, payload: AgentSessionCreate) -> AgentSession:
        task = self.context.db.get(Task, payload.task_id)
        if task is None:
            raise ValueError("Task not found")

        repository_id = payload.repository_id
        worktree = None
        if payload.worktree_id is not None:
            worktree = self.context.db.get(Worktree, payload.worktree_id)
            if worktree is None:
                raise ValueError("Worktree not found")
            repository_id = worktree.repository_id

        working_directory = settings.runtime_home
        if worktree is not None:
            working_directory = Path(worktree.path)
        elif repository_id is not None:
            repository = self.context.db.get(Repository, repository_id)
            if repository is None:
                raise ValueError("Repository not found")
            working_directory = Path(repository.local_path)

        attempt_number = 1
        existing = self.list_sessions(task_id=task.id)
        if existing:
            attempt_number = len(existing) + 1

        session_name = safe_tmux_name(f"acp-{task.project_id[:6]}-{task.id[:8]}-{payload.profile}-{attempt_number}")
        runtime_info = self.runtime.spawn_session(
            session_name=session_name,
            working_directory=working_directory,
            profile=payload.profile,
            command=payload.command,
        )

        session = AgentSession(
            project_id=task.project_id,
            task_id=task.id,
            repository_id=repository_id,
            worktree_id=payload.worktree_id,
            profile=payload.profile,
            status="running",
            session_name=runtime_info.session_name,
            runtime_metadata={
                "pane_id": runtime_info.pane_id,
                "window_name": runtime_info.window_name,
                "working_directory": runtime_info.working_directory,
                "command": runtime_info.command,
            },
        )
        self.context.db.add(session)
        self.context.db.flush()

        run = AgentRun(
            session_id=session.id,
            attempt_number=attempt_number,
            status="running",
            summary=f"{payload.profile} session launched",
            runtime_metadata=session.runtime_metadata,
        )
        self.context.db.add(run)
        self.context.db.add(
            SessionMessage(
                session_id=session.id,
                message_type="system",
                source="control-plane",
                body=f"📡 Spawned {payload.profile} session in {runtime_info.working_directory}",
                payload_json={"session_name": runtime_info.session_name},
            )
        )

        if worktree is not None:
            worktree.session_id = session.id

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

    def refresh_session_status(self, session_id: str) -> AgentSession:
        session = self.get_session(session_id)
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


class WaitingService:
    def __init__(self, context: ServiceContext, runtime: TmuxRuntimeAdapter | None = None) -> None:
        self.context = context
        self.runtime = runtime or TmuxRuntimeAdapter()

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


class DiagnosticsService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

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
            result = subprocess.run(
                ["tmux", "list-sessions"],
                capture_output=True,
                text=True,
                check=False,
            )
            tmux_server_running = result.returncode == 0
        return DiagnosticsRead(
            app_name=settings.app_name,
            environment=settings.app_env,
            database_path=str(settings.database_path),
            runtime_home=str(settings.runtime_home),
            tmux_available=which("tmux") is not None,
            tmux_server_running=tmux_server_running,
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
        waiting_count = self.context.db.scalar(select(func.count(WaitingQuestion.id)).where(WaitingQuestion.status == "open")) or 0
        blocked_count = self.context.db.scalar(select(func.count(Task.id)).where(Task.blocked_reason.is_not(None))) or 0
        running_sessions = self.context.db.scalar(select(func.count(AgentSession.id)).where(AgentSession.status == "running")) or 0
        return DashboardRead(
            projects=[ProjectSummary.model_validate(project) for project in projects],
            recent_events=[EventRecord.model_validate(event) for event in events],
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

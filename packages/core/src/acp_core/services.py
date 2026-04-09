from __future__ import annotations

from dataclasses import dataclass
from re import sub
from shutil import which
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from acp_core.constants import DEFAULT_BOARD_COLUMNS, TASK_TRANSITIONS, WORKFLOW_BY_COLUMN_KEY
from acp_core.logging import logger
from acp_core.models import Board, BoardColumn, Event, Project, Task
from acp_core.schemas import BoardView, DashboardRead, DiagnosticsRead, ProjectCreate, TaskCreate, TaskPatch
from acp_core.settings import settings


def slugify(value: str) -> str:
    normalized = sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "project"


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


class DiagnosticsService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def get_diagnostics(self) -> DiagnosticsRead:
        project_count = self.context.db.scalar(select(func.count(Project.id))) or 0
        task_count = self.context.db.scalar(select(func.count(Task.id))) or 0
        return DiagnosticsRead(
            app_name=settings.app_name,
            environment=settings.app_env,
            database_path=str(settings.database_path),
            runtime_home=str(settings.runtime_home),
            tmux_available=which("tmux") is not None,
            git_available=which("git") is not None,
            current_project_count=project_count,
            current_task_count=task_count,
        )


class DashboardService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def get_dashboard(self) -> DashboardRead:
        projects = list(self.context.db.scalars(select(Project).order_by(Project.created_at.desc()).limit(8)))
        events = list(self.context.db.scalars(select(Event).order_by(Event.created_at.desc()).limit(12)))
        waiting_count = self.context.db.scalar(select(func.count(Task.id)).where(Task.waiting_for_human.is_(True))) or 0
        blocked_count = self.context.db.scalar(select(func.count(Task.id)).where(Task.blocked_reason.is_not(None))) or 0
        return DashboardRead(
            projects=[ProjectSummary.model_validate(project) for project in projects],
            recent_events=[EventRecord.model_validate(event) for event in events],
            waiting_count=waiting_count,
            blocked_count=blocked_count,
            running_sessions=0,
        )


# Deferred imports to keep the module order straightforward.
from acp_core.schemas import BoardColumnRead, EventRecord, ProjectSummary, TaskRead  # noqa: E402

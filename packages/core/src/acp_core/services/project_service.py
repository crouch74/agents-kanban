from __future__ import annotations

from sqlalchemy import select

from acp_core.constants import DEFAULT_BOARD_COLUMNS
from acp_core.logging import logger
from acp_core.models import AgentSession, Board, BoardColumn, Project, Repository, Task, WaitingQuestion, Worktree
from acp_core.schemas import (
    AgentSessionRead,
    BoardColumnRead,
    BoardView,
    ProjectCreate,
    ProjectOverview,
    ProjectSummary,
    RepositoryRead,
    TaskRead,
    WaitingQuestionRead,
    WorktreeRead,
)
from acp_core.services.base_service import ServiceContext, slugify


class ProjectService:
    """Project and board orchestration service.

    WHY:
        Keeps board topology and project reads/writes centralized so REST and
        MCP surfaces share identical workflow behavior and event emission.
    """
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_projects(self) -> list[Project]:
        """Purpose: list projects.

        Args:
            None.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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
        """Purpose: get project.

        Args:
            project_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        project = self.context.db.get(Project, project_id)
        if project is None:
            raise ValueError("Project not found")
        return project

    def create_project(self, payload: ProjectCreate) -> Project:
        """Purpose: create project.

        Args:
            payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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
        """Purpose: get board view.

        Args:
            project_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        project = self.get_project(project_id)
        if project.board is None:
            raise ValueError("Board not found")
        self._repair_board_columns(project.board)

        tasks_stmt = (
            select(Task)
            .where(Task.project_id == project_id, Task.workflow_state != "cancelled")
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
        """Purpose: get project overview.

        Args:
            project_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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



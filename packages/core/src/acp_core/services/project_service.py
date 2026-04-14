from __future__ import annotations

from sqlalchemy import select

from acp_core.constants import DEFAULT_BOARD_COLUMNS
from acp_core.logging import logger
from acp_core.models import Board, BoardColumn, Project, Task
from acp_core.schemas import BoardColumnRead, BoardView, ProjectCreate, ProjectOverview, ProjectSummary, TaskRead
from acp_core.services.base_service import ServiceContext, slugify


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

        logger.info("✅ project created", project_id=project.id, slug=project.slug)
        return project

    def get_board_view(self, project_id: str) -> BoardView:
        project = self.get_project(project_id)
        if project.board is None:
            raise ValueError("Board not found")

        tasks_stmt = select(Task).where(Task.project_id == project_id).order_by(Task.created_at.asc())
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
        return ProjectOverview(
            project=ProjectSummary.model_validate(project),
            board=board,
        )

    def archive_project(self, project_id: str) -> Project:
        project = self.get_project(project_id)
        if project.archived:
            return project

        project.archived = True
        self.context.record_event(
            entity_type="project",
            entity_id=project.id,
            event_type="project.archived",
            payload_json={"archived": True},
        )
        self.context.db.commit()
        self.context.db.refresh(project)
        logger.info("✅ project archived", project_id=project.id)
        return project

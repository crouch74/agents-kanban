from __future__ import annotations

from acp_core.db import SessionLocal
from acp_core.schemas import ProjectCreate
from acp_core.services.base_service import ServiceContext
from acp_core.services.project_service import ProjectService


def test_project_service_creates_project_with_default_board() -> None:
    db = SessionLocal()
    try:
        service = ProjectService(ServiceContext(db=db, actor_type="test", actor_name="pytest"))
        project = service.create_project(ProjectCreate(name="Unit Project", description="Unit test project"))

        overview = service.get_project_overview(project.id)
        assert overview.project.name == "Unit Project"
        assert [column.key for column in overview.board.columns] == [
            "backlog",
            "in_progress",
            "done",
        ]
    finally:
        db.close()

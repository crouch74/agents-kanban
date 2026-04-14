from __future__ import annotations

from acp_core.db import SessionLocal
from acp_core.schemas import ProjectCreate, TaskCommentCreate, TaskCreate, TaskPatch
from acp_core.services.base_service import ServiceContext
from acp_core.services.project_service import ProjectService
from acp_core.services.task_service import TaskService


def test_task_service_transition_and_comment_flow() -> None:
    db = SessionLocal()
    try:
        context = ServiceContext(db=db, actor_type="test", actor_name="pytest")
        project = ProjectService(context).create_project(ProjectCreate(name="Task Service"))
        task_service = TaskService(context)

        task = task_service.create_task(TaskCreate(project_id=project.id, title="Unit task"))
        assert task.workflow_state == "backlog"

        task = task_service.patch_task(task.id, TaskPatch(workflow_state="in_progress"))
        assert task.workflow_state == "in_progress"

        comment = task_service.add_comment(
            task.id,
            TaskCommentCreate(author_type="agent", author_name="codex", source="mcp", body="Work in progress"),
        )
        assert comment.author_name == "codex"

        detail = task_service.get_task_detail(task.id)
        assert len(detail.comments) == 1
        assert detail.comments[0].source == "mcp"
    finally:
        db.close()

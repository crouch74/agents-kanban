from __future__ import annotations

from sqlalchemy import select

from acp_core.constants import TASK_TRANSITIONS, WORKFLOW_BY_COLUMN_KEY
from acp_core.logging import logger
from acp_core.models import Board, BoardColumn, Task, TaskComment
from acp_core.schemas import TaskCommentCreate, TaskCommentRead, TaskCreate, TaskDetail, TaskPatch
from acp_core.services.base_service import ServiceContext


class TaskService:
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_tasks(self, *, project_id: str | None = None, status: str | None = None, q: str | None = None) -> list[Task]:
        stmt = select(Task).order_by(Task.updated_at.desc())
        if project_id is not None:
            stmt = stmt.where(Task.project_id == project_id)
        if status is not None:
            stmt = stmt.where(Task.workflow_state == status)
        if q is not None and q.strip():
            like = f"%{q.strip()}%"
            stmt = stmt.where((Task.title.ilike(like)) | (Task.description.ilike(like)))
        return list(self.context.db.scalars(stmt))

    def get_task(self, task_id: str) -> Task:
        task = self.context.db.get(Task, task_id)
        if task is None:
            raise ValueError("Task not found")
        return task

    def create_task(self, payload: TaskCreate) -> Task:
        board = self.context.db.scalar(select(Board).where(Board.project_id == payload.project_id))
        if board is None:
            raise ValueError("Project board not found")

        column = next((item for item in board.columns if item.key == payload.board_column_key), None)
        if column is None:
            raise ValueError("Board column not found")

        metadata = {
            "assignee": payload.assignee,
            "source": payload.source,
        }
        task = Task(
            project_id=payload.project_id,
            board_column_id=column.id,
            title=payload.title,
            description=payload.description,
            workflow_state=WORKFLOW_BY_COLUMN_KEY[column.key],
            priority=payload.priority,
            tags=payload.tags,
            metadata_json=metadata,
            blocked_reason=None,
            waiting_for_human=False,
            parent_task_id=None,
        )

        self.context.db.add(task)
        self.context.db.flush()
        self.context.record_event(
            entity_type="task",
            entity_id=task.id,
            event_type="task.created",
            payload_json={
                "title": task.title,
                "project_id": task.project_id,
                "task_id": task.id,
                "source": payload.source,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(task)
        logger.info("✅ task created", task_id=task.id, project_id=task.project_id)
        return task

    def patch_task(self, task_id: str, payload: TaskPatch) -> Task:
        task = self.get_task(task_id)
        provided = payload.model_fields_set
        next_workflow_state = task.workflow_state

        if "title" in provided and payload.title is not None:
            task.title = payload.title
        if "description" in provided:
            task.description = payload.description
        if "priority" in provided and payload.priority is not None:
            task.priority = payload.priority
        if "tags" in provided and payload.tags is not None:
            task.tags = payload.tags

        metadata = dict(task.metadata_json)
        if "assignee" in provided:
            metadata["assignee"] = payload.assignee
        task.metadata_json = metadata

        if "board_column_id" in provided and payload.board_column_id is not None:
            column = self.context.db.get(BoardColumn, payload.board_column_id)
            if column is None:
                raise ValueError("Board column not found")
            task.board_column_id = column.id
            next_workflow_state = WORKFLOW_BY_COLUMN_KEY.get(column.key, next_workflow_state)
        elif "workflow_state" in provided and payload.workflow_state is not None:
            allowed = TASK_TRANSITIONS.get(task.workflow_state, set())
            if payload.workflow_state not in allowed:
                raise ValueError(f"Invalid workflow transition from {task.workflow_state} to {payload.workflow_state}")
            next_workflow_state = payload.workflow_state
            column = self._column_for_workflow_state(task.project_id, next_workflow_state)
            if column is not None:
                task.board_column_id = column.id

        task.workflow_state = next_workflow_state

        self.context.record_event(
            entity_type="task",
            entity_id=task.id,
            event_type="task.updated",
            payload_json={
                "project_id": task.project_id,
                "task_id": task.id,
                "workflow_state": task.workflow_state,
                "assignee": metadata.get("assignee"),
            },
        )
        self.context.db.commit()
        self.context.db.refresh(task)
        logger.info("✅ task updated", task_id=task.id, workflow_state=task.workflow_state)
        return task

    def _column_for_workflow_state(self, project_id: str, workflow_state: str) -> BoardColumn | None:
        board = self.context.db.scalar(select(Board).where(Board.project_id == project_id))
        if board is None:
            return None
        return next((column for column in board.columns if WORKFLOW_BY_COLUMN_KEY.get(column.key) == workflow_state), None)

    def get_task_detail(self, task_id: str) -> TaskDetail:
        task = self.get_task(task_id)
        comments = list(
            self.context.db.scalars(
                select(TaskComment).where(TaskComment.task_id == task.id).order_by(TaskComment.created_at.asc())
            )
        )
        return TaskDetail(
            **task_to_read(task),
            comments=[comment_to_read(item) for item in comments],
        )

    def list_comments(self, task_id: str) -> list[TaskCommentRead]:
        self.get_task(task_id)
        comments = list(
            self.context.db.scalars(
                select(TaskComment).where(TaskComment.task_id == task_id).order_by(TaskComment.created_at.asc())
            )
        )
        return [comment_to_read(item) for item in comments]

    def add_comment(self, task_id: str, payload: TaskCommentCreate) -> TaskComment:
        task = self.get_task(task_id)
        metadata = dict(payload.metadata_json)
        if payload.source:
            metadata["source"] = payload.source
        comment = TaskComment(
            task_id=task.id,
            author_type=payload.author_type,
            author_name=payload.author_name,
            body=payload.body,
            metadata_json=metadata,
        )
        self.context.db.add(comment)
        self.context.db.flush()
        self.context.record_event(
            entity_type="task_comment",
            entity_id=comment.id,
            event_type="task.comment_added",
            payload_json={
                "project_id": task.project_id,
                "task_id": task.id,
                "author_name": comment.author_name,
                "source": payload.source,
            },
        )
        self.context.db.commit()
        self.context.db.refresh(comment)
        logger.info("✅ task comment added", task_id=task.id, comment_id=comment.id)
        return comment


def task_to_read(task: Task) -> dict[str, object]:
    metadata = task.metadata_json if isinstance(task.metadata_json, dict) else {}
    return {
        "id": task.id,
        "project_id": task.project_id,
        "board_column_id": task.board_column_id,
        "title": task.title,
        "description": task.description,
        "workflow_state": task.workflow_state,
        "priority": task.priority,
        "tags": task.tags,
        "assignee": metadata.get("assignee"),
        "source": metadata.get("source"),
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def comment_to_read(comment: TaskComment) -> TaskCommentRead:
    metadata = comment.metadata_json if isinstance(comment.metadata_json, dict) else {}
    return TaskCommentRead(
        id=comment.id,
        task_id=comment.task_id,
        author_type=comment.author_type,
        author_name=comment.author_name,
        source=(metadata.get("source") if isinstance(metadata.get("source"), str) else None),
        body=comment.body,
        metadata_json=metadata,
        created_at=comment.created_at,
    )

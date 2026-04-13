from __future__ import annotations

from sqlalchemy import func, select

from acp_core.constants import TASK_TRANSITIONS, WORKFLOW_BY_COLUMN_KEY
from acp_core.logging import logger
from acp_core.models import (
    Board,
    BoardColumn,
    Task,
    TaskArtifact,
    TaskCheck,
    TaskComment,
    TaskDependency,
)
from acp_core.schemas import (
    TaskArtifactCreate,
    TaskCheckCreate,
    TaskCommentCreate,
    TaskCreate,
    TaskDependencyCreate,
    TaskPatch,
)
from acp_core.services.task_read_service import TaskReadService
from acp_core.services.task_workflow_service import TaskWorkflowService


class TaskWriteService(TaskReadService, TaskWorkflowService):
    """Task mutations, evidence writes, and transition enforcement."""

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
        old_workflow_state = task.workflow_state
        next_workflow_state = task.workflow_state

        if "title" in provided and payload.title is not None:
            task.title = payload.title

        if "description" in provided:
            task.description = payload.description

        if "blocked_reason" in provided:
            task.blocked_reason = payload.blocked_reason

        if "waiting_for_human" in provided and payload.waiting_for_human is not None:
            task.waiting_for_human = payload.waiting_for_human

        if "board_column_id" in provided and payload.board_column_id is not None:
            column = self.context.db.get(BoardColumn, payload.board_column_id)
            if column is None:
                raise ValueError("Board column not found")
            task.board_column_id = column.id
            next_workflow_state = WORKFLOW_BY_COLUMN_KEY.get(column.key, next_workflow_state)
        elif "workflow_state" in provided and payload.workflow_state is not None:
            allowed = TASK_TRANSITIONS[task.workflow_state]
            if payload.workflow_state not in allowed:
                raise ValueError(
                    f"Invalid workflow transition from {task.workflow_state} to {payload.workflow_state}"
                )
            next_workflow_state = payload.workflow_state

        if task.workflow_state != "done" and next_workflow_state == "done":
            self._ensure_completion_evidence(task)

        task.workflow_state = next_workflow_state
        if "board_column_id" not in provided and next_workflow_state != "cancelled":
            column = self._column_for_workflow_state(task.project_id, next_workflow_state)
            if column is not None:
                task.board_column_id = column.id

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

        from acp_core.services.task_orchestration_service import TaskOrchestrationService

        if task.workflow_state == "ready" and old_workflow_state != "ready":
            self._auto_trigger_agent_session(task)
        else:
            TaskOrchestrationService(self.context).handle_task_updated(task.id)

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

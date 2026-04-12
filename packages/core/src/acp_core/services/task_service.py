from __future__ import annotations

from sqlalchemy import func, select

from acp_core.constants import TASK_TRANSITIONS, WORKFLOW_BY_COLUMN_KEY
from acp_core.logging import logger
from acp_core.models import Board, BoardColumn, Task, TaskArtifact, TaskCheck, TaskComment, TaskDependency, WaitingQuestion
from acp_core.schemas import (
    TaskArtifactCreate,
    TaskArtifactRead,
    TaskCheckCreate,
    TaskCheckRead,
    TaskCommentCreate,
    TaskCommentRead,
    TaskCompletionReadinessRead,
    TaskCreate,
    TaskDependencyCreate,
    TaskDependencyRead,
    TaskDetail,
    TaskPatch,
    TaskRead,
)
from acp_core.services.base_service import ServiceContext


class TaskService:
    """Task workflow service, including completion gates and evidence writes.

    WHY:
        Transition validation, done-readiness checks, and event emission happen
        here to prevent UI/API paths from bypassing canonical workflow policy.
    """
    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        """Purpose: list tasks.

        Args:
            project_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        stmt = select(Task).order_by(Task.created_at.desc())
        if project_id is not None:
            stmt = stmt.where(Task.project_id == project_id)
        return list(self.context.db.scalars(stmt))

    def get_task(self, task_id: str) -> Task:
        """Purpose: get task.

        Args:
            task_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
        task = self.context.db.get(Task, task_id)
        if task is None:
            raise ValueError("Task not found")
        return task

    def get_task_detail(self, task_id: str) -> TaskDetail:
        """Purpose: get task detail.

        Args:
            task_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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
        """Purpose: create task.

        Args:
            payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
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

    def _column_for_workflow_state(self, project_id: str, workflow_state: str) -> BoardColumn | None:
        board = self.context.db.scalar(select(Board).where(Board.project_id == project_id))
        if board is None:
            return None
        return next((column for column in board.columns if WORKFLOW_BY_COLUMN_KEY.get(column.key) == workflow_state), None)

    def get_completion_readiness(self, task_id: str) -> TaskCompletionReadinessRead:
        """Purpose: get completion readiness.

        Args:
            task_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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

    def _auto_trigger_agent_session(self, task: Task) -> None:
        """Auto-triggers an autonomous agent session if none is currently active."""
        # Check if there is already an active session for this task
        from acp_core.services.session_service import SessionService
        session_service = SessionService(self.context)
        sessions = session_service.list_sessions(task_id=task.id)
        
        has_active = False
        for s in sessions:
            if s.status in {"running", "waiting_human"}:
                # Double check with the runtime if it's actually alive
                try:
                    is_active = session_service.runtime.is_session_active(s.session_name)
                except Exception:
                    is_active = False
                
                if is_active:
                    has_active = True
                    break
        
        if not has_active:
            logger.info("🤖 agentic board: auto-triggering session", task_id=task.id)
            # Find a suitable worktree if one already exists
            worktree_id = None
            if task.worktrees:
                # Pick the most recent active worktree
                for wt in sorted(task.worktrees, key=lambda x: x.created_at, reverse=True):
                    if wt.status in {"active", "locked"}:
                        worktree_id = wt.id
                        break
            
            try:
                session_service._spawn_session_record(
                    task=task,
                    profile="executor",
                    worktree_id=worktree_id,
                )
            except Exception:
                import traceback
                logger.error("🤖 agentic board: failed to auto-trigger", task_id=task.id, exc=traceback.format_exc())

    def patch_task(self, task_id: str, payload: TaskPatch) -> Task:
        """Purpose: patch task.

        Args:
            task_id: Input parameter.; payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
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

        # Agentic Board: Auto-trigger session on Ready
        if task.workflow_state == "ready" and old_workflow_state != "ready":
             self._auto_trigger_agent_session(task)
             self.context.db.commit()

        logger.info("🗂️ task updated", task_id=task.id, workflow_state=task.workflow_state)
        return task

    def add_comment(self, task_id: str, payload: TaskCommentCreate) -> TaskComment:
        """Purpose: add comment.

        Args:
            task_id: Input parameter.; payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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
        """Purpose: add check.

        Args:
            task_id: Input parameter.; payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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
        """Purpose: add artifact.

        Args:
            task_id: Input parameter.; payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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
        """Purpose: add dependency.

        Args:
            task_id: Input parameter.; payload: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        WHY:
            Enforces canonical gating/event/reconciliation semantics in the service layer.
        """
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
        """Purpose: claim task.

        Args:
            task_id: Input parameter.; actor_name: Input parameter.; session_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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
        """Purpose: get dependencies.

        Args:
            task_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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
        """Purpose: next task.

        Args:
            project_id: Input parameter.

        Returns:
            Service result as declared by the function signature.

        Raises:
            ValueError: When validation or lookup constraints fail.
        """
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



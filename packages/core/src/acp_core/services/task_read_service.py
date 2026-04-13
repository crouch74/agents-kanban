from __future__ import annotations

from sqlalchemy import func, select

from acp_core.models import (
    Task,
    TaskArtifact,
    TaskCheck,
    TaskComment,
    TaskDependency,
    WaitingQuestion,
)
from acp_core.schemas import (
    TaskArtifactRead,
    TaskCheckRead,
    TaskCommentRead,
    TaskCompletionReadinessRead,
    TaskDependencyRead,
    TaskDetail,
    TaskRead,
    WaitingQuestionRead,
)


class TaskReadService:
    """Read-side task queries and readiness projections."""

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
                select(TaskDependency)
                .where(TaskDependency.task_id == task.id)
                .order_by(TaskDependency.created_at.asc())
            )
        )
        comments = list(
            self.context.db.scalars(
                select(TaskComment)
                .where(TaskComment.task_id == task.id)
                .order_by(TaskComment.created_at.asc())
            )
        )
        checks = list(
            self.context.db.scalars(
                select(TaskCheck)
                .where(TaskCheck.task_id == task.id)
                .order_by(TaskCheck.created_at.asc())
            )
        )
        artifacts = list(
            self.context.db.scalars(
                select(TaskArtifact)
                .where(TaskArtifact.task_id == task.id)
                .order_by(TaskArtifact.created_at.asc())
            )
        )
        waiting_questions = list(
            self.context.db.scalars(
                select(WaitingQuestion)
                .where(WaitingQuestion.task_id == task.id)
                .order_by(WaitingQuestion.created_at.desc())
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

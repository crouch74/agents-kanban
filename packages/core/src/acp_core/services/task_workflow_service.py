from __future__ import annotations
from sqlalchemy import select

from acp_core.constants import WORKFLOW_BY_COLUMN_KEY
from acp_core.models import Board, BoardColumn, Task


class TaskWorkflowService:
    """Workflow-only helpers shared by task write paths."""

    def _ensure_completion_evidence(self, task: Task) -> None:
        readiness = self.get_completion_readiness(task.id)
        if not readiness.can_mark_done:
            raise ValueError(
                "Task cannot move to done: " + ", ".join(readiness.missing_requirements)
            )

    def _column_for_workflow_state(
        self,
        project_id: str,
        workflow_state: str,
    ) -> BoardColumn | None:
        board = self.context.db.scalar(select(Board).where(Board.project_id == project_id))
        if board is None:
            return None
        return next(
            (
                column
                for column in board.columns
                if WORKFLOW_BY_COLUMN_KEY.get(column.key) == workflow_state
            ),
            None,
        )

    def _auto_trigger_agent_session(self, task: Task) -> None:
        from acp_core.services.task_orchestration_service import TaskOrchestrationService

        TaskOrchestrationService(self.context).handle_task_ready(task.id)

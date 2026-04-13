from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

from acp_core.constants import WORKFLOW_BY_COLUMN_KEY
from acp_core.logging import logger
from acp_core.models import AgentSession, Board, BoardColumn, Repository, Task, WaitingQuestion, Worktree
from acp_core.schemas import AgentSessionCreate, SessionLaunchInputCreate
from acp_core.services.base_service import ServiceContext

ACTIVE_SESSION_STATUSES = {"running", "waiting_human", "blocked"}
ORCHESTRATION_METADATA_KEY = "subtree_orchestration"


class TaskOrchestrationService:
    """Coordinates parent tasks that execute their immediate subtasks in sequence."""

    def __init__(self, context: ServiceContext) -> None:
        self.context = context

    def handle_task_ready(self, task_id: str) -> None:
        task = self.context.db.get(Task, task_id)
        if task is None:
            return

        if task.parent_task_id is not None:
            self._ensure_single_task_session(task)
            return

        subtasks = self._list_subtasks(task.id)
        if not subtasks:
            self._clear_orchestration(task)
            self._ensure_single_task_session(task)
            return

        state = self._build_state(task, subtasks)
        task.metadata_json = self._metadata_with_orchestration(task, state)
        self.context.record_event(
            entity_type="task",
            entity_id=task.id,
            event_type="task.subtree_orchestration_started",
            payload_json={"ordered_subtask_ids": state["ordered_subtask_ids"]},
        )
        self.context.db.commit()
        self.reconcile_parent(task.id)

    def handle_task_updated(self, task_id: str) -> None:
        task = self.context.db.get(Task, task_id)
        if task is None:
            return

        if task.parent_task_id is not None:
            self.reconcile_parent(task.parent_task_id)
            return

        if self._get_state(task) is not None:
            self.reconcile_parent(task.id)

    def handle_session_updated(self, session_id: str) -> None:
        session = self.context.db.get(AgentSession, session_id)
        if session is None:
            return

        task = self.context.db.get(Task, session.task_id)
        if task is None:
            return

        if task.parent_task_id is not None:
            self.reconcile_parent(task.parent_task_id)
            return

        if self._get_state(task) is not None:
            self.reconcile_parent(task.id)

    def reconcile_parent(self, parent_task_id: str) -> None:
        parent = self.context.db.get(Task, parent_task_id)
        if parent is None or parent.parent_task_id is not None:
            return

        subtasks = self._list_subtasks(parent.id)
        if not subtasks:
            return

        state = self._get_state(parent)
        if state is None:
            if parent.workflow_state != "ready":
                return
            state = self._build_state(parent, subtasks)

        state["ordered_subtask_ids"] = self._sync_ordered_subtask_ids(
            state.get("ordered_subtask_ids", []),
            subtasks,
        )

        if state.get("mode") == "paused" and not self._parent_has_pause_condition(parent, state):
            state["mode"] = "active"
            if parent.blocked_reason == state.get("last_block_reason"):
                parent.blocked_reason = None

        if state.get("phase") == "verification":
            self._reconcile_verification(parent, state)
            return

        self._reconcile_subtasks(parent, state)

    def _reconcile_subtasks(self, parent: Task, state: dict[str, Any]) -> None:
        for subtask_id in state["ordered_subtask_ids"]:
            subtask = self.context.db.get(Task, subtask_id)
            if subtask is None:
                continue

            if subtask.workflow_state == "done":
                if state.get("current_subtask_id") == subtask.id:
                    state["current_subtask_id"] = None
                    state["active_session_id"] = None
                    self.context.record_event(
                        entity_type="task",
                        entity_id=parent.id,
                        event_type="task.subtask_execution_completed",
                        payload_json={"subtask_id": subtask.id},
                    )
                continue

            if subtask.workflow_state == "cancelled":
                self._pause_parent(
                    parent,
                    state,
                    f"Subtree orchestration paused: subtask '{subtask.title}' was cancelled.",
                )
                return

            if self._task_is_waiting(subtask):
                self._pause_parent(
                    parent,
                    state,
                    f"Subtree orchestration paused: subtask '{subtask.title}' is waiting for input.",
                )
                return

            current_subtask_id = state.get("current_subtask_id")
            active_session_id = state.get("active_session_id")

            if current_subtask_id != subtask.id:
                state["current_subtask_id"] = subtask.id
                state["active_session_id"] = None
                active_session_id = None

            if active_session_id:
                active_session = self.context.db.get(AgentSession, active_session_id)
                if active_session is not None and active_session.status in ACTIVE_SESSION_STATUSES:
                    self._save_state(parent, state)
                    return
                if active_session is not None and active_session.status == "done":
                    self._pause_parent(
                        parent,
                        state,
                        (
                            f"Subtree orchestration paused: subtask '{subtask.title}' "
                            "finished its session without reaching done."
                        ),
                    )
                    return
                if active_session is not None and active_session.status in {"failed", "cancelled"}:
                    self._pause_parent(
                        parent,
                        state,
                        f"Subtree orchestration paused: subtask '{subtask.title}' session ended as {active_session.status}.",
                    )
                    return

            live_session = self._active_session_for_task(subtask.id)
            if live_session is not None:
                state["active_session_id"] = live_session.id
                self._save_state(parent, state)
                return

            self._ensure_task_in_ready_state(subtask)
            session = self._spawn_subtask_session(parent, subtask)
            if session is None:
                self._pause_parent(
                    parent,
                    state,
                    f"Subtree orchestration paused: failed to launch subtask '{subtask.title}'.",
                )
                return

            state["mode"] = "active"
            state["phase"] = "subtasks"
            state["active_session_id"] = session.id
            self.context.record_event(
                entity_type="task",
                entity_id=parent.id,
                event_type="task.subtask_execution_started",
                payload_json={"subtask_id": subtask.id, "session_id": session.id},
            )
            self._save_state(parent, state)
            return

        self._start_parent_verification(parent, state)

    def _reconcile_verification(self, parent: Task, state: dict[str, Any]) -> None:
        if self._task_is_waiting(parent):
            self._pause_parent(
                parent,
                state,
                "Subtree orchestration paused: parent task is waiting for input.",
            )
            return

        verification_session_id = state.get("verification_session_id")
        if verification_session_id:
            session = self.context.db.get(AgentSession, verification_session_id)
            if session is not None and session.status in ACTIVE_SESSION_STATUSES:
                self._save_state(parent, state)
                return
            if session is not None and session.status == "done":
                state["mode"] = "completed"
                state["phase"] = "finished"
                state["active_session_id"] = None
                if parent.blocked_reason == state.get("last_block_reason"):
                    parent.blocked_reason = None
                self.context.record_event(
                    entity_type="task",
                    entity_id=parent.id,
                    event_type="task.subtree_orchestration_completed",
                    payload_json={"verification_session_id": session.id},
                )
                self._save_state(parent, state)
                return
            if session is not None and session.status in {"failed", "cancelled"}:
                self._pause_parent(
                    parent,
                    state,
                    f"Subtree orchestration paused: parent verification ended as {session.status}.",
                )
                return

        live_session = self._active_session_for_task(parent.id, profile="verifier")
        if live_session is not None:
            state["verification_session_id"] = live_session.id
            state["active_session_id"] = live_session.id
            self._save_state(parent, state)
            return

        session = self._spawn_parent_verifier_session(parent, state["ordered_subtask_ids"])
        if session is None:
            self._pause_parent(
                parent,
                state,
                "Subtree orchestration paused: failed to launch parent verification.",
            )
            return

        state["mode"] = "active"
        state["phase"] = "verification"
        state["current_subtask_id"] = None
        state["active_session_id"] = session.id
        state["verification_session_id"] = session.id
        self.context.record_event(
            entity_type="task",
            entity_id=parent.id,
            event_type="task.verification_started",
            payload_json={"session_id": session.id},
        )
        self._save_state(parent, state)

    def _start_parent_verification(self, parent: Task, state: dict[str, Any]) -> None:
        state["phase"] = "verification"
        state["current_subtask_id"] = None
        state["active_session_id"] = None
        self._save_state(parent, state)
        self._reconcile_verification(parent, state)

    def _pause_parent(self, parent: Task, state: dict[str, Any], reason: str) -> None:
        state["mode"] = "paused"
        state["last_block_reason"] = reason
        state["active_session_id"] = None
        parent.blocked_reason = reason
        self.context.record_event(
            entity_type="task",
            entity_id=parent.id,
            event_type="task.subtree_orchestration_paused",
            payload_json={"reason": reason},
        )
        self._save_state(parent, state)

    def _ensure_single_task_session(self, task: Task) -> None:
        if self._active_session_for_task(task.id) is not None:
            return
        self._spawn_session(
            task=task,
            profile="executor",
            task_kind="execute",
            prompt=self._build_single_task_prompt(task),
            parent=None,
        )

    def _spawn_subtask_session(self, parent: Task, subtask: Task) -> AgentSession | None:
        return self._spawn_session(
            task=subtask,
            profile="executor",
            task_kind="execute",
            prompt=self._build_subtask_prompt(parent, subtask),
            parent=parent,
        )

    def _spawn_parent_verifier_session(
        self,
        parent: Task,
        ordered_subtask_ids: list[str],
    ) -> AgentSession | None:
        subtask_titles: list[str] = []
        for subtask_id in ordered_subtask_ids:
            subtask = self.context.db.get(Task, subtask_id)
            if subtask is not None:
                subtask_titles.append(subtask.title)
        return self._spawn_session(
            task=parent,
            profile="verifier",
            task_kind="verify",
            prompt=self._build_parent_verification_prompt(parent, subtask_titles),
            parent=parent,
        )

    def _spawn_session(
        self,
        *,
        task: Task,
        profile: str,
        task_kind: str,
        prompt: str,
        parent: Task | None,
    ) -> AgentSession | None:
        from acp_core.services.session_service import SessionService

        repository_id, worktree_id = self._resolve_launch_target(task, parent=parent)
        session_service = SessionService(self.context)
        try:
            return session_service.spawn_session(
                AgentSessionCreate(
                    task_id=task.id,
                    profile=profile,
                    repository_id=repository_id,
                    worktree_id=worktree_id,
                    launch_input=SessionLaunchInputCreate(
                        task_kind=task_kind,
                        prompt=prompt,
                        repository_id=repository_id,
                        worktree_id=worktree_id,
                    ),
                )
            )
        except Exception:
            logger.exception(
                "task orchestration session spawn failed",
                task_id=task.id,
                parent_task_id=parent.id if parent else None,
                profile=profile,
            )
            return None

    def _resolve_launch_target(
        self,
        task: Task,
        *,
        parent: Task | None,
    ) -> tuple[str | None, str | None]:
        preferred_worktree = self._latest_active_worktree(task)
        if preferred_worktree is None and parent is not None:
            preferred_worktree = self._latest_active_worktree(parent)
        if preferred_worktree is not None:
            return preferred_worktree.repository_id, preferred_worktree.id

        repository = self.context.db.scalar(
            select(Repository)
            .where(Repository.project_id == task.project_id)
            .order_by(Repository.created_at.asc())
            .limit(1)
        )
        if repository is not None:
            return repository.id, None
        return None, None

    @staticmethod
    def _latest_active_worktree(task: Task) -> Worktree | None:
        active_worktrees = [
            worktree
            for worktree in task.worktrees
            if worktree.status in {"active", "locked"}
        ]
        if not active_worktrees:
            return None
        return sorted(active_worktrees, key=lambda item: item.created_at, reverse=True)[0]

    def _ensure_task_in_ready_state(self, task: Task) -> None:
        if task.workflow_state != "backlog":
            return

        ready_column = self._column_for_workflow_state(task.project_id, "ready")
        task.workflow_state = "ready"
        if ready_column is not None:
            task.board_column_id = ready_column.id
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

    def _task_is_waiting(self, task: Task) -> bool:
        if task.waiting_for_human or bool(task.blocked_reason):
            return True
        open_question_count = self.context.db.scalar(
            select(func.count(WaitingQuestion.id)).where(
                WaitingQuestion.task_id == task.id,
                WaitingQuestion.status == "open",
            )
        ) or 0
        return open_question_count > 0

    def _parent_has_pause_condition(self, parent: Task, state: dict[str, Any]) -> bool:
        if parent.blocked_reason != state.get("last_block_reason"):
            return False
        current_subtask_id = state.get("current_subtask_id")
        if not current_subtask_id:
            return False
        subtask = self.context.db.get(Task, current_subtask_id)
        if subtask is None:
            return False
        return self._task_is_waiting(subtask) or subtask.workflow_state == "cancelled"

    def _active_session_for_task(
        self,
        task_id: str,
        *,
        profile: str | None = None,
    ) -> AgentSession | None:
        sessions = list(
            self.context.db.scalars(
                select(AgentSession)
                .where(AgentSession.task_id == task_id)
                .order_by(AgentSession.created_at.desc())
            )
        )
        for session in sessions:
            if profile is not None and session.profile != profile:
                continue
            if session.status in ACTIVE_SESSION_STATUSES:
                return session
        return None

    def _build_state(self, parent: Task, subtasks: list[Task]) -> dict[str, Any]:
        previous_state = self._get_state(parent) or {}
        return {
            "mode": "active",
            "phase": "subtasks",
            "ordered_subtask_ids": self._sync_ordered_subtask_ids(
                previous_state.get("ordered_subtask_ids", []),
                subtasks,
            ),
            "current_subtask_id": None,
            "active_session_id": None,
            "verification_session_id": None,
            "last_block_reason": None,
        }

    @staticmethod
    def _sync_ordered_subtask_ids(existing_ids: list[str], subtasks: list[Task]) -> list[str]:
        by_id = {task.id: task for task in subtasks}
        ordered_existing = [task_id for task_id in existing_ids if task_id in by_id]
        remaining_ids = [
            task.id
            for task in sorted(subtasks, key=lambda item: item.created_at)
            if task.id not in ordered_existing
        ]
        return ordered_existing + remaining_ids

    def _save_state(self, task: Task, state: dict[str, Any]) -> None:
        task.metadata_json = self._metadata_with_orchestration(task, state)
        self.context.db.commit()
        self.context.db.refresh(task)

    def _clear_orchestration(self, task: Task) -> None:
        metadata = dict(task.metadata_json)
        if ORCHESTRATION_METADATA_KEY not in metadata:
            return
        metadata.pop(ORCHESTRATION_METADATA_KEY, None)
        task.metadata_json = metadata
        self.context.db.commit()
        self.context.db.refresh(task)

    @staticmethod
    def _metadata_with_orchestration(task: Task, state: dict[str, Any]) -> dict[str, Any]:
        metadata = dict(task.metadata_json)
        metadata[ORCHESTRATION_METADATA_KEY] = state
        return metadata

    @staticmethod
    def _get_state(task: Task) -> dict[str, Any] | None:
        value = task.metadata_json.get(ORCHESTRATION_METADATA_KEY)
        if isinstance(value, dict):
            return dict(value)
        return None

    def _list_subtasks(self, parent_task_id: str) -> list[Task]:
        return list(
            self.context.db.scalars(
                select(Task)
                .where(Task.parent_task_id == parent_task_id)
                .order_by(Task.created_at.asc())
            )
        )

    @staticmethod
    def _build_single_task_prompt(task: Task) -> str:
        task_summary = task.description or task.title
        return (
            f"You are executing the ACP task '{task.title}'.\n\n"
            f"Task objective:\n{task_summary}\n\n"
            "Expected behavior:\n"
            "- Implement the requested change for this task.\n"
            "- Keep ACP comments, checks, and artifacts current with what you do.\n"
            "- If requirements are unclear or blocked, open a waiting question instead of guessing.\n"
            "- Only move the task to done when verification evidence has been attached."
        )

    @staticmethod
    def _build_subtask_prompt(parent: Task, subtask: Task) -> str:
        parent_summary = parent.description or parent.title
        subtask_summary = subtask.description or subtask.title
        return (
            f"You are executing the ACP subtask '{subtask.title}' for parent task '{parent.title}'.\n\n"
            f"Overall parent goal:\n{parent_summary}\n\n"
            f"Your subtask:\n{subtask_summary}\n\n"
            "Execution rules:\n"
            "- Focus on this subtask only.\n"
            "- Leave the parent-level integration and final verification to the parent verification phase.\n"
            "- Record comments, checks, and artifacts on the subtask as you work.\n"
            "- If you uncover missing requirements, open a waiting question rather than inventing scope.\n"
            "- Do not mark the parent task done."
        )

    @staticmethod
    def _build_parent_verification_prompt(
        parent: Task,
        subtask_titles: list[str],
    ) -> str:
        parent_summary = parent.description or parent.title
        subtask_list = "\n".join(f"- {title}" for title in subtask_titles) or "- No subtasks recorded"
        return (
            f"You are running the final parent verification phase for ACP task '{parent.title}'.\n\n"
            f"Overall goal:\n{parent_summary}\n\n"
            "Completed subtasks:\n"
            f"{subtask_list}\n\n"
            "Your responsibilities:\n"
            "- Verify the intended overall task has been implemented end-to-end.\n"
            "- Add any glue code or integration work still required between subtask outputs.\n"
            "- Run or record the verification evidence needed on the parent task.\n"
            "- Use ACP comments, checks, and artifacts to leave an operator-auditable verification trail.\n"
            "- Only move the parent task to done if the readiness gate is actually satisfied."
        )

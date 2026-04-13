from __future__ import annotations

from collections.abc import Mapping

from acp_core.enums import WorkflowState

DEFAULT_BOARD_COLUMNS: list[dict[str, object]] = [
    {
        "key": WorkflowState.BACKLOG.value,
        "name": "Backlog",
        "position": 0,
        "wip_limit": None,
        "entry_policy": "Capture work that is not yet ready to pull.",
        "exit_policy": "Move to Ready when scoped enough to start.",
        "done_policy": "Task has a title, owner context, and clear next step.",
    },
    {
        "key": WorkflowState.READY.value,
        "name": "Ready",
        "position": 1,
        "wip_limit": 8,
        "entry_policy": "Only pull items that can start without ambiguity.",
        "exit_policy": "Pull into In Progress when capacity exists.",
        "done_policy": "Task is unblocked and selected for active execution.",
    },
    {
        "key": WorkflowState.IN_PROGRESS.value,
        "name": "In Progress",
        "position": 2,
        "wip_limit": 5,
        "entry_policy": "Pull work only when active WIP has capacity.",
        "exit_policy": "Move to Review when execution is complete.",
        "done_policy": "Work has evidence, notes, and a clear review handoff.",
    },
    {
        "key": WorkflowState.REVIEW.value,
        "name": "Review",
        "position": 3,
        "wip_limit": 5,
        "entry_policy": "Review only work with checks or artifacts attached.",
        "exit_policy": "Move to Done once acceptance criteria are satisfied.",
        "done_policy": "Work has been verified or explicitly accepted.",
    },
    {
        "key": WorkflowState.DONE.value,
        "name": "Done",
        "position": 4,
        "wip_limit": None,
        "entry_policy": "Only completed and accepted work belongs here.",
        "exit_policy": "Return to Review only when reopened.",
        "done_policy": "Acceptance criteria and completion evidence are satisfied.",
    },
]

WORKFLOW_BY_COLUMN_KEY: Mapping[str, str] = {
    WorkflowState.BACKLOG.value: WorkflowState.BACKLOG.value,
    WorkflowState.READY.value: WorkflowState.READY.value,
    WorkflowState.IN_PROGRESS.value: WorkflowState.IN_PROGRESS.value,
    WorkflowState.REVIEW.value: WorkflowState.REVIEW.value,
    WorkflowState.DONE.value: WorkflowState.DONE.value,
}

TASK_TRANSITIONS: Mapping[str, set[str]] = {
    WorkflowState.BACKLOG.value: {WorkflowState.READY.value, WorkflowState.CANCELLED.value},
    WorkflowState.READY.value: {WorkflowState.BACKLOG.value, WorkflowState.IN_PROGRESS.value, WorkflowState.CANCELLED.value},
    WorkflowState.IN_PROGRESS.value: {WorkflowState.READY.value, WorkflowState.REVIEW.value, WorkflowState.CANCELLED.value},
    WorkflowState.REVIEW.value: {WorkflowState.IN_PROGRESS.value, WorkflowState.DONE.value, WorkflowState.CANCELLED.value},
    WorkflowState.DONE.value: {WorkflowState.REVIEW.value, WorkflowState.CANCELLED.value},
    WorkflowState.CANCELLED.value: {WorkflowState.BACKLOG.value},
}

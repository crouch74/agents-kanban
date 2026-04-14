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
        "exit_policy": "Move to In Progress when work starts.",
        "done_policy": "Task has a title, owner context, and clear next step.",
    },
    {
        "key": WorkflowState.IN_PROGRESS.value,
        "name": "In Progress",
        "position": 1,
        "wip_limit": 5,
        "entry_policy": "Pull work only when active WIP has capacity.",
        "exit_policy": "Move to Done when execution is complete.",
        "done_policy": "Work includes comments and handoff notes.",
    },
    {
        "key": WorkflowState.DONE.value,
        "name": "Done",
        "position": 2,
        "wip_limit": None,
        "entry_policy": "Only completed and accepted work belongs here.",
        "exit_policy": "Return to In Progress when reopened.",
        "done_policy": "Acceptance criteria and completion evidence are satisfied.",
    },
]

WORKFLOW_BY_COLUMN_KEY: Mapping[str, str] = {
    WorkflowState.BACKLOG.value: WorkflowState.BACKLOG.value,
    WorkflowState.IN_PROGRESS.value: WorkflowState.IN_PROGRESS.value,
    WorkflowState.DONE.value: WorkflowState.DONE.value,
}

TASK_TRANSITIONS: Mapping[str, set[str]] = {
    WorkflowState.BACKLOG.value: {WorkflowState.IN_PROGRESS.value},
    WorkflowState.IN_PROGRESS.value: {WorkflowState.BACKLOG.value, WorkflowState.DONE.value},
    WorkflowState.DONE.value: {WorkflowState.IN_PROGRESS.value},
}

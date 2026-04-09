from __future__ import annotations

from collections.abc import Mapping

DEFAULT_BOARD_COLUMNS: list[dict[str, object]] = [
    {
        "key": "backlog",
        "name": "Backlog",
        "position": 0,
        "wip_limit": None,
        "entry_policy": "Capture work that is not yet ready to pull.",
        "exit_policy": "Move to Ready when scoped enough to start.",
        "done_policy": "Task has a title, owner context, and clear next step.",
    },
    {
        "key": "ready",
        "name": "Ready",
        "position": 1,
        "wip_limit": 8,
        "entry_policy": "Only pull items that can start without ambiguity.",
        "exit_policy": "Pull into In Progress when capacity exists.",
        "done_policy": "Task is unblocked and selected for active execution.",
    },
    {
        "key": "in_progress",
        "name": "In Progress",
        "position": 2,
        "wip_limit": 5,
        "entry_policy": "Pull work only when active WIP has capacity.",
        "exit_policy": "Move to Review when execution is complete.",
        "done_policy": "Work has evidence, notes, and a clear review handoff.",
    },
    {
        "key": "review",
        "name": "Review",
        "position": 3,
        "wip_limit": 5,
        "entry_policy": "Review only work with checks or artifacts attached.",
        "exit_policy": "Move to Done once acceptance criteria are satisfied.",
        "done_policy": "Work has been verified or explicitly accepted.",
    },
    {
        "key": "done",
        "name": "Done",
        "position": 4,
        "wip_limit": None,
        "entry_policy": "Only completed and accepted work belongs here.",
        "exit_policy": "Return to Review only when reopened.",
        "done_policy": "Acceptance criteria and completion evidence are satisfied.",
    },
]

WORKFLOW_BY_COLUMN_KEY: Mapping[str, str] = {
    "backlog": "backlog",
    "ready": "ready",
    "in_progress": "in_progress",
    "review": "review",
    "done": "done",
}

TASK_TRANSITIONS: Mapping[str, set[str]] = {
    "backlog": {"ready", "cancelled"},
    "ready": {"backlog", "in_progress", "cancelled"},
    "in_progress": {"ready", "review", "cancelled"},
    "review": {"in_progress", "done", "cancelled"},
    "done": {"review", "cancelled"},
    "cancelled": set(),
}


from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str


TOOLS: list[ToolSpec] = [
    ToolSpec("project_list", "List projects visible to the current agent."),
    ToolSpec("project_get", "Fetch a project and high-level context."),
    ToolSpec("board_get", "Read structured board state for a project."),
    ToolSpec("task_get", "Fetch one task with structured fields."),
    ToolSpec("task_create", "Create a new task."),
    ToolSpec("subtask_create", "Create a subtask under a task."),
    ToolSpec("task_update", "Patch task state or metadata."),
    ToolSpec("task_claim", "Claim a task for an agent session."),
    ToolSpec("task_comment_add", "Attach a comment to a task."),
    ToolSpec("task_check_add", "Attach a structured check to a task."),
    ToolSpec("task_next", "Find the next suitable task."),
    ToolSpec("task_dependencies_get", "List dependency edges for a task."),
    ToolSpec("session_spawn", "Start an agent session for a task."),
    ToolSpec("session_status", "Read session runtime status."),
    ToolSpec("session_tail", "Read recent session output."),
    ToolSpec("session_list", "List sessions relevant to an agent."),
    ToolSpec("question_open", "Open a waiting question for human input."),
    ToolSpec("question_answer_get", "Read a human reply."),
    ToolSpec("worktree_create", "Allocate a worktree for a task."),
    ToolSpec("worktree_list", "List worktrees."),
    ToolSpec("worktree_get", "Fetch one worktree."),
    ToolSpec("context_search", "Search tasks, events, questions, and comments."),
]


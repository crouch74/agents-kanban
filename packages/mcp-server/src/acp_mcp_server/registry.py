from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

from acp_mcp_server import handlers


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., Any]


@dataclass(frozen=True)
class ResourceSpec:
    uri: str
    name: str
    description: str
    handler: Callable[..., Any]


TOOL_HANDLERS: dict[str, ToolSpec] = {
    "project_list": ToolSpec(
        "project_list",
        "List projects visible to the current agent.",
        handlers.project_list,
    ),
    "project_get": ToolSpec(
        "project_get", "Fetch a project and high-level context.", handlers.project_get
    ),
    "board_get": ToolSpec(
        "board_get", "Read structured board state for a project.", handlers.board_get
    ),
    "task_get": ToolSpec(
        "task_get",
        "Fetch one task with structured fields and evidence.",
        handlers.task_get,
    ),
    "project_create": ToolSpec(
        "project_create", "Create a project and default board.", handlers.project_create
    ),
    "project_bootstrap": ToolSpec(
        "project_bootstrap",
        "Create a project, prepare the repository, and launch the kickoff session.",
        handlers.project_bootstrap,
    ),
    "task_create": ToolSpec("task_create", "Create a new task.", handlers.task_create),
    "subtask_create": ToolSpec(
        "subtask_create", "Create a subtask under a task.", handlers.subtask_create
    ),
    "task_update": ToolSpec(
        "task_update", "Patch task state or metadata.", handlers.task_update
    ),
    "task_claim": ToolSpec(
        "task_claim", "Claim a task for an agent session.", handlers.task_claim
    ),
    "task_comment_add": ToolSpec(
        "task_comment_add", "Attach a comment to a task.", handlers.task_comment_add
    ),
    "task_check_add": ToolSpec(
        "task_check_add",
        "Attach a structured check to a task.",
        handlers.task_check_add,
    ),
    "task_artifact_add": ToolSpec(
        "task_artifact_add", "Attach an artifact to a task.", handlers.task_artifact_add
    ),
    "task_next": ToolSpec(
        "task_next", "Find the next suitable task.", handlers.task_next
    ),
    "task_dependencies_get": ToolSpec(
        "task_dependencies_get",
        "List dependency edges for a task.",
        handlers.task_dependencies_get,
    ),
    "task_dependency_add": ToolSpec(
        "task_dependency_add",
        "Attach a dependency edge to a task.",
        handlers.task_dependency_add,
    ),
    "task_completion_readiness": ToolSpec(
        "task_completion_readiness",
        "Check whether a task is ready to move to done.",
        handlers.task_completion_readiness,
    ),
    "session_spawn": ToolSpec(
        "session_spawn", "Start an agent session for a task.", handlers.session_spawn
    ),
    "session_status": ToolSpec(
        "session_status", "Read session runtime status.", handlers.session_status
    ),
    "session_follow_up": ToolSpec(
        "session_follow_up",
        "Start a retry, reviewer, or verifier session linked to an existing session chain.",
        handlers.session_follow_up,
    ),
    "session_tail": ToolSpec(
        "session_tail", "Read recent session output.", handlers.session_tail
    ),
    "session_list": ToolSpec(
        "session_list", "List sessions relevant to an agent.", handlers.session_list
    ),
    "question_open": ToolSpec(
        "question_open",
        "Open a waiting question for human input.",
        handlers.question_open,
    ),
    "question_answer_get": ToolSpec(
        "question_answer_get", "Read a human reply.", handlers.question_answer_get
    ),
    "worktree_create": ToolSpec(
        "worktree_create", "Allocate a worktree for a task.", handlers.worktree_create
    ),
    "worktree_list": ToolSpec(
        "worktree_list", "List worktrees.", handlers.worktree_list
    ),
    "worktree_get": ToolSpec(
        "worktree_get", "Fetch one worktree.", handlers.worktree_get
    ),
    "context_search": ToolSpec(
        "context_search",
        "Search tasks, events, questions, and comments.",
        handlers.context_search,
    ),
    "diagnostics_get": ToolSpec(
        "diagnostics_get",
        "Read local diagnostics and recovery state.",
        handlers.diagnostics_get,
    ),
    "worktree_hygiene_list": ToolSpec(
        "worktree_hygiene_list",
        "List stale or recommended worktree cleanup items.",
        handlers.worktree_hygiene_list,
    ),
}

RESOURCE_HANDLERS: dict[str, ResourceSpec] = {
    "project_board_state": ResourceSpec(
        "control-plane://projects/{project_id}/board",
        "project_board_state",
        "Project board state.",
        handlers.project_board_resource,
    ),
    "task_detail_state": ResourceSpec(
        "control-plane://tasks/{task_id}",
        "task_detail_state",
        "Task detail state.",
        handlers.task_detail_resource,
    ),
    "task_completion_state": ResourceSpec(
        "control-plane://tasks/{task_id}/completion",
        "task_completion_state",
        "Task completion readiness state.",
        handlers.task_completion_resource,
    ),
    "session_timeline_state": ResourceSpec(
        "control-plane://sessions/{session_id}/timeline",
        "session_timeline_state",
        "Session timeline state.",
        handlers.session_timeline_resource,
    ),
    "waiting_question_state": ResourceSpec(
        "control-plane://questions/{question_id}",
        "waiting_question_state",
        "Waiting question state.",
        handlers.question_resource,
    ),
    "repo_inventory_state": ResourceSpec(
        "control-plane://projects/{project_id}/repos",
        "repo_inventory_state",
        "Repo and worktree inventory.",
        handlers.repo_inventory_resource,
    ),
    "local_diagnostics_state": ResourceSpec(
        "control-plane://diagnostics/local",
        "local_diagnostics_state",
        "Local diagnostics and runtime hygiene state.",
        handlers.diagnostics_resource,
    ),
    "recent_project_events": ResourceSpec(
        "control-plane://events/project/{project_id}",
        "recent_project_events",
        "Recent project events.",
        lambda project_id: handlers.recent_events_resource(project_id=project_id),
    ),
    "recent_task_events": ResourceSpec(
        "control-plane://events/task/{task_id}",
        "recent_task_events",
        "Recent task events.",
        lambda task_id: handlers.recent_events_resource(task_id=task_id),
    ),
}


def register_mcp_handlers(mcp: FastMCP) -> None:
    for spec in TOOL_HANDLERS.values():
        mcp.tool(name=spec.name, description=spec.description)(spec.handler)

    for spec in RESOURCE_HANDLERS.values():
        mcp.resource(spec.uri, name=spec.name, description=spec.description)(
            spec.handler
        )

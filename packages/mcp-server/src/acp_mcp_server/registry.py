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
        "List projects visible to the current actor.",
        handlers.project_list,
    ),
    "project_get": ToolSpec(
        "project_get", "Fetch a project with board snapshot.", handlers.project_get
    ),
    "board_get": ToolSpec(
        "board_get", "Read board state for a project.", handlers.board_get
    ),
    "project_create": ToolSpec(
        "project_create", "Create a project and default board.", handlers.project_create
    ),
    "task_list": ToolSpec(
        "task_list", "List tasks with optional filters.", handlers.task_list
    ),
    "task_get": ToolSpec(
        "task_get",
        "Fetch one task with comments.",
        handlers.task_get,
    ),
    "task_create": ToolSpec("task_create", "Create a new task.", handlers.task_create),
    "task_update": ToolSpec(
        "task_update", "Patch task state or metadata.", handlers.task_update
    ),
    "task_comment_add": ToolSpec(
        "task_comment_add", "Attach a comment to a task.", handlers.task_comment_add
    ),
    "context_search": ToolSpec(
        "context_search",
        "Search tasks and events.",
        handlers.context_search,
    ),
    "dashboard_get": ToolSpec(
        "dashboard_get",
        "Read project and task count summary.",
        handlers.dashboard_get,
    ),
}

RESOURCE_HANDLERS: dict[str, ResourceSpec] = {
    "project_board_state": ResourceSpec(
        "taskboard://projects/{project_id}/board",
        "project_board_state",
        "Project board state.",
        handlers.project_board_resource,
    ),
    "task_detail_state": ResourceSpec(
        "taskboard://tasks/{task_id}",
        "task_detail_state",
        "Task detail state.",
        handlers.task_detail_resource,
    ),
    "recent_project_events": ResourceSpec(
        "taskboard://events/project/{project_id}",
        "recent_project_events",
        "Recent project events.",
        lambda project_id: handlers.recent_events_resource(project_id=project_id),
    ),
    "recent_task_events": ResourceSpec(
        "taskboard://events/task/{task_id}",
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

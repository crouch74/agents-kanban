from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from acp_mcp_server import handlers

mcp = FastMCP("Agent Control Plane", json_response=True)


@mcp.tool()
def project_list() -> list[dict]:
    """List projects visible to the current agent."""
    return [item.model_dump() for item in handlers.project_list()]


@mcp.tool()
def project_get(project_id: str) -> dict:
    """Fetch a project and high-level context."""
    return handlers.project_get(project_id)


@mcp.tool()
def board_get(project_id: str) -> dict:
    """Read structured board state for a project."""
    return handlers.board_get(project_id)


@mcp.tool()
def task_get(task_id: str) -> dict:
    """Fetch one task with structured fields and evidence."""
    return handlers.task_get(task_id)


@mcp.tool()
def task_create(project_id: str, title: str, description: str | None = None, priority: str = "medium") -> dict:
    """Create a new task."""
    return handlers.task_create(project_id, title, description, priority)


@mcp.tool()
def subtask_create(parent_task_id: str, title: str, description: str | None = None, priority: str = "medium") -> dict:
    """Create a subtask under a task."""
    return handlers.subtask_create(parent_task_id, title, description, priority)


@mcp.tool()
def task_update(
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    workflow_state: str | None = None,
    blocked_reason: str | None = None,
    waiting_for_human: bool | None = None,
) -> dict:
    """Patch task state or metadata."""
    return handlers.task_update(task_id, title, description, workflow_state, blocked_reason, waiting_for_human)


@mcp.tool()
def task_claim(task_id: str, actor_name: str, session_id: str | None = None) -> dict:
    """Claim a task for an agent session."""
    return handlers.task_claim(task_id, actor_name, session_id)


@mcp.tool()
def task_comment_add(task_id: str, author_name: str, body: str, author_type: str = "agent") -> dict:
    """Attach a comment to a task."""
    return handlers.task_comment_add(task_id, author_name, body, author_type)


@mcp.tool()
def task_check_add(task_id: str, check_type: str, status: str, summary: str) -> dict:
    """Attach a structured check to a task."""
    return handlers.task_check_add(task_id, check_type, status, summary)


@mcp.tool()
def task_next(project_id: str | None = None) -> dict | None:
    """Find the next suitable task."""
    return handlers.task_next(project_id)


@mcp.tool()
def task_dependencies_get(task_id: str) -> list[dict]:
    """List dependency edges for a task."""
    return handlers.task_dependencies_get(task_id)


@mcp.tool()
def session_spawn(
    task_id: str,
    profile: str = "executor",
    repository_id: str | None = None,
    worktree_id: str | None = None,
    command: str | None = None,
) -> dict:
    """Start an agent session for a task."""
    return handlers.session_spawn(task_id, profile, repository_id, worktree_id, command)


@mcp.tool()
def session_status(session_id: str) -> dict:
    """Read session runtime status."""
    return handlers.session_status(session_id)


@mcp.tool()
def session_tail(session_id: str, lines: int = 80) -> dict:
    """Read recent session output."""
    return handlers.session_tail(session_id, lines)


@mcp.tool()
def session_list(project_id: str | None = None, task_id: str | None = None) -> list[dict]:
    """List sessions relevant to an agent."""
    return handlers.session_list(project_id, task_id)


@mcp.tool()
def question_open(
    task_id: str,
    prompt: str,
    session_id: str | None = None,
    blocked_reason: str | None = None,
    urgency: str | None = None,
    options_json: list[dict] | None = None,
) -> dict:
    """Open a waiting question for human input."""
    return handlers.question_open(task_id, prompt, session_id, blocked_reason, urgency, options_json)


@mcp.tool()
def question_answer_get(question_id: str) -> dict:
    """Read a human reply."""
    return handlers.question_answer_get(question_id)


@mcp.tool()
def worktree_create(repository_id: str, task_id: str | None = None, label: str | None = None) -> dict:
    """Allocate a worktree for a task."""
    return handlers.worktree_create(repository_id, task_id, label)


@mcp.tool()
def worktree_list(project_id: str | None = None) -> list[dict]:
    """List worktrees."""
    return handlers.worktree_list(project_id)


@mcp.tool()
def worktree_get(worktree_id: str) -> dict:
    """Fetch one worktree."""
    return handlers.worktree_get(worktree_id)


@mcp.tool()
def context_search(query: str, project_id: str | None = None, limit: int = 20) -> dict:
    """Search tasks, events, questions, and comments."""
    return handlers.context_search(query, project_id, limit)


@mcp.resource("control-plane://projects/{project_id}/board")
def project_board_state(project_id: str) -> dict:
    """Project board state."""
    return handlers.project_board_resource(project_id)


@mcp.resource("control-plane://tasks/{task_id}")
def task_detail_state(task_id: str) -> dict:
    """Task detail state."""
    return handlers.task_detail_resource(task_id)


@mcp.resource("control-plane://sessions/{session_id}/timeline")
def session_timeline_state(session_id: str) -> dict:
    """Session timeline state."""
    return handlers.session_timeline_resource(session_id)


@mcp.resource("control-plane://questions/{question_id}")
def waiting_question_state(question_id: str) -> dict:
    """Waiting question state."""
    return handlers.question_resource(question_id)


@mcp.resource("control-plane://projects/{project_id}/repos")
def repo_inventory_state(project_id: str) -> dict:
    """Repo and worktree inventory."""
    return handlers.repo_inventory_resource(project_id)


@mcp.resource("control-plane://events/project/{project_id}")
def recent_project_events(project_id: str) -> list[dict]:
    """Recent project events."""
    return handlers.recent_events_resource(project_id=project_id)


@mcp.resource("control-plane://events/task/{task_id}")
def recent_task_events(task_id: str) -> list[dict]:
    """Recent task events."""
    return handlers.recent_events_resource(task_id=task_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

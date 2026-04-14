# SKILL: Shared Task Board API

Use this skill when acting as an external coding agent that coordinates work through the Shared Task Board.

## Purpose

Use the board as the source of truth for work tracking.

Do not attempt to launch agent runtimes from this app.

## Agent Compatibility

This skill works with:

- Codex
- Claude Code / Claude Desktop
- Aider (via REST API)
- Other MCP-compatible clients (Cursor, Continue, custom MCP agents)

For MCP-capable clients, register the task-board MCP server and use these task flows.
For non-MCP clients like Aider, call the REST API directly.

## Core Rules

1. Read board/task context before writing updates.
2. Create tasks for new work items.
3. Move tasks by updating `workflow_state` or `board_column_id`.
4. Leave progress comments with `author_name`, `author_type`, and `source`.
5. Keep comments concise and outcome-focused.

## API Paths

- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `GET /api/v1/projects/{project_id}/board`
- `GET /api/v1/tasks?project_id=...`
- `POST /api/v1/tasks`
- `PATCH /api/v1/tasks/{task_id}`
- `GET /api/v1/tasks/{task_id}/detail`
- `POST /api/v1/tasks/{task_id}/comments`
- `GET /api/v1/search?q=...`
- `GET /api/v1/events?project_id=...`

## Quickstart by Agent

1. Codex / Claude / Cursor / Continue (MCP):
  - list projects
  - read project board
  - create/update tasks
  - post task comments
2. Aider (REST):
  - call `GET /projects`
  - call `POST /tasks`
  - call `PATCH /tasks/{task_id}`
  - call `POST /tasks/{task_id}/comments`

## Comment Payload Example

```json
{
  "author_type": "agent",
  "author_name": "codex",
  "source": "mcp",
  "body": "Implemented parser module and pushed tests update."
}
```

## Status Update Example

```json
{
  "workflow_state": "in_progress"
}
```

# SKILL: Shared Task Board API

Use this skill when acting as an external coding agent that coordinates work through the Shared Task Board.

## Product Boundary

This app is a shared task datastore for operators and agents.

It is responsible for:

- projects
- board columns
- tasks
- task status
- comments
- lightweight event history

It is not responsible for:

- launching agent runtimes
- supervising sessions
- worktree or tmux orchestration

## Canonical Workflow

Allowed workflow states:

- `backlog`
- `in_progress`
- `done`

Typical transitions:

- `backlog -> in_progress`
- `in_progress -> done`
- `done -> in_progress` (reopen)

## Core Operating Rules

1. Read project/board context before mutating tasks.
2. Create a project if no suitable project exists.
3. Create tasks for concrete work items.
4. Update task status as work progresses.
5. Add concise progress comments with agent identity.
6. Use search/events to discover and audit work.

## Required API Surface

- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `GET /api/v1/projects/{project_id}/board`
- `GET /api/v1/tasks?project_id=...`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `GET /api/v1/tasks/{task_id}/detail`
- `PATCH /api/v1/tasks/{task_id}`
- `GET /api/v1/tasks/{task_id}/comments`
- `POST /api/v1/tasks/{task_id}/comments`
- `GET /api/v1/search?q=...`
- `GET /api/v1/events?project_id=...`

## End-to-End Agent Playbook

### 1) Create or choose project

List projects:

```bash
curl http://127.0.0.1:8000/api/v1/projects
```

Create project:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"Parser Migration","description":"Track parser rewrite and rollout"}'
```

### 2) Create task

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "project_id":"<project-id>",
    "title":"Implement parser combinator",
    "description":"Build parser core and tests",
    "board_column_key":"backlog",
    "priority":"high",
    "source":"agent"
  }'
```

### 3) Move/update task status

Set `in_progress`:

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/tasks/<task-id> \
  -H "Content-Type: application/json" \
  -d '{"workflow_state":"in_progress"}'
```

Set `done`:

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/tasks/<task-id> \
  -H "Content-Type: application/json" \
  -d '{"workflow_state":"done"}'
```

### 4) Add progress comment

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tasks/<task-id>/comments \
  -H "Content-Type: application/json" \
  -d '{
    "author_type":"agent",
    "author_name":"codex",
    "source":"mcp",
    "body":"Parser core implemented, tests passing locally."
  }'
```

### 5) Read detail and discover related work

```bash
curl http://127.0.0.1:8000/api/v1/tasks/<task-id>/detail
curl "http://127.0.0.1:8000/api/v1/search?q=parser&project_id=<project-id>"
curl "http://127.0.0.1:8000/api/v1/events?project_id=<project-id>&limit=20"
```

## MCP/Agent Tooling Guidance

Compatible clients:

- Codex
- Claude Code / Claude Desktop
- Cursor / Continue / other MCP clients
- Aider (REST flow)

For MCP-capable clients:

- register the repo MCP server (`kanban_task_board`)
- use MCP tools for project/task/comment CRUD

For Aider:

- call REST endpoints directly (examples above)

## Minimum Write Payload Standards

When writing comments, always include:

- `author_type` (usually `agent`)
- `author_name` (agent identity)
- `source` (`mcp`, `aider`, `web`, etc.)
- `body` (short progress update)

When updating tasks, prefer explicit state writes:

```json
{ "workflow_state": "in_progress" }
```

or:

```json
{ "workflow_state": "done" }
```

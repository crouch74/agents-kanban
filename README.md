# Shared Task Board

Shared Task Board is a local-first coordination system for operators and external coding agents.

The product boundary is intentionally narrow:

- source of truth for `projects`, `board columns`, `tasks`, `status`, `comments`, and lightweight `events`
- humans use the web app to create, prioritize, and move work
- agents use API/MCP to create tasks, update status, and post progress comments
- this application does **not** launch, host, supervise, or reconcile agent runtimes

## Stack

- Backend: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2
- Frontend: React 19, TypeScript, Vite, TanStack Query
- Transport: REST + WebSocket mutation invalidation
- Store: SQLite (local, durable)
- Agent interface: MCP tools/resources mapped to task-board operations

## Core Workflows

1. Create a project.
2. Add tasks into board columns.
3. Drag tasks across columns (`backlog`, `ready`, `in_progress`, `review`, `done`, `cancelled`).
3. Drag tasks across columns (`backlog`, `in_progress`, `done`).
4. Open task detail and add comments with actor/source metadata.
5. Use search/events to monitor progress.

## API Surface (Current)

- `GET /api/v1/health`
- `GET /api/v1/dashboard`
- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/archive`
- `GET /api/v1/projects/{project_id}/board`
- `GET /api/v1/tasks`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `GET /api/v1/tasks/{task_id}/detail`
- `PATCH /api/v1/tasks/{task_id}`
- `GET /api/v1/tasks/{task_id}/comments`
- `POST /api/v1/tasks/{task_id}/comments`
- `GET /api/v1/events`
- `GET /api/v1/search`
- `GET /api/v1/settings/diagnostics`
- `POST /api/v1/settings/purge-db`

Removed control-plane surfaces include sessions, worktrees, repositories, waiting-question inbox, bootstrap execution, and runtime diagnostics.

## How-To: connect major coding agents

### 1. Codex

```toml
[mcp_servers.kanban_task_board]
command = "bash"
args = ["-lc", "cd /Users/aeid/git_tree/kanban && export PYTHONPATH=/Users/aeid/git_tree/kanban/packages/core/src:/Users/aeid/git_tree/kanban/packages/mcp-server/src:${PYTHONPATH:-} && /Users/aeid/git_tree/kanban/.venv/bin/python -c 'from acp_mcp_server.server import mcp; mcp.run()'"]
```

Enable the repository skill:

```toml
[[skills.config]]
path = "/Users/aeid/git_tree/kanban/skills/agent-control-plane-api/SKILL.md"
enabled = true
```

### 2. Claude Code / Claude Desktop

Add the same MCP server command in your Claude MCP config:

```json
{
  "mcpServers": {
    "kanban_task_board": {
      "command": "bash",
      "args": [
        "-lc",
        "cd /Users/aeid/git_tree/kanban && export PYTHONPATH=/Users/aeid/git_tree/kanban/packages/core/src:/Users/aeid/git_tree/kanban/packages/mcp-server/src:${PYTHONPATH:-} && /Users/aeid/git_tree/kanban/.venv/bin/python -c 'from acp_mcp_server.server import mcp; mcp.run()'"
      ]
    }
  }
}
```

### 3. Aider

Aider can use the REST API directly:

```bash
curl http://127.0.0.1:8000/api/v1/projects

curl -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<project-id>","title":"Implement parser","board_column_key":"backlog","source":"aider"}'

curl -X POST http://127.0.0.1:8000/api/v1/tasks/<task-id>/comments \
  -H "Content-Type: application/json" \
  -d '{"author_type":"agent","author_name":"aider","source":"aider","body":"Work in progress"}'
```

### 4. Other MCP-compatible agents (Cursor, Continue, etc.)

Register the same stdio MCP command under a server name such as `kanban_task_board`.

Restart the agent tool after config changes.

## Agent Integration

- MCP server exposes task-board-only tools/resources.
- Skill guide for agent API usage: [skills/agent-control-plane-api/SKILL.md](skills/agent-control-plane-api/SKILL.md)

## Verification

```bash
bash scripts/bootstrap.sh
bash scripts/verify.sh --skip-bootstrap
```

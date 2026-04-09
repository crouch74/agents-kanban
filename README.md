# Agent Control Plane

Agent Control Plane is a local-first control plane for a single technical
operator managing multiple AI agents across multiple repositories and projects.
It combines structured kanban workflow, tmux-backed runtime visibility, git
worktree isolation, and an MCP-native agent interface.

## Current Status

This repository currently contains:

- product and architecture documents
- monorepo scaffolding for the API, web app, shared core, MCP server, and SDK
- a runnable FastAPI shell with diagnostics and placeholder views
- a Vite/React workspace shell wired to the API contract

## Stack

- Backend: Python, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, structlog
- Frontend: React, TypeScript, Vite, TanStack Query, Zustand, Tailwind CSS
- Runtime: SQLite (WAL), tmux, git worktrees
- Agent interface: MCP

## Repo Layout

- `apps/api`: FastAPI application
- `apps/web`: React + Vite operator UI
- `packages/core`: shared domain models, services, repositories, adapters
- `packages/mcp-server`: MCP server shell
- `packages/sdk`: generated and hand-authored TypeScript SDK helpers
- `docs/prd`: product and architecture documents
- `docs/adr`: architecture decisions
- `scripts`: local development helpers
- `tests`: integration and end-to-end tests

## Local Development

The repository is scaffolded for a Python + npm workflow.

1. Create a Python virtual environment.
2. Install backend dependencies from `apps/api/requirements-dev.txt`.
3. Install frontend dependencies from `apps/web/package.json`.
4. Run the API via `scripts/dev-api.sh`.
5. Run the web app via `scripts/dev-web.sh`.

## Logging

Runtime logs are structured and emoji-prefixed by convention:

- `🧭` orchestration
- `🗂️` task and project operations
- `🌿` git and worktree operations
- `🤖` agent operations
- `💬` waiting questions and replies
- `📡` session runtime and streaming
- `✅` checks and completions
- `⚠️` warnings
- `🧪` tests


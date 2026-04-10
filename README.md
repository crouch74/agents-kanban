# Agent Control Plane

Agent Control Plane is a local-first control plane for a single technical
operator managing multiple AI agents across multiple repositories and projects.
It combines a structured kanban workflow, tmux-backed session runtime, git
worktree isolation, a FastAPI backend, a React operator UI, and an MCP-native
agent surface.

## Current State

This repository is beyond scaffold stage. The current implementation includes:

- projects with one default board per project
- canonical kanban columns: `Backlog`, `Ready`, `In Progress`, `Review`, `Done`
- tasks and one level of subtasks
- task dependencies, comments, checks, and artifacts
- repository registration for local git repositories
- deterministic task-linked git worktree allocation and lifecycle management
- tmux-backed agent sessions with status, tail, timeline, cancel, and follow-up
  workflows
- waiting questions and human replies with resume semantics
- append-only audit events and dashboard/activity views
- global search across key operator surfaces
- a real MCP server with typed tools/resources and idempotent write support
- startup runtime reconciliation and worktree hygiene diagnostics
- live WebSocket-driven UI refresh on committed mutations

The backend plus SQLite plus append-only events are the system of record. The UI
and MCP server are clients of those domain services.

## What Is Still Deferred

The app is useful today, but v1 is not fully complete yet. Notable deferred
areas:

- richer export/import and backup flows
- deeper UI decomposition from the current large operator shell
- stronger Alembic-driven schema evolution instead of relying primarily on
  `create_all`
- more complete end-to-end browser coverage
- richer artifact storage and log ingestion
- broader planner/reviewer orchestration workflows beyond the current
  follow-up-session model

## Stack

- Backend: Python, FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2,
  Alembic, structlog
- Frontend: React, TypeScript, Vite, TanStack Query, Zustand, Tailwind CSS
- Runtime: SQLite in WAL mode, tmux, git worktrees
- Agent interface: official MCP Python SDK

## Repo Layout

- `apps/api`: FastAPI HTTP and WebSocket entrypoints
- `apps/web`: React operator UI
- `packages/core`: shared models, schemas, services, adapters, settings
- `packages/mcp-server`: MCP server entrypoint built on shared services
- `packages/sdk`: lightweight TypeScript types used by the web app
- `docs/prd`: product, API, domain, state, and implementation docs
- `docs/adr`: architecture decisions
- `scripts`: local bootstrap and dev helpers
- `tests`: integration and end-to-end coverage

## Local Development

Bootstrap once:

1. Run `scripts/bootstrap.sh`

Run the backend:

1. Run `scripts/dev-api.sh`

Run the web app:

1. Run `scripts/dev-web.sh`

Useful test commands:

- `.venv/bin/pytest tests/integration -q`
- `npm --workspace @acp/web run test`
- `npm --workspace @acp/web run build`
- `npm run test:e2e`

## Runtime Conventions

- `ACP_RUNTIME_HOME` controls the local data directory. By default it is
  `.acp/` in the repo root.
- SQLite runs in WAL mode with foreign keys enabled.
- tmux session names are deterministic and prefixed with `acp-`.
- Worktree branch names are deterministic and task-derived.
- Structured logs use emoji prefixes for fast scanning.

## Docs

- [Current State](/Users/aeid/git_tree/kanban/docs/prd/current-state.md)
- [Refined PRD](/Users/aeid/git_tree/kanban/docs/prd/refined-prd.md)
- [Domain Model](/Users/aeid/git_tree/kanban/docs/prd/domain-model.md)
- [State Machines](/Users/aeid/git_tree/kanban/docs/prd/state-machines.md)
- [API Outline](/Users/aeid/git_tree/kanban/docs/prd/api-outline.md)
- [MCP Surface](/Users/aeid/git_tree/kanban/docs/prd/mcp-surface.md)
- [Architecture Decisions](/Users/aeid/git_tree/kanban/docs/adr/0001-modular-monolith.md)
- [Agent Guide](/Users/aeid/git_tree/kanban/AGENTS.md)

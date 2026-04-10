# Agent Control Plane

<!-- TODO(maintainer): replace OWNER/REPO in CI and coverage badges once repository slug is confirmed. -->
[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-artifact%20in%20CI-blue)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![Node 22](https://img.shields.io/badge/node-22-5FA04E?logo=node.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi&logoColor=white)
![React 19](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)

Agent Control Plane is a local-first control plane for a single technical
operator managing multiple AI agents across multiple repositories and projects.
It combines a structured kanban workflow, tmux-backed session runtime, git
worktree isolation, a FastAPI backend, a React operator UI, and an MCP-native
agent surface.

## Stack

- Backend: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, structlog
- Frontend: React 19, TypeScript, Vite, TanStack Query, Tailwind CSS
- Verification: pytest (+pytest-cov), Vitest, Playwright
- Runtime: SQLite (WAL), tmux, git worktrees
- Package management: `pip` in `.venv`, `npm` workspaces

## Verification

Canonical commands (used by local development, Codex Cloud, and GitHub Actions):

1. Bootstrap everything from a clean checkout:

   ```bash
   bash scripts/bootstrap.sh
   ```

2. Run all verification:

   ```bash
   bash scripts/verify.sh
   ```

3. Optional explicit entrypoints:

   ```bash
   bash scripts/test_integration.sh
   bash scripts/test_ui.sh
   ```

CI workflow (`.github/workflows/ci.yml`) runs on pull requests and pushes to
`main` inside a repo-owned Docker image (`Dockerfile.ci`), bootstraps from
scratch, runs `scripts/verify.sh`, and uploads coverage (`coverage.xml`) plus
Playwright artifacts (`playwright-report/`, `test-results/`).

## Current State

This repository is beyond scaffold stage. The current implementation includes:

- projects with one default board per project
- guided project bootstrap from repo path, stack preset, and kickoff prompt
- canonical kanban columns: `Backlog`, `Ready`, `In Progress`, `Review`, `Done`
- tasks and one level of subtasks
- task dependencies, comments, checks, and artifacts
- repository registration for local git repositories
- optional repo initialization and starter scaffold for empty folders
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

## Local Development

Recommended single entrypoint:

1. Run `scripts/dev-stack.sh`

This script:

- bootstraps local dependencies when needed
- starts API, web, and MCP by default
- writes per-service logs under `.acp/logs/dev/`
- streams prefixed live logs in one terminal
- stops all managed processes on `Ctrl-C`

Useful variants:

- `scripts/dev-stack.sh --no-mcp`
- `scripts/dev-stack.sh --api-only`
- `scripts/dev-stack.sh --web-only`
- `scripts/dev-stack.sh --mcp-only`
- `scripts/dev-stack.sh --no-bootstrap`

## Runtime Conventions

- `ACP_RUNTIME_HOME` controls the local data directory. By default it is
  `.acp/` in the repo root.
- SQLite runs in WAL mode with foreign keys enabled.
- tmux session names are deterministic and prefixed with `acp-`.
- Worktree branch names are deterministic and task-derived.
- Structured logs use emoji prefixes for fast scanning.

## Docs

- [Current State](docs/prd/current-state.md)
- [Refined PRD](docs/prd/refined-prd.md)
- [Domain Model](docs/prd/domain-model.md)
- [State Machines](docs/prd/state-machines.md)
- [API Outline](docs/prd/api-outline.md)
- [MCP Surface](docs/prd/mcp-surface.md)
- [Architecture Decisions](docs/adr/0001-modular-monolith.md)
- [Agent Guide](AGENTS.md)

# `apps/api` Module Guide

## Purpose
`apps/api` hosts the FastAPI application that exposes Agent Control Plane REST APIs and WebSocket broadcast endpoints. It is the primary operator-facing backend surface and delegates business logic to shared services in `packages/core`.

## Shared Glossary
- Canonical terms used by this module (for example `workflow_state`, blocked/waiting overlays, completion readiness, and audit events) are defined in [`docs/glossary.md`](../../docs/glossary.md).

## Key Inputs / Outputs
- **Inputs**
  - HTTP requests under `/api/v1/*` (projects, tasks, sessions, diagnostics, search, etc.).
  - WebSocket client connections under the ws router for live mutation updates.
  - Runtime settings from environment variables (via shared settings).
  - SQLite-backed state and append-only event writes through `acp_core` services.
- **Outputs**
  - JSON API responses with structured read models.
  - Validation and transition errors when workflow rules are not satisfied.
  - WebSocket broadcast events for UI cache invalidation and live updates.
  - Structured logs for API/runtime operations.

## Dependencies
- Python 3.12+
- FastAPI, Uvicorn, Pydantic v2, SQLAlchemy, Structlog
- Local package dependency: `acp-core` (editable install from `packages/core`)
- Runtime tools used by service layer: `tmux`, `git`

## Local Run Command(s)
- From repo root (recommended stack entrypoint):
  - `bash scripts/dev-stack.sh`
- API-only:
  - `bash scripts/dev-stack.sh --api-only`
- Direct API dev runner:
  - `bash scripts/dev-api.sh`

## Test Command(s)
- API + integration coverage suite:
  - `bash scripts/test_integration.sh`
- Full repository verification (includes API, lint, and UI checks):
  - `bash scripts/verify.sh`

## Known Limitations
- Local schema setup is still primarily `Base.metadata.create_all`; Alembic exists but migration-driven evolution is not yet complete.
- Some operational behavior (tmux/worktree/runtime) depends on local machine tooling and state, so CI and local behavior can differ when those tools are unavailable.
- API behavior parity with MCP is intentional but not perfect in every edge flow; new write behavior should continue to be added in shared services first.

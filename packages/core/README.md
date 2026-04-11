# `packages/core` Module Guide

## Purpose
`packages/core` is the shared domain/service layer for Agent Control Plane and the behavioral center of the system. It defines models, schemas, settings, runtime adapters, and canonical workflow/business logic used by both REST and MCP surfaces.

## Shared Glossary
- Canonical terms owned or enforced by core services (including `workflow_state`, blocked overlay, completion readiness, session lineage, and audit events) are defined in [`docs/glossary.md`](../../docs/glossary.md).

## Key Inputs / Outputs
- **Inputs**
  - Service method calls from API handlers and MCP handlers.
  - Database sessions and persisted domain entities.
  - Runtime adapter inputs for tmux sessions, git worktrees, and diagnostics actions.
- **Outputs**
  - Structured read models and write results for projects, tasks, sessions, repositories, and diagnostics.
  - Append-only event records for material state changes.
  - Deterministic workflow transition validation and completion/readiness gate enforcement.

## Dependencies
- Python 3.12+
- Pydantic v2, Pydantic Settings, SQLAlchemy 2, Structlog
- Runtime ecosystem assumptions: SQLite, tmux, git worktrees

## Local Run Command(s)
- Core is a shared library (no standalone server).
- Run consumers with auto-reload against core changes:
  - `bash scripts/dev-stack.sh`
  - `bash scripts/dev-stack.sh --api-only`
  - `bash scripts/dev-stack.sh --mcp-only`

## Test Command(s)
- Integration tests that cover service behavior through API and MCP:
  - `bash scripts/test_integration.sh`
- Targeted unit tests for service facades/legacy wrappers:
  - `.venv/bin/python -m pytest tests/unit/core -q`

## Known Limitations
- Schema evolution is conservative and not fully migration-driven yet.
- Some lineage and runtime context are still carried in runtime metadata fields.
- Legacy service wrapper paths still exist (`services_legacy.py`) while consolidation continues.

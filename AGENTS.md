# AGENTS.md

This file is the working agreement for future coding agents contributing to
Agent Control Plane.

## Product Intent

Build and extend a serious local-first control plane for one technical operator
managing multiple AI agents across projects and repositories.

This is:

- a control plane first
- a kanban board second
- a terminal viewer third

Do not turn it into a thin wrapper around raw terminals, and do not make the UI
the source of truth.

## Current Architecture

- `apps/api`: FastAPI entrypoints and WebSocket broadcast layer
- `packages/core`: models, schemas, settings, runtime adapter, and shared domain
  services
- `packages/mcp-server`: MCP tools/resources built on the same shared services
- `apps/web`: operator UI
- `packages/sdk`: lightweight TypeScript contracts

The shared service layer in `packages/core/src/acp_core/services.py` is the
behavioral center of the app.

The canonical local development entrypoint is `scripts/dev-stack.sh`. New local
services or long-running developer processes should be integrated into that
launcher instead of introducing another parallel startup path.

## Non-Negotiable Guardrails

### Source of truth

- The backend plus SQLite plus append-only events are the system of record.
- UI state is a cache and interaction layer, not an authority.
- tmux tail output is helpful evidence, not canonical state.

### Workflow model

- Keep canonical task workflow states in the backend.
- Blocked and waiting are overlays, not columns.
- Do not bypass transition validation in UI, REST, or MCP code.
- Do not bypass completion readiness when moving a task to `done`.

### API and MCP parity

- New material behavior should live in shared services first.
- REST and MCP should call into the same service-layer logic whenever possible.
- If you add a write flow to one surface and not the other, be explicit about
  why.

### Runtime and worktrees

- tmux remains the runtime backbone.
- git worktrees remain the isolation strategy.
- Session and worktree metadata must stay visible in structured state, not just
  logs.
- Diagnostics and recovery are product features. Do not hide drift.

## Current Technical Realities

- The repo still relies primarily on `Base.metadata.create_all` for local DB
  setup.
- Alembic exists, but schema evolution is not fully migration-driven yet.
- Session lineage is currently stored in `AgentSession.runtime_metadata`.
- The operator UI works, but `apps/web/src/App.tsx` is still too large.

This means:

- be conservative with schema changes
- prefer additive, backward-safe changes
- if a change truly needs a new durable relational model, update docs and make
  the migration path deliberate

## Coding Patterns to Preserve

### Services

- Keep handlers thin and business rules in services.
- Record an event for each material write.
- Return structured read models from the service layer where it improves parity.

### Logging

Use structured logs with meaningful emoji prefixes. Current conventions:

- `🧭` orchestration and recovery
- `🗂️` project/task operations
- `🌿` git and worktrees
- `🤖` agent operations
- `💬` waiting questions and replies
- `📡` session runtime and streaming
- `✅` checks and completions
- `⚠️` warnings
- `🧪` tests

### Frontend

- Prefer extracting focused components instead of growing `App.tsx` further.
- Keep TanStack Query as the async state layer.
- Use live mutation broadcasts to invalidate queries rather than inventing a
  parallel state system.
- Preserve the current operator-first UX: glanceable, intervention-friendly,
  local, and not overloaded.

### MCP

- Keep tool names predictable.
- Keep write operations idempotent where practical via `client_request_id`.
- Prefer exposing structured reads rather than expecting agents to scrape text.

## Documentation Rules

If you materially change behavior, update the docs in the same slice:

- `README.md` for onboarding/current-state summary
- `docs/prd/current-state.md` for as-built status
- `docs/prd/api-outline.md` for REST changes
- `docs/prd/mcp-surface.md` for MCP changes
- `docs/prd/state-machines.md` if transitions or gates change
- `docs/prd/domain-model.md` if aggregates/relationships change
- `docs/adr/*` when a durable architectural decision changes or a new one is
  introduced

## Testing Expectations

For meaningful changes, prefer covering the affected behavior in:

- integration tests under `tests/integration`
- web tests in `apps/web/src/App.test.tsx` or future component tests
- Playwright when the change is a critical end-to-end operator workflow

Minimum expectation:

- run `.venv/bin/pytest tests/integration -q`
- run `npm --workspace @acp/web run test`
- run `npm --workspace @acp/web run build`

## Safe Extension Areas

Good next slices:

- export/import and backup flows
- stronger diagnostics actions
- component extraction in the web UI
- richer e2e coverage
- better artifact and log handling

High-care areas:

- schema changes
- workflow semantics
- session/worktree ownership semantics
- API/MCP drift
- hidden state that is only visible in the UI

## Commit Hygiene

- Use small, reviewable commits.
- Follow Conventional Commit style.
- Keep commit scope aligned to a single slice when possible.

## If You Are Unsure

Prefer the simpler local-first option.
Prefer boring, explicit data over clever automation.
Prefer adding structure over asking humans or agents to infer state.
Prefer shared service logic over duplicating behavior in handlers or UI code.

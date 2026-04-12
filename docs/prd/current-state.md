# Current Implementation State

## Summary

The repository is currently in a meaningful pre-v1 but already-usable state. It
is no longer a scaffold or demo shell. The app supports real local operator
workflows across tasks, worktrees, sessions, waiting questions, and MCP-based
agent interaction.

## Implemented Areas

### Backend and persistence

- FastAPI app under `apps/api`
- shared domain/service layer under `packages/core`
- SQLite database with WAL mode and foreign keys enabled
- append-only `events` table for audit history
- startup runtime reconciliation

### Operator UI

- dashboard with projects, active sessions, blocked tasks, waiting questions,
  and recent events
- project overview composed from board, repositories, worktrees, sessions, and
  waiting questions
- project bootstrap wizard for repo path, stack preset, kickoff prompt, and
  optional worktree kickoff
- quick-create actions in the shell header for task entry and project bootstrap
- task inspector with subtasks, comments, checks, artifacts, and dependencies
- session runtime view with tail, timeline, waiting state, and session chain
- diagnostics panel with runtime orphan detection and worktree hygiene signals
- standalone activity timeline plus workspace-wide search and live refresh via
  WebSocket mutation broadcasts

### Domain behavior

- one board per project with default canonical columns
- one level of subtasks
- column WIP enforcement on task creation
- task transitions enforced in the service layer
- task completion readiness gate
- repository registration and metadata capture
- bootstrap flow for existing repos, empty folders, or brand-new paths when `initialize_repo` is enabled
- kickoff agent command runs in non-interactive mode via `codex -a never exec -s workspace-write` for tmux bootstrap sessions
- minimal starter scaffolds for a focused set of stack presets
- deterministic worktree allocation and lifecycle updates
- tmux-backed sessions with cancel and follow-up flows
- waiting question open/answer/resume flow

### MCP

- production MCP tool surface over the shared services
- idempotent writes via `client_request_id`
- resource endpoints for board, task, completion, sessions, repos, diagnostics,
  and events

### Testing

- integration coverage for projects, tasks, evidence, repositories, worktrees,
  sessions, waiting questions, search, diagnostics, live WebSocket behavior,
  recovery, and MCP handlers
- Python integration coverage gate enforced at **84% minimum** total coverage
  (`scripts/test_integration.sh` with `--cov-fail-under=84`)
- Vitest web unit coverage reporting enabled with minimum thresholds of
  **70% lines / 70% statements / 70% functions / 60% branches**
- one Playwright smoke test for the web shell
- one Vitest app-shell test

### Local developer runtime

- `scripts/dev-stack.sh` bootstraps when needed and starts API, web, and MCP in
  one terminal session
- live logs are multiplexed with stable service prefixes
- raw per-service logs are written under `.acp/logs/dev`

## Known Implementation Limits

- `apps/web/src/App.tsx` is still too large and should be decomposed carefully
  without changing behavior
- Alembic exists, but the current runtime still relies heavily on
  `Base.metadata.create_all`; schema changes must be made conservatively
- session lineage currently lives in `runtime_metadata` instead of a dedicated
  relational table
- board customization and settings UX are still light
- artifact storage is metadata-first rather than a comprehensive managed asset
  subsystem
- e2e coverage is still shallow

## Recommended Next Work

- export/import and backup flows
- stronger schema migration discipline
- richer component extraction in the web app
- more complete e2e coverage for waiting, recovery, and worktree/session flows
- better operator actions from diagnostics

## Operational Truths to Preserve

- the backend and database own state, not the UI
- API and MCP must remain behaviorally aligned through the shared service layer
- blocked and waiting are overlays, not separate workflow columns
- done is gated by evidence and unresolved blockers
- raw tmux output is useful, but it is not the source of truth

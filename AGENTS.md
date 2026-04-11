# AGENTS.md
> This file governs all AI agent behavior in this repository.
> Every agent session (Codex, Claude Code, Copilot, etc.) must read
> this file before taking any action. Last updated: 2026-04-11

## 1. Repo Overview
- Agent Control Plane is a local-first control plane for one technical operator managing multiple AI agents across repositories and projects. It combines a canonical backend workflow state machine, append-only audit events, tmux-backed runtime sessions, deterministic git worktrees, a FastAPI API + WebSocket layer, a React operator UI, and an MCP server that reuses backend service logic.
- Primary tech stack:
  - Python 3.12+ (FastAPI 0.116.x, SQLAlchemy 2.0.x, Pydantic v2, Alembic, structlog, pytest).
  - TypeScript + React 19 (Vite 7, Vitest 3, TanStack Query 5, Zustand, Tailwind CSS 4).
  - MCP Python server (`mcp` package 1.9.x) sharing `acp_core` services.
  - SQLite (WAL mode) as local durable store.
  - tmux + git worktrees as runtime isolation primitives.
  - npm workspaces + package-lock for JS dependency locking.
- Architecture pattern and layer rules:
  - Modular-monolith backend with shared service layer (`packages/core/src/acp_core/services/*`) as behavior center.
  - API handlers and MCP handlers are thin orchestration adapters and should delegate material behavior to shared services.
  - Backend + SQLite + append-only events are canonical truth; UI is cache/interaction layer.
  - Blocked/waiting are overlays, not canonical task workflow states.
- Monorepo structure:
  - `apps/api` (FastAPI surface)
  - `apps/web` (React operator UI)
  - `packages/core` (domain models, schemas, settings, runtime adapters, services)
  - `packages/mcp-server` (MCP tools/resources)
  - `packages/sdk` (TypeScript contracts)
  - `tests` (integration/unit/e2e)

## 2. Getting Started
Exact commands:
- Install dependencies:
  - `bash scripts/bootstrap.sh`
- Set up environment:
  - `cp .env.example .env`
- Run dev server (full stack):
  - `bash scripts/dev-stack.sh`
- Run database migrations / seeds:
  - Migrations are not the primary local path yet; current bootstrap path is implicit DB creation via service startup (`Base.metadata.create_all`).
  - Alembic exists under `apps/api/alembic`, but a canonical migration command is **[NOT YET ESTABLISHED — recommend: document and standardize `alembic upgrade head` path]**.
  - Seed command is **[NOT YET ESTABLISHED — recommend: add explicit `scripts/seed.sh` if needed]**.
- Verify setup is working:
  - `bash scripts/verify.sh`
  - Optional focused checks:
    - `bash scripts/test_integration.sh`
    - `bash scripts/test_ui.sh`

## 3. Project Structure
Annotated top-level tree:
- `.github/` — CI/CD and security workflows, allowlists, automation policy.
- `apps/`
  - `apps/api/` — FastAPI entrypoint, REST routes, WebSocket hub/events, bootstrap DI.
  - `apps/web/` — React/Vite operator UI, feature containers, state/query wiring, tests.
- `packages/`
  - `packages/core/` — shared backend domain entities, DB models, schemas, runtime adapters, service layer.
  - `packages/mcp-server/` — MCP server and handlers using shared services.
  - `packages/sdk/` — lightweight TypeScript SDK/contracts.
- `tests/`
  - `tests/integration/` — Python API/MCP/runtime integration tests.
  - `tests/unit/` — targeted backend unit/service compatibility tests.
  - `tests/e2e/` — Playwright UI workflows.
- `scripts/` — canonical bootstrap/dev/verify/lint/test/codegen automation.
- `docs/` — PRD, ADR, API artifacts/specs, setup guides, glossary.
- `docker-compose.yml` — containerized local stack option.
- `AGENTS.md` — cross-agent operating contract.

## 4. Architecture Rules
- Layer dependency direction (enforced):
  - `apps/api` and `packages/mcp-server` → `packages/core`.
  - `packages/core` must not depend on API or MCP layers.
  - UI (`apps/web`) consumes API/WebSocket contracts; it must not become system-of-record.
- What belongs where:
  - `packages/core`: business rules, transition validation, readiness gates, durable writes, event recording.
  - `apps/api`: HTTP serialization, auth boundary, request/response mapping, websocket broadcast triggers.
  - `packages/mcp-server`: MCP tool/resource schemas + handler glue to services.
  - `apps/web`: presentation, operator workflow UX, query/mutation orchestration.
- Import rules:
  - Keep Python imports grouped stdlib → third-party → local package imports.
  - Prefer domain service imports from `acp_core.services.<domain>_service` modules (compat layer exists but is transitional).
  - Frontend uses `@/` alias for `apps/web/src` imports.
- Business logic placement:
  - Must live in shared service layer (`packages/core/src/acp_core/services/*`).
  - Must NOT be duplicated in route handlers, MCP handlers, or React components.
- Patterns:
  - Dependency injection: FastAPI `Depends(...)` + bootstrap dependency providers.
  - Error handling: services raise `ValueError` for domain/validation failures; API maps to `HTTPException` with 4xx.
  - Async operations: backend endpoints are mostly sync functions; lifespan + websocket runtime use async where needed; frontend uses async/await with TanStack Query.
  - Configuration: `pydantic-settings` via `Settings` with `ACP_` env prefix.

## 5. Coding Conventions
- File naming:
  - Python modules: `snake_case.py` (example: `task_service.py`).
  - React components/screens: mostly `PascalCase.tsx` (example: `ProjectBoardScreen.tsx`).
  - Some frontend files use kebab-case (example: `project-bootstrap-wizard.tsx`) — **[NOT YET ESTABLISHED — recommend: settle on PascalCase for components and kebab-case for non-component utility files]**.
- Function naming:
  - Python: `snake_case` (example: `reconcile_runtime_sessions`).
  - TS/React: `camelCase` for functions/hooks; React components in `PascalCase`.
- Class naming:
  - `PascalCase` (example: `TaskService`, `Settings`, SQLAlchemy model classes).
- Constant naming:
  - Python constants are uppercase snake case where used (example: workflow mapping constants).
  - TS constants generally `camelCase`/`const` style in-module — **[NOT YET ESTABLISHED — recommend: uppercase snake case for exported immutable constants]**.
- Variable naming:
  - Python: `snake_case`.
  - TypeScript: `camelCase`.
- Max file size:
  - **[NOT YET ESTABLISHED — recommend: 400 lines soft limit; split by feature responsibility]**.
- Max function size:
  - **[NOT YET ESTABLISHED — recommend: 60 lines soft limit excluding docstring/types]**.
- Cyclomatic complexity limit:
  - **[NOT YET ESTABLISHED — recommend: <= 10 per function]**.
- Import ordering:
  - Python: stdlib, third-party, local modules with blank lines between groups.
  - TypeScript: external deps first, then internal `@/` imports.
- Comment style:
  - Explain intent/invariants and non-obvious decisions.
  - Avoid narrating obvious code.
  - Keep TODO/FIXME usage minimal and tracked (see behavioral rules).

## 6. Error Handling Rules
- Use types/scenarios:
  - Service/domain validation failures: raise `ValueError` with operator-useful message.
  - API routes: convert service `ValueError` to `HTTPException` (usually 400/404).
  - Request schema violations: let FastAPI/Pydantic return 422 automatically.
- External call failures:
  - Wrap git/tmux/runtime failures in service-level structured errors/events with context in payload metadata; do not silently drop failures.
- Required error context fields (logs/events):
  - `actor_type`, `actor_name`, `entity_type`, `entity_id`, `event_type`, correlation metadata when available.
  - Include project/task/session/worktree identifiers when known.
- What to log on error:
  - Emoji-prefixed structured log with subsystem marker (`⚠️`, `🧭`, `🌿`, `🤖`, etc.) and key IDs.
- Never expose in API error responses:
  - stack traces
  - raw SQL queries
  - filesystem internals beyond intended operator metadata
  - host/container absolute paths unrelated to task context
- Retry strategy:
  - **[NOT YET ESTABLISHED — recommend: bounded retries with backoff only for transient runtime/tooling operations (tmux/git/network), never for deterministic validation failures]**.

## 7. Testing Standards
- Frameworks/config:
  - Python: `pytest` (+ `pytest-asyncio`, `pytest-cov`) configured via `pytest.ini`.
  - Web unit: `Vitest` config in `apps/web/vite.config.ts`.
  - E2E: Playwright config in `playwright.config.ts`.
- Test file naming:
  - Python: `test_*.py` by behavior slice (example: `test_tasks_api.py`).
  - Web tests: `*.test.tsx` / `*.spec.ts` (example: `activity-timeline.test.tsx`).
- Test naming:
  - Python style in repo: `test_<behavior>_<condition/result>`.
  - Vitest style in repo: sentence-style `test('renders ...', ...)`.
  - `should ... when ...` phrasing is **[NOT YET ESTABLISHED — recommend for newly added tests]**.
- AAA pattern:
  - Present in many tests but not formally mandated — **[NOT YET ESTABLISHED — recommend: explicit Arrange/Act/Assert blocks for new tests]**.
- Mocking boundary:
  - Mock at I/O/runtime edges (tmux, git, HTTP, filesystem, time); keep service/state semantics real in integration tests.
- Coverage thresholds:
  - Python integration: `--cov-fail-under=84`.
  - Web (Vitest): lines 70 / statements 70 / functions 70 / branches 60.
- Commands:
  - Run all tests: `bash scripts/verify.sh --skip-bootstrap`
  - Run with coverage: `bash scripts/test_integration.sh`
  - Run single file: `.venv/bin/python -m pytest tests/integration/test_tasks_api.py -q`
  - Run in watch mode: **[NOT YET ESTABLISHED — recommend: add vitest watch script if needed]**

## 8. CI/CD & Quality Gates
- Pipeline stages/order:
  - CI (`.github/workflows/ci.yml`): `quick-checks` → (`python-tests`, `web-unit-build`) → `playwright-e2e`; PR-only screenshot-evidence job also runs after quick checks + web build.
  - Additional workflows: `security.yml`, `security-analysis.yml` (CodeQL), `container-image-security.yml`.
- Must-pass gates for merge to `main`:
  - Python import lint (`ruff F401` subset)
  - OpenAPI artifact drift check
  - Web TypeScript check
  - Integration tests + coverage gate
  - Web unit tests + build
  - Playwright tests
  - Security scans (dependency/secret/code scanning/container policies per workflow settings)
- Local commands mirroring CI:
  - Lint: `bash scripts/lint_python.sh`
  - Format check: `.venv/bin/ruff format --check apps/api packages/core/src packages/mcp-server/src tests`
  - Type check: `npm run lint:web`
  - Tests: `bash scripts/verify.sh --skip-bootstrap`
  - Full CI sim: `bash scripts/verify.sh`

## 9. Domain Knowledge
- Glossary (key terms):
  - `workflow_state`: canonical task lifecycle (`backlog`, `ready`, `in_progress`, `review`, `done`, `cancelled`).
  - `blocked overlay`: `blocked_reason` without changing canonical workflow state.
  - `waiting overlay`: `waiting_for_human` marker tied to waiting-question flow.
  - `completion readiness`: gate for `done` transitions based on checks/artifacts/dependencies/open questions.
  - `session lineage`: parent/follow-up lineage currently in `AgentSession.runtime_metadata`.
  - `worktree hygiene`: diagnostics posture for stale/orphan/misaligned worktrees.
  - `audit event`: append-only mutation trail.
- Core business rules (never violate):
  - Task transitions must follow allowed state machine.
  - `done` requires readiness gate pass.
  - Blocked/waiting are overlays, not replacement columns/states.
  - Every material write should emit an event.
  - API and MCP behavior should stay parity-aligned via shared services.
- Invariants by entity:
  - Project owns one board (current implementation).
  - Task subtasks are one level deep only.
  - Worktrees belong to repositories and may link to task/session context.
  - Waiting questions can drive session wait/resume semantics.
- State machines:
  - Task transitions:
    - `backlog <-> ready`
    - `ready <-> in_progress`
    - `in_progress <-> review`
    - `review <-> done`
    - Any state → `cancelled` (as documented)
  - Waiting question: `open -> answered -> closed`, or `open -> dismissed`.
  - Session statuses include: `queued`, `running`, `waiting_human`, `blocked`, `done`, `failed`, `cancelled` with runtime reconciliation on startup.
  - Worktree lifecycle: `requested -> provisioning -> active/ error`, then archival/pruning/lock flows.
- External service contracts and SLAs:
  - No formal SLA docs found.
  - External integrations currently include tmux runtime, git worktrees, MCP protocol tools/resources, and local filesystem paths.
  - **[NOT YET ESTABLISHED — recommend: define expected response-time/error-budget targets for API and runtime operations]**.

## 10. Agent Behavioral Rules
Rules that apply to EVERY agent in EVERY session:

### Before Starting Any Task
- [ ] Read this entire file.
- [ ] Run `bash scripts/verify.sh --skip-bootstrap` and confirm baseline (or report environmental blockers immediately).
- [ ] Understand task scope; if ambiguous, follow Ambiguity Protocol.
- [ ] Identify impacted layers/modules before editing.

### What Agents MUST Do
- Keep commits atomic (one logical slice per commit).
- Use Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`).
- Add/update tests for behavior changes.
- Run full verification before PR: `bash scripts/verify.sh --skip-bootstrap` (or `bash scripts/verify.sh` when dependencies may be stale).
- Preserve backend-as-source-of-truth model.
- Keep API and MCP logic aligned via shared services.
- Keep handlers thin; place material behavior in `packages/core` services.

### What Agents MUST NEVER Do
- Modify generated/dependency/runtime artifacts directly:
  - `node_modules/`, `coverage/`, `playwright-report/`, `test-results/`, `.acp/`, `.artifacts/`.
- Bypass workflow transition validation or completion readiness gates.
- Change public API/MCP contract shape without docs + artifact updates (`docs/api/openapi-v1.json`, PRD/API docs as applicable).
- Add dependencies without explicit human approval.
- Use `Any`/`any` or type-ignore suppression without inline justification.
- Swallow errors silently.
- Add TODO/FIXME/HACK comments without a linked tracking issue.
- Auto-merge PRs.
- Commit directly to `main`.
- Delete tests merely to satisfy coverage gates.
- Use arbitrary sleep-based waits in tests when deterministic waits are possible.

### Ambiguity Protocol
If a task is ambiguous:
1. List plausible interpretations.
2. State recommended interpretation and rationale.
3. STOP and await human confirmation before implementation.

### Scope Creep Protocol
If related issues are discovered during assigned work:
1. Note them in `FINDINGS.md`.
2. Complete only assigned task.
3. Do not bundle unrelated fixes in same PR.

## 11. Known Issues & Deferred Debt
Known deferred items (do not fix unless explicitly tasked):
- README badge placeholder still references `OWNER/REPO` — `README.md` — deferred until repository slug is finalized.
- `apps/web/src/App.tsx` remains too large — frontend architecture debt tracked in docs; extract components without behavior drift when explicitly tasked.
- Schema evolution is still largely `Base.metadata.create_all` driven — migration discipline is intentionally gradual.
- Session lineage remains in `AgentSession.runtime_metadata` instead of dedicated relational model.
- E2E coverage remains shallow relative to critical workflows.

TODO/FIXME/HACK scan results:
- `TODO(maintainer): replace OWNER/REPO in CI and coverage badges once repository slug is confirmed.` (`README.md`)

## 12. Changelog
| Date | Author | Change |
|------|--------|--------|
| 2026-04-11 | Codex (generated) | Replaced AGENTS.md with repository-wide cross-agent governance based on full repo scan; marked non-established conventions explicitly. |

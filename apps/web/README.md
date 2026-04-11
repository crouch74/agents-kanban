# `apps/web` Module Guide

## Purpose
`apps/web` is the operator UI for Agent Control Plane. It presents a glanceable local-first dashboard/kanban experience, drives operator actions, and consumes REST + WebSocket signals from the backend.

## Key Inputs / Outputs
- **Inputs**
  - REST API responses from `apps/api`.
  - WebSocket mutation broadcasts for live invalidation/refresh.
  - Operator interactions (project bootstrap, task state changes, session actions, diagnostics actions).
- **Outputs**
  - Interactive control-plane UI views (board, task detail, sessions, activity, diagnostics).
  - Mutating API requests back to backend endpoints.
  - Local async cache behavior through TanStack Query.

## Dependencies
- Node.js 22+
- React 19, TypeScript, Vite, TanStack Query, Tailwind CSS
- Local package dependency: `@acp/sdk` from `packages/sdk`

## Local Run Command(s)
- From repo root (recommended full stack):
  - `bash scripts/dev-stack.sh`
- Web-only stack:
  - `bash scripts/dev-stack.sh --web-only`
- Direct web dev server:
  - `bash scripts/dev-web.sh`
  - or `npm --workspace @acp/web run dev`

## Test Command(s)
- Web unit tests:
  - `npm --workspace @acp/web run test`
- Type/lint check:
  - `npm --workspace @acp/web run lint`
- Full UI verification (unit + build + Playwright smoke):
  - `bash scripts/test_ui.sh`

## Known Limitations
- `apps/web/src/App.tsx` remains large and should continue to be decomposed into focused components.
- The UI is intentionally not the source of truth; stale local cache can appear briefly until query invalidation/refetch completes.
- Browser E2E checks rely on Playwright browser installation in the local environment.

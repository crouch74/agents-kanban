# `packages/sdk` Module Guide

## Purpose
`packages/sdk` contains lightweight TypeScript contracts for frontend consumption of backend APIs, including generated OpenAPI-derived types and SDK re-exports.

## Shared Glossary
- Canonical vocabulary represented in generated contracts (for example `workflow_state`, waiting-question fields, and completion-readiness data) is defined in [`docs/glossary.md`](../../docs/glossary.md).

## Key Inputs / Outputs
- **Inputs**
  - Backend OpenAPI schema (`/openapi.json`) for type generation.
  - TypeScript imports from consuming apps (primarily `apps/web`).
- **Outputs**
  - Typed API contracts re-exported through `src/index.ts`.
  - Generated contract file (`src/generated.ts`) updated from backend schema.

## Dependencies
- Node.js 22+
- TypeScript
- `openapi-typescript` (run from repository root scripts)

## Local Run Command(s)
- Regenerate SDK contracts from a running local API:
  - `npm run codegen:sdk`

## Test Command(s)
- SDK correctness is primarily validated transitively by web type-check/build:
  - `npm --workspace @acp/web run lint`
  - `npm --workspace @acp/web run build`

## Known Limitations
- No standalone test suite exists in this package yet.
- Generated types are only as current as the last `codegen:sdk` run against the active API schema.
- Runtime client behavior is intentionally minimal; this package focuses on contracts.

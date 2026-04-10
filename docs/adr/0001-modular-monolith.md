# ADR 0001: Modular Monolith

## Status

Accepted

## Decision

Build Agent Control Plane as a modular monolith with these top-level
responsibilities:

- `apps/api` for HTTP and WebSocket entrypoints
- `packages/core` for models, schemas, domain services, runtime and git
  adapters, and settings
- `packages/mcp-server` for the MCP entrypoint
- `apps/web` for the operator UI
- `packages/sdk` for lightweight TypeScript contracts consumed by the web app

## Why

- local-first deployment favors low operational complexity
- single-operator usage does not justify distributed services
- shared domain rules reduce drift between REST and MCP surfaces
- debugging is easier when the runtime, DB, and service layer live in one repo

## Consequences

- the shared service layer is the extension point and must stay disciplined
- API handlers and MCP handlers should stay thin
- if we later split services, the domain boundaries in `packages/core` are the
  seams to preserve

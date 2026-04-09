# ADR 0001: Modular Monolith

## Status

Accepted

## Decision

Build Agent Control Plane as a modular monolith with:

- `apps/api` for HTTP/WebSocket entry points
- `packages/core` for domain logic and adapters
- `packages/mcp-server` for the MCP entry point
- `apps/web` for the operator UI

## Why

- local-first deployment favors low operational complexity
- one operator does not need distributed services
- shared domain rules reduce drift between API and MCP surfaces


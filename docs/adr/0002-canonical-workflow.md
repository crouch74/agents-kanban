# ADR 0002: Canonical Workflow States

## Status

Accepted

## Decision

Use canonical backend workflow states for tasks, with board columns mapping onto
those states for presentation and light customization.

The canonical states are:

- `backlog`
- `ready`
- `in_progress`
- `review`
- `done`
- `cancelled`

Blocked and waiting remain overlays instead of bespoke workflow columns.

## Why

- agent tools need deterministic semantics
- crash recovery and search are simpler when workflow state is normalized
- standard kanban reporting remains possible
- the operator can still see blocked/waiting work inside the actual flow stage

## Consequences

- service-layer transition rules are authoritative
- UI drag/drop must defer to backend validation
- API and MCP writes must not bypass transition logic

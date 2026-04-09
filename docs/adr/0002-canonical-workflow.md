# ADR 0002: Canonical Workflow States

## Status

Accepted

## Decision

Use canonical backend workflow states for tasks and sessions. Project boards map
columns onto those states for presentation and limited customization.

Blocked and waiting remain overlays instead of bespoke columns.

## Why

- agent tools need deterministic state semantics
- crash recovery and search become simpler
- standard kanban reporting remains possible


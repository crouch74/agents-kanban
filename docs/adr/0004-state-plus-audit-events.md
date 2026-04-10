# ADR 0004: Current State Tables Plus Audit Events

## Status

Accepted

## Decision

Use normalized current-state tables for operational reads and an append-only
`events` table for auditability and activity/history views.

This is not full event sourcing. The events table complements current state
rather than replacing it.

## Why

- operators need fast current-state queries
- future agents need audit visibility without scraping logs
- session timelines, dashboard activity, and search benefit from durable events
- this is much simpler than a full replay architecture for a local-first tool

## Consequences

- every material write should emit an event
- API and MCP writes should continue to share the same service-layer event
  emission path
- if a new feature changes durable state and does not emit an event, it is
  probably incomplete

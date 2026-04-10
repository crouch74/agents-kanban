# ADR 0006: Session Lineage in Runtime Metadata

## Status

Accepted

## Decision

Track session-family lineage and follow-up relationships inside
`AgentSession.runtime_metadata` for now, instead of introducing a new relational
table immediately.

This currently carries values such as:

- `session_family_id`
- `follow_up_of_session_id`
- `follow_up_type`
- `source_profile`

## Why

- the repo still relies primarily on `Base.metadata.create_all` for local DB
  bootstrapping
- we wanted follow-up session chains without forcing a breaking local schema
  migration
- the metadata approach is enough for timeline and operator workflow needs today

## Consequences

- session lineage queries must continue to go through the service layer rather
  than ad-hoc JSON parsing in handlers
- if we later move to a dedicated relational model, preserve the current session
  family semantics and follow-up types
- future agents should not scatter lineage logic across the UI

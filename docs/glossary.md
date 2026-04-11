# Agent Control Plane Glossary

This glossary defines core domain and runtime terms used across the control
plane. Treat these definitions as shorthand; canonical behavior remains defined
in the linked PRD and ADR documents.

## Workflow & state terms

### workflow_state
The canonical backend lifecycle state for a task (`backlog`, `ready`,
`in_progress`, `in_review`, `done`). This is the normalized workflow truth used
for validation, transitions, and search; board columns map onto this state
rather than replacing it.

Canonical references:
- [Domain model: Task aggregate + invariants](./prd/domain-model.md)
- [State machine: task workflow states and transitions](./prd/state-machines.md)
- [ADR 0002: canonical workflow](./adr/0002-canonical-workflow.md)

### blocked overlay
A non-column, non-state overlay indicating operational blockage while a task
remains in its current canonical `workflow_state`. Implemented as
`blocked_reason` metadata so operators can see blockage without inventing
parallel workflow columns.

Canonical references:
- [Domain model: overlays on Task](./prd/domain-model.md)
- [State machine: blocked/waiting overlays](./prd/state-machines.md)
- [ADR 0002: overlays vs workflow columns](./adr/0002-canonical-workflow.md)

### completion readiness
A gate that must pass before a task may transition to `done`. Readiness is
computed from checks, artifacts, dependencies, and waiting-question state so
`done` represents verifiable completion.

Canonical references:
- [Domain model: computed readiness](./prd/domain-model.md)
- [State machine: `done` transition gate](./prd/state-machines.md)
- [ADR 0005: evidence-gated completion](./adr/0005-evidence-gated-completion.md)

## Human-in-the-loop terms

### waiting question
A durable human-input request opened by an agent/session when it cannot proceed
autonomously. A waiting question can carry urgency, prompt, and optional answer
choices; answering it drives resume semantics for the related workflow.

Canonical references:
- [Domain model: waiting question + answer entities](./prd/domain-model.md)
- [State machine: waiting overlay and session transitions](./prd/state-machines.md)
- [ADR 0002: waiting as overlay](./adr/0002-canonical-workflow.md)

## Runtime terms

### session lineage
Parent/child and restart lineage metadata for agent sessions, currently stored
additively in session runtime metadata rather than a dedicated relational table.
Used for timeline context, diagnostics, and recovery reasoning.

Canonical references:
- [Domain model: session lineage notes](./prd/domain-model.md)
- [Current state: lineage implementation reality](./prd/current-state.md)
- [ADR 0006: lineage in metadata](./adr/0006-session-lineage-in-metadata.md)

### worktree hygiene
Diagnostics posture around keeping git worktree state healthy and explainable
(for example: stale/orphan detection, branch/task alignment, and cleanup
visibility). Hygiene is a product feature surfaced in structured diagnostics, not
just log text.

Canonical references:
- [Current state: diagnostics + hygiene coverage](./prd/current-state.md)
- [Domain model: project/task/session/worktree relationships](./prd/domain-model.md)
- [ADR 0003: runtime model and operator diagnostics](./adr/0003-runtime-model.md)

## Auditability terms

### audit event
An append-only event record emitted for each material write. Current-state
tables power operational reads; audit events provide durable history for
traceability, timeline context, and recovery analysis.

Canonical references:
- [Domain model: append-only event history](./prd/domain-model.md)
- [Current state: events table](./prd/current-state.md)
- [ADR 0004: state plus audit events](./adr/0004-state-plus-audit-events.md)

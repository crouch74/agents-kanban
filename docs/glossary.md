# Glossary

This glossary defines core terms used across Agent Control Plane docs, API/MCP
surfaces, and operator workflows.

## workflow_state

The canonical backend lifecycle state for a task: `backlog`, `ready`,
`in_progress`, `review`, `done`, or `cancelled`. Workflow state is authoritative
in the service layer and is normalized from board interactions where applicable.

Canonical references:

- [State Machines: Task Workflow](./prd/state-machines.md#task-workflow)
- [Domain Model: Task](./prd/domain-model.md#task)
- [ADR 0002: Canonical Workflow States](./adr/0002-canonical-workflow.md)

## blocked overlay

A non-column overlay that marks a task as blocked while preserving its canonical
workflow stage. It is represented by `blocked_reason` and intentionally remains
separate from `workflow_state`.

Canonical references:

- [State Machines: Task overlays](./prd/state-machines.md#task-overlays)
- [Domain Model: Task](./prd/domain-model.md#task)
- [ADR 0002: Canonical Workflow States](./adr/0002-canonical-workflow.md)

## waiting question

A durable human-in-the-loop interruption record attached to a task (and
optionally a session). Opening a waiting question sets the waiting overlay and
can pause a running session until a human reply is provided.

Canonical references:

- [State Machines: Waiting Question Workflow](./prd/state-machines.md#waiting-question-workflow)
- [Domain Model: Waiting Question](./prd/domain-model.md#waiting-question)
- [ADR 0002: Canonical Workflow States](./adr/0002-canonical-workflow.md)

## session lineage

The family/follow-up relationship between agent sessions, currently stored in
`AgentSession.runtime_metadata` (for example `session_family_id` and
`follow_up_of_session_id`) instead of a dedicated relational table.

Canonical references:

- [Domain Model: Agent Session](./prd/domain-model.md#agent-session)
- [Domain Model: Important Practical Limits](./prd/domain-model.md#important-practical-limits)
- [ADR 0006: Session Lineage in Runtime Metadata](./adr/0006-session-lineage-in-metadata.md)

## worktree hygiene

Operational cleanup and drift-detection behavior for worktrees, including
recommendations to inspect missing paths, archive completed session worktrees,
or prune archived stale entries.

Canonical references:

- [State Machines: Worktree Workflow](./prd/state-machines.md#worktree-workflow)
- [Domain Model: Worktree](./prd/domain-model.md#worktree)
- [ADR 0003: Runtime Model](./adr/0003-runtime-model.md)

## completion readiness

The gate that must pass before a task can transition to `done`: evidence
(checks/artifacts), no unresolved blocking dependencies, and no open waiting
questions.

Canonical references:

- [State Machines: Completion Readiness Gate](./prd/state-machines.md#completion-readiness-gate)
- [Domain Model: Important Practical Limits](./prd/domain-model.md#important-practical-limits)
- [ADR 0005: Evidence-Gated Completion](./adr/0005-evidence-gated-completion.md)

## audit event

An immutable append-only event record emitted on material writes, used for
activity history, timelines, diagnostics, and audit visibility.

Canonical references:

- [Domain Model: Event](./prd/domain-model.md#event)
- [State + Events architecture notes](./prd/domain-model.md#source-of-truth-model)
- [ADR 0004: Current State Tables Plus Audit Events](./adr/0004-state-plus-audit-events.md)

# ADR 0007: Schema Evolution Policy for Local-First Compatibility

## Status

Accepted

## Context

The current implementation uses two mechanisms for schema setup/evolution:

- `packages/core/src/acp_core/db.py` uses `Base.metadata.create_all(...)` as the
  default local bootstrap path.
- `apps/api/alembic` exists for migration-driven schema evolution.

Given the product's local-first operating model, we need explicit policy on when
`create_all` is acceptable versus when Alembic is mandatory, and how rollouts
must preserve compatibility for existing local operators.

## Decision

### 1) When `Base.metadata.create_all` is acceptable

`Base.metadata.create_all` is acceptable only for **bootstrap-safe, additive
initialization** where all of the following are true:

1. The change can be applied safely on a fresh database without mutating
   existing tables in-place.
2. Existing operator data is not at risk if the code runs before any migration
   step.
3. The behavior can tolerate mixed states during local development (for example,
   optional metadata fields with service-layer defaults).
4. No existing relational contract is tightened (no new non-null requirement,
   no dropped/renamed column, no altered foreign key semantics, no destructive
   unique/index changes).

In short: `create_all` is for **initial creation and harmless additive
bootstrapping**, not for durable schema evolution of already-populated local
installations.

### 2) When Alembic migration is mandatory

An Alembic migration under `apps/api/alembic` is mandatory for any **durable
model change** that affects existing persisted data or relational behavior.

#### Explicit trigger criteria (mandatory migration)

A migration is required when any of the following occurs:

1. **Table lifecycle changes**
   - adding a new durable table that must exist consistently across upgrades
   - renaming or dropping a table
2. **Column contract changes**
   - adding a non-null column without a universally safe runtime default
   - changing type, nullability, default, precision, or semantic meaning of an
     existing column
   - renaming or dropping a column
3. **Constraint/index changes**
   - adding/removing/changing unique constraints
   - adding/removing/changing foreign keys or cascade behavior
   - adding/removing indexes needed for correctness (not only performance)
4. **State machine and workflow durability changes**
   - changes that alter persisted workflow validity, completion-readiness
     semantics, or write-time validation invariants
5. **Data backfill or transformation requirements**
   - any release that requires rewriting existing rows to preserve behavior
6. **Cross-surface contract preservation**
   - when API/MCP/service-layer parity depends on schema changes being applied in
     a deterministic order

If any trigger matches, migration is not optional.

### 3) Rollout policy for local-first compatibility

For durable schema evolution, use an **expand → migrate/backfill → contract**
rollout:

1. **Expand (backward compatible)**
   - introduce additive schema elements first (typically nullable/new tables)
   - keep old and new code paths readable during transition
2. **Migrate/backfill (deterministic)**
   - run Alembic migration(s) and required data backfill
   - make backfill idempotent where practical
3. **Contract (after compatibility window)**
   - enforce stricter constraints only after the fleet can run upgraded code
   - remove legacy fields/paths in a later deliberate step

### 4) Guardrails for implementation parity

- Place behavioral logic in shared services first; REST and MCP surfaces should
  consume the same service-layer rules.
- Do not rely on UI-only assumptions to bridge schema transitions.
- Log schema and migration operations with structured diagnostics to keep local
  recovery explicit.

## Consequences

- We keep fast local bootstrap via `create_all` for safe additive setup.
- We require Alembic for changes that affect durable relational correctness.
- We reduce upgrade risk for local operators by requiring staged, explicit
  rollout plans.
- Future schema-affecting work must classify itself against the trigger criteria
  during design and PR review.

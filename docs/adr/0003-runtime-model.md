# ADR 0003: tmux Plus Worktree Runtime Model

## Status

Accepted

## Decision

Use tmux as the session runtime and git worktrees as the workspace isolation
strategy. Persist structured session/worktree metadata in SQLite and treat
terminal output as supplementary evidence rather than the source of truth.

## Why

- durable local runtime
- offline-friendly execution
- easy operator visibility and restart continuity
- supports multiple concurrent sessions without inventing a custom scheduler

## Consequences

- runtime reconciliation is a first-class startup concern
- diagnostics must expose tmux drift and stale worktree signals
- session APIs must return both structured metadata and tail/timeline views

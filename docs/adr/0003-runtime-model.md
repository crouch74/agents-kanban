# ADR 0003: tmux + Worktree Runtime Model

## Status

Accepted

## Decision

Use tmux as the session runtime and git worktrees as the workspace isolation
strategy. Persist structured runtime metadata in SQLite and treat terminal output
as supplementary evidence rather than the source of truth.

## Why

- durable local runtime
- offline-friendly
- easy recovery and operator visibility
- supports many concurrent sessions without inventing a scheduler

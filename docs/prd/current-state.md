# Current Implementation State

## Summary

The application is now a shared task-tracking system for operators and external agents.

It is no longer an agent runtime control plane.

## Implemented Areas

- Projects with one default board each
- Canonical board columns and workflow transitions
- Task CRUD and status transitions
- Task comments with actor/source metadata
- Lightweight events timeline for auditability
- Search over tasks/events
- MCP tool/resource surface for task-board operations
- Web UI focused on projects, board, task detail, comments, search, activity

## Explicitly Removed

- tmux runtime orchestration and reconciliation
- session spawning/follow-up/tail/cancel APIs
- waiting question inbox model and APIs
- repositories/worktrees as active product concerns
- bootstrap flows that launch coding agents
- runtime diagnostics and orphan cleanup flows

## Operational Truths

- Backend + database own workflow state.
- API and MCP behavior are aligned via shared services.
- Board/task/comment state is the core product surface.
- Agent execution happens outside this application.

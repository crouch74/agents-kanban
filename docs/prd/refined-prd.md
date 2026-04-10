# Agent Control Plane PRD

## Product Summary

Agent Control Plane is a local-first operational workspace for one technical
operator coordinating multiple AI agents across multiple repositories and
projects. The product combines:

- structured kanban workflow
- task-linked worktree isolation
- tmux-backed local runtime execution
- append-only operational history
- an MCP-native interface for agents
- a human UI optimized for attention, intervention, and recovery

The current system of record is the backend domain model plus SQLite plus the
append-only `events` table. The React UI and MCP server are clients of the same
shared services.

## Product Positioning

This app is intentionally:

- a control plane first
- a kanban board second
- a terminal viewer third

The board helps the operator steer work, but the board is not the source of
truth. Raw terminal output is visible, but it is not trusted as the canonical
representation of system state.

## Primary Actors

### Human operator

One technical operator who needs:

- global visibility across projects, tasks, sessions, and worktrees
- fast intervention when an agent is blocked
- clean local execution and offline behavior
- crash continuity without reconstructing context manually

### Agent actors

Agents are treated as first-class actors and currently operate through:

- typed MCP tools
- structured MCP resources
- deterministic task, session, worktree, and search contracts

The design goal is that agents should not need to scrape the UI or infer state
from free-form text when a structured contract is available.

## Product Principles

- Local-first and offline after installation
- Shared domain services for REST and MCP behavior
- Canonical workflow state in the backend
- Blocked and waiting modeled as overlays rather than board columns
- Durable audit events for every material write
- Explicit worktree and session records instead of hidden shell state
- Recovery and diagnostics treated as product features, not dev-only concerns

## Standard Kanban Model Adopted

The current implementation follows a standard five-column pull flow:

- `Backlog`
- `Ready`
- `In Progress`
- `Review`
- `Done`

Key rules:

- WIP limits live on columns
- work is pulled into active columns rather than automatically pushed
- blocked and waiting items remain in their current workflow column
- done requires explicit evidence and no unresolved blockers

## Current In-Scope Behavior

Implemented today:

- project creation with one default board per project
- repository registration for local git repositories
- tasks and one level of subtasks
- task dependencies, comments, checks, artifacts
- worktree allocation, archive, lock, and prune lifecycle
- tmux-backed sessions with spawn, follow-up, cancel, tail, and timeline
- waiting questions and human replies
- dashboard, diagnostics, global search, and event feed
- startup reconciliation of runtime state
- stale worktree hygiene recommendations
- MCP tool and resource surface over the same domain services

Partially implemented or intentionally limited today:

- board customization is still minimal
- the web shell is functional but concentrated in a large `App.tsx`
- export/import exists only as future intent
- deeper multi-step orchestration is still operator-driven
- SQLite schema evolution is still conservative and compatibility-aware

## Core Operator Workflows

- Create a project and get a default board immediately.
- Register one or more local repositories under a project.
- Create tasks and subtasks manually.
- Allocate a worktree for a task.
- Spawn an executor session in tmux.
- Inspect session tail, timeline, linked events, and waiting state.
- Spawn follow-up reviewer/verifier/retry sessions from an existing session.
- Answer waiting questions from the inbox or task/session context.
- Move tasks through canonical workflow states with evidence gating.
- Use diagnostics to discover runtime drift and stale worktrees.

## Core Agent Workflows

- Discover projects, boards, tasks, and context through MCP.
- Create tasks or subtasks.
- Add comments, checks, artifacts, and dependencies.
- Spawn or inspect sessions and worktrees.
- Open waiting questions and read answers.
- Read task completion readiness before marking work done.
- Search context and inspect diagnostics/hygiene state.

## Constraints and Tradeoffs

- Single-user local environment only in the current design.
- Only one subtask nesting level is supported in v1.
- SQLite remains the local default and is not being replaced with a server DB.
- tmux is the runtime backbone; we persist metadata around it rather than
  abstracting it away.
- Session lineage is currently modeled via structured metadata to preserve local
  DB compatibility while the repository still relies on `create_all`.

## Success Criteria for the Current Build

The app already clears these bars:

- the operator can manage work across projects inside one local UI
- agents can interact through MCP instead of UI scraping
- worktree ownership and session runtime are visible in structured state
- waiting questions and replies are durable and queryable
- restart and diagnostics flows preserve operational understanding

The next bar is hardening:

- stronger backup/export/import story
- better component decomposition
- more comprehensive end-to-end coverage
- safer long-term schema migration discipline

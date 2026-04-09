# Agent Control Plane PRD

## Product Summary

Agent Control Plane is a local-first operational workspace for managing AI
agents across projects, repositories, tasks, worktrees, and sessions. The
product serves one technical operator and treats both humans and agents as
first-class actors.

The system of record is the backend plus SQLite database plus append-only event
history. The UI visualizes and steers that state; agents interact through MCP
contracts rather than UI scraping.

## Goals

- Make multi-agent work observable at a glance.
- Make work steerable and resumable without digging through raw terminals.
- Keep agent workflows structured, deterministic, and auditable.
- Preserve local-first and offline operation after installation.
- Keep the codebase maintainable for future coding agents.

## Key Product Principles

- Control plane first, kanban board second, terminal viewer third.
- Canonical backend workflow state with customizable column mapping.
- Blocked and waiting are overlays, not alternate workflow stages.
- Every material write operation emits a durable audit event.
- Worktrees are explicit first-class records, not hidden git side effects.
- Session runtime state is persisted separately from raw terminal output.

## Standard Kanban Guidance Adopted in v1

- Default columns: `Backlog`, `Ready`, `In Progress`, `Review`, `Done`
- WIP limits belong to columns, not ad-hoc operator memory.
- Column policies are explicit and visible.
- Work is pulled into active states rather than pushed automatically.
- Blocked and waiting items remain visible in their workflow stage.
- Done requires evidence through checks and/or acceptance criteria.

## Human Workflows

- Create projects, attach repositories, and operate from one board per project.
- Create tasks and subtasks manually or via planning agents.
- Spawn agent sessions with linked worktree and runtime metadata.
- Review comments, checks, questions, artifacts, and event history.
- Respond quickly to waiting questions from an inbox.
- Inspect all running and blocked work from a global dashboard.
- Recover context after a restart without reconstructing history from scratch.

## Agent Workflows

- Discover next task through predictable read tools.
- Claim and update work through structured MCP calls.
- Create subtasks without relying on natural-language parsing.
- Request a worktree, emit progress, and attach checks and artifacts.
- Open a waiting question when blocked and resume after a reply.

## Scope

### In scope

- projects, repositories, boards, columns
- tasks, subtasks, dependencies
- comments, checks, artifacts
- agent sessions and session runs
- waiting questions and human replies
- git worktree lifecycle
- MCP server with structured tools/resources
- diagnostics, search, dashboard, and crash continuity basics

### Out of scope

- multi-user collaboration
- cloud sync
- internet-required features
- enterprise auth
- deployment pipelines and automatic merging
- distributed execution across multiple machines

## Success Criteria

- Operator can create a project and attached repo, then work entirely inside the
  app for task/session visibility.
- Agents can claim, update, and complete work through MCP tools without scraping
  the UI.
- Waiting questions and replies are durable, queryable, and resumable.
- Restarting the app preserves operator understanding of current and recent work.


# Domain Model

## Source of Truth Model

The system deliberately separates:

- current-state tables used for fast reads and operational queries
- append-only event history used for auditability and recovery context

The `events` table is not a full event-sourced replay engine, but every
material write is expected to emit an event so operators and future agents can
understand how a state was reached.

## Core Aggregates

### Project

- owns one board
- groups repositories, tasks, sessions, questions, worktrees, and events
- carries human-facing project metadata

### Repository

- belongs to one project
- stores local filesystem path and git metadata
- acts as the owning root for worktrees

### Board

- belongs to one project
- stores ordered columns and column policies
- does not own the workflow truth independently from task state

### Task

- belongs to one project
- maps to one canonical workflow state and one board column
- may have one `parent_task_id` in v1
- owns comments, checks, artifacts, dependencies, waiting questions, sessions,
  and optionally worktrees
- stores overlays for `blocked_reason` and `waiting_for_human`

### Task Dependency

- directed edge from a task to another task
- currently supports `blocks` and `relates_to`
- influences completion readiness for the dependent task

### Task Evidence

The evidence model is split into three immutable record types:

- comments for narrative progress/history
- checks for structured validation state
- artifacts for filesystem, git, document, or output references

### Agent Session

- belongs to one task and one project
- may link to a repository and worktree
- stores status, profile, tmux session name, and runtime metadata
- owns session messages and runs
- may participate in a session family through `runtime_metadata`

### Agent Run

- attempt record under one session
- captures launch summary and runtime metadata snapshot
- currently used for timeline display and attempt visibility

### Waiting Question

- belongs to one task and optionally one session
- represents a durable human-in-the-loop interruption
- stores prompt, blocked reason, urgency, and optional answer choices

### Human Reply

- belongs to one waiting question
- stores responder name, reply body, and structured payload

### Worktree

- belongs to one repository
- may link to a task and optionally the most relevant active session
- stores branch name, filesystem path, lifecycle state, and metadata
- remains visible even after active execution ends

### Event

- immutable audit record
- stores actor identity, entity type/id, event type, correlation id, and payload
- used in dashboard activity, session timelines, MCP resources, and diagnostics

## Relationship Notes

- tasks remain the primary unit of operator intent
- sessions are execution or review activity around a task
- worktrees are isolation resources owned by task/repository context, not by an
  agent brand
- waiting questions connect task state and session state without making either
  one depend solely on terminal output
- session families are currently modeled in session runtime metadata to avoid
  forced schema churn while preserving follow-up lineage

## Important Practical Limits

- subtasks are one level deep only
- one project currently maps to one board
- session lineage is additive metadata, not a separate relational table
- completion readiness is computed from checks, artifacts, dependencies, and
  open questions rather than a stored boolean

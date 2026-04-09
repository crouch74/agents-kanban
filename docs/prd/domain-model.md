# Domain Model

## Core Aggregates

### Project

- owns one board
- links one or more repositories
- contains tasks, sessions, questions, worktrees, and events

### Repository

- belongs to one project
- stores local path, git metadata, and health snapshot
- owns worktree records

### Board

- belongs to one project
- stores ordered columns and column policies

### Task

- belongs to one project and board
- may have one parent task in v1
- links to dependencies, comments, checks, artifacts, sessions, and worktrees
- stores canonical workflow state and overlays for blocked/waiting

### Agent Session

- belongs to one project and one task
- links to repository and worktree when applicable
- contains one or more runs and many session messages

### Waiting Question

- belongs to one task and optionally one session
- stores structured question details and human reply state

### Worktree

- belongs to one repository
- linked to task and optionally active session
- persists lifecycle independently of raw git output

### Event

- immutable audit record emitted for material state transitions

## Relationship Notes

- tasks remain the primary unit of operator intent
- sessions are execution attempts or collaborators around tasks
- worktrees are isolation resources owned by tasks, not by agent brands
- event log complements current-state tables rather than replacing them


# State Machines

## Task Workflow

Canonical workflow states:

- `backlog`
- `ready`
- `in_progress`
- `review`
- `done`
- `cancelled`

Current allowed transitions:

- `backlog -> ready`
- `ready -> backlog`
- `ready -> in_progress`
- `in_progress -> ready`
- `in_progress -> review`
- `review -> in_progress`
- `review -> done`
- `done -> review`
- `backlog|ready|in_progress|review|done -> cancelled`

Important rules:

- board column changes also normalize workflow state via
  `WORKFLOW_BY_COLUMN_KEY`
- blocked and waiting remain overlays, not workflow states
- moving into `done` requires completion readiness to pass

### Task overlays

- `blocked_reason != null` means the task is operationally blocked
- `waiting_for_human = true` means the task is waiting on operator input

Those overlays can coexist with `ready`, `in_progress`, or `review`.

## Session Workflow

Current session statuses in the implementation:

- `queued`
- `running`
- `waiting_human`
- `blocked`
- `done`
- `failed`
- `cancelled`

Observed transitions:

- `queued -> running`
- `running -> waiting_human`
- `running -> blocked`
- `running -> done`
- `running -> failed`
- `running -> cancelled`
- `waiting_human -> running`
- `blocked -> running`

Practical reconciliation behavior:

- startup reconciliation maps tracked sessions back to `running`,
  `waiting_human`, or `done` based on tmux presence
- terminal status alone is not trusted; persisted state is refreshed through the
  service layer

## Waiting Question Workflow

- `open -> answered`
- `answered -> closed`
- `open -> dismissed`

Important coupling:

- opening a question marks the task `waiting_for_human`
- if linked to a running session, that session moves to `waiting_human`
- answering a question can resume the linked session if its runtime still
  exists

## Worktree Workflow

- `requested -> provisioning`
- `provisioning -> active`
- `provisioning -> error`
- `active -> locked`
- `active -> archived`
- `active -> error`
- `locked -> archived`
- `archived -> pruned`
- `archived -> error`

Practical hygiene behavior:

- a worktree linked to a finished or cancelled session is usually recommended
  for `archive`
- an already archived worktree with stale reasons is usually recommended for
  `prune`
- a missing path is recommended for `inspect`

## Completion Readiness Gate

Before a task may enter `done`, the current implementation requires:

- at least one passing or warning check, or at least one artifact
- no unresolved blocking dependencies
- no open waiting questions

This gate is enforced in the service layer and should not be bypassed from API,
MCP, or UI code.

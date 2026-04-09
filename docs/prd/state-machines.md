# State Machines

## Task Workflow

Canonical workflow states:

- `backlog`
- `ready`
- `in_progress`
- `review`
- `done`
- `cancelled`

Overlays:

- `blocked`
- `waiting_human`

Allowed workflow transitions:

- `backlog -> ready`
- `ready -> in_progress`
- `in_progress -> review`
- `review -> done`
- `review -> in_progress`
- `ready -> backlog`
- `in_progress -> ready`
- `done -> review`
- `* -> cancelled`

## Session Workflow

- `queued -> running`
- `running -> waiting_human`
- `running -> blocked`
- `running -> done`
- `running -> failed`
- `running -> cancelled`
- `waiting_human -> running`
- `blocked -> running`

## Waiting Question Workflow

- `open -> answered`
- `answered -> closed`
- `open -> dismissed`

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


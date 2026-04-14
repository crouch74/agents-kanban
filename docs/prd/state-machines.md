# State Machines

## Task Workflow

Canonical states:

- `backlog`
- `ready`
- `in_progress`
- `review`
- `done`
- `cancelled`

Allowed transitions:

- `backlog -> ready`
- `ready -> backlog`
- `ready -> in_progress`
- `in_progress -> ready`
- `in_progress -> review`
- `review -> in_progress`
- `review -> done`
- `done -> review`
- `backlog|ready|in_progress|review|done -> cancelled`
- `cancelled -> backlog`

Board-column moves normalize `workflow_state` through column mapping.

## Comments

Task comments are append-only records with:

- `author_type`
- `author_name`
- optional `source`
- `body`
- `created_at`

Comments are used for both operator notes and agent progress updates.

## Events

Material writes emit lightweight events with:

- actor metadata
- entity metadata
- event type
- payload
- timestamp

Events provide a compact audit timeline.

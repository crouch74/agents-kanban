# API Outline

Base path: `/api/v1`

## Diagnostics

- `GET /health`
- `GET /diagnostics`

## Projects

- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`

## Boards

- `GET /boards/{board_id}`
- `GET /projects/{project_id}/board`

## Tasks

- `GET /tasks`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `PATCH /tasks/{task_id}`
- `POST /tasks/{task_id}/subtasks`
- `GET /tasks/{task_id}/dependencies`
- `POST /tasks/{task_id}/comments`
- `POST /tasks/{task_id}/checks`

## Sessions

- `GET /sessions`
- `POST /sessions`
- `GET /sessions/{session_id}`

## Questions

- `GET /questions`
- `POST /questions`
- `GET /questions/{question_id}`
- `POST /questions/{question_id}/replies`

## Worktrees

- `GET /worktrees`
- `POST /worktrees`
- `GET /worktrees/{worktree_id}`

## Search and Events

- `GET /search`
- `GET /events`


# API Outline

Base path: `/api/v1`

The REST API is implemented in FastAPI and is the operator-facing transport over
the shared domain services in `packages/core`.

## Diagnostics and Dashboard

- `GET /health`
- `GET /diagnostics`
- `GET /dashboard`

## Projects and Boards

- `GET /projects`
- `POST /projects`
- `POST /projects/bootstrap`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/board`

`GET /projects/{project_id}` currently returns a composite project overview with:

- project summary
- board view
- repositories
- worktrees
- sessions
- open waiting questions

`POST /projects/bootstrap` creates the project, prepares the repository,
creates a kickoff planning task, and starts the kickoff session. Default
execution stays on the repository's current branch; kickoff worktrees are
optional.

## Tasks

- `GET /tasks`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `GET /tasks/{task_id}/detail`
- `PATCH /tasks/{task_id}`
- `POST /tasks/{task_id}/comments`
- `POST /tasks/{task_id}/checks`
- `POST /tasks/{task_id}/artifacts`
- `GET /tasks/{task_id}/dependencies`
- `POST /tasks/{task_id}/dependencies`

Notes:

- subtasks are created through `POST /tasks` using `parent_task_id`
- patching a task can update title, description, workflow/column, blocked
  reason, and waiting flag

## Repositories and Worktrees

- `GET /repositories`
- `POST /repositories`
- `GET /repositories/{repository_id}`
- `GET /worktrees`
- `POST /worktrees`
- `GET /worktrees/{worktree_id}`
- `PATCH /worktrees/{worktree_id}`

## Sessions

- `GET /sessions`
- `POST /sessions`
- `POST /sessions/{session_id}/follow-up`
- `GET /sessions/{session_id}`
- `GET /sessions/{session_id}/tail`
- `GET /sessions/{session_id}/timeline`
- `POST /sessions/{session_id}/cancel`

Notes:

- `follow-up` is used for retries, reviewer sessions, verifier sessions, and
  handoff-style continuation
- timeline responses include runs, messages, waiting questions, events, and
  related sessions in the same session family

## Waiting Questions

- `GET /questions`
- `POST /questions`
- `GET /questions/{question_id}`
- `POST /questions/{question_id}/replies`

## Search and Events

- `GET /search`
- `GET /events`

## Live Updates

- WebSocket `/api/v1/ws`
- AsyncAPI contract: `docs/api/asyncapi-ws-v1.yaml`

The WebSocket surface is used to broadcast committed mutation events so the web
client can invalidate stale query results.

## OpenAPI Snapshot Contract

- Canonical OpenAPI artifact: `docs/api/openapi-v1.json`
- Regeneration command: `.venv/bin/python scripts/generate_openapi.py`
- Drift check command: `.venv/bin/python scripts/generate_openapi.py --check`

Any REST route, request/response model, or FastAPI metadata change must include
an updated `docs/api/openapi-v1.json` in the same PR so repository docs and
automation stay in sync with the implemented API surface.

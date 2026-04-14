# API Outline

Base path: `/api/v1`

## Health and Dashboard

- `GET /health`
- `GET /dashboard`

## Projects and Boards

- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/archive`
- `GET /projects/{project_id}/board`

## Tasks

- `GET /tasks`
  - filters: `project_id`, `status`, `q`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `GET /tasks/{task_id}/detail`
- `PATCH /tasks/{task_id}`
- `GET /tasks/{task_id}/comments`
- `POST /tasks/{task_id}/comments`

## Search and Events

- `GET /search`
  - filters: `q`, `project_id`, `status`, `limit`
- `GET /events`
  - filters: `project_id`, `task_id`, `limit`

## Live Updates

- WebSocket: `/api/v1/ws`
- Emits `mutation.committed` after durable writes.

## Removed API Domains

The following domains were deliberately removed from the product boundary:

- sessions
- waiting questions
- repositories
- worktrees
- bootstrap execution
- runtime diagnostics/reconciliation

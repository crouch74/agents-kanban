---
name: agent-control-plane-api
description: Use this skill when working with Agent Control Plane tasks, sessions, questions, worktrees, diagnostics, or bootstrap flows through the REST API instead of MCP.
metadata:
  short-description: ACP REST API usage
---

# Agent Control Plane API

Use the REST API as the source of truth for ACP operations.

## Workflow

1. Read `.acp/project.local.json`.
2. Resolve `api_base_url` from that file.
3. If `api_base_url` is missing, derive it from the active ACP runtime or environment instead of hardcoding host or port.
4. Fetch `${api_base_url}/openapi.json` and use it to confirm request/response shapes before writing.
5. Use `/api/v1` endpoints for ACP actions.

## Core Endpoints

- Projects and boards: `GET /projects`, `POST /projects`, `POST /projects/bootstrap`, `GET /projects/{project_id}`, `GET /projects/{project_id}/board`
- Tasks: `GET /tasks`, `POST /tasks`, `GET /tasks/{task_id}`, `PATCH /tasks/{task_id}`, `POST /tasks/{task_id}/comments`, `POST /tasks/{task_id}/checks`, `POST /tasks/{task_id}/artifacts`, `GET /tasks/{task_id}/dependencies`, `POST /tasks/{task_id}/dependencies`
- Sessions: `GET /sessions`, `POST /sessions`, `GET /sessions/{session_id}`, `GET /sessions/{session_id}/tail`, `GET /sessions/{session_id}/timeline`, `POST /sessions/{session_id}/follow-up`, `POST /sessions/{session_id}/cancel`
- Questions: `GET /questions`, `POST /questions`, `GET /questions/{question_id}`, `POST /questions/{question_id}/replies`
- Worktrees and diagnostics: `GET /worktrees`, `POST /worktrees`, `GET /worktrees/{worktree_id}`, `PATCH /worktrees/{worktree_id}`, `GET /diagnostics`, `GET /search`, `GET /events`

## Rules

- Never hardcode `127.0.0.1:8000` or any other fixed port when the active ACP runtime can tell you the API base URL.
- Prefer the live OpenAPI document over memory when request fields or response shapes matter.
- Keep writes aligned with the canonical workflow and completion-readiness rules enforced by the API.
- Use the API for ACP state; do not rely on MCP tools for kickoff or routine control-plane updates.

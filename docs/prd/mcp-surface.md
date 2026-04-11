# MCP Surface

The MCP server is a real product surface, not a future stub. It is implemented
in `packages/mcp-server` and delegates to the same shared domain services as the
REST API.

## Tool Design Rules

- predictable names
- structured inputs and outputs
- cheap reads
- clear side effects on writes
- idempotent write options through `client_request_id`
- audit event emission for every material write

## Implemented Tools

### Project and board context

- `project_list`
- `project_get`
- `project_create`
- `project_bootstrap`
- `board_get`

### Task lifecycle

- `task_get`
- `task_create`
- `subtask_create`
- `task_update`
- `task_claim`
- `task_next`
- `task_dependencies_get`
- `task_dependency_add`
- `task_comment_add`
- `task_check_add`
- `task_artifact_add`
- `task_completion_readiness`

### Session lifecycle

- `session_spawn`
- `session_status`
- `session_follow_up`
- `session_tail`
- `session_list`

### Waiting/human loop

- `question_open`
- `question_answer_get`

### Worktree and diagnostics

- `worktree_create`
- `worktree_list`
- `worktree_get`
- `worktree_hygiene_list`
- `diagnostics_get`

### Search

- `context_search`

## Implemented Resources

- `control-plane://projects/{project_id}/board`
- `control-plane://tasks/{task_id}`
- `control-plane://tasks/{task_id}/completion`
- `control-plane://sessions/{session_id}/timeline`
- `control-plane://questions/{question_id}`
- `control-plane://projects/{project_id}/repos`
- `control-plane://diagnostics/local`
- `control-plane://events/project/{project_id}`
- `control-plane://events/task/{task_id}`

## Current Agent Workflow Shape

A common agent loop today looks like:

1. `task_next` or `project_get`
2. `task_get`
3. `worktree_get` or `worktree_create`
4. `session_spawn`
5. `task_comment_add`, `task_check_add`, `task_artifact_add`
6. `question_open` if blocked
7. `question_answer_get` when resuming
8. `task_completion_readiness`
9. `task_update`

## Important Notes

- MCP writes share the same service-layer rules as the API, including evidence
  gating and transition validation
- follow-up sessions are session-family aware and can be used for verifier or
  reviewer workflows
- diagnostics and worktree hygiene are intentionally exposed to agents so they
  can self-correct before a human intervenes
- `project_bootstrap` can initialize an empty repo, add ACP guidance files, and
  launch the kickoff Codex session in either repo mode or worktree mode

## MCP Error Mapping Guidance

MCP tools should mirror the same domain error semantics as REST, while using a
consistent MCP error envelope for tool-call failures.

Recommended tool error payload:

```json
{
  "ok": false,
  "error": {
    "code": "transition_blocked",
    "message": "Cannot transition task from 'in_progress' to 'done'.",
    "details": {
      "task_id": "task_123",
      "from": "in_progress",
      "to": "done"
    },
    "http_status": 409,
    "retryable": false
  }
}
```

### Mapping from API semantics

| API status/code family | MCP `error.code` | `retryable` |
| --- | --- | --- |
| `422 validation_error` | `validation_error` | `false` |
| `404 *_not_found` | resource-specific code (for example `task_not_found`) | `false` |
| `409 transition_blocked` / `invalid_transition` | same code from service layer | `false` |
| `502 runtime_adapter_failure` | `runtime_adapter_failure` | `true` |
| `503 runtime_unavailable` | `runtime_unavailable` | `true` |
| `504 runtime_timeout` | `runtime_timeout` | `true` |
| `500 internal_error` | `internal_error` | generally `false` unless handler marks transient |

### Common MCP failure examples

Validation failure:

```json
{
  "ok": false,
  "error": {
    "code": "validation_error",
    "message": "Field 'title' must not be empty.",
    "details": {
      "field": "title"
    },
    "http_status": 422,
    "retryable": false
  }
}
```

Not found:

```json
{
  "ok": false,
  "error": {
    "code": "task_not_found",
    "message": "Task 'task_999' was not found.",
    "details": {
      "task_id": "task_999"
    },
    "http_status": 404,
    "retryable": false
  }
}
```

Transition blocked:

```json
{
  "ok": false,
  "error": {
    "code": "transition_blocked",
    "message": "Task is not ready for done.",
    "details": {
      "missing": ["artifacts", "checks"]
    },
    "http_status": 409,
    "retryable": false
  }
}
```

Runtime adapter unavailable:

```json
{
  "ok": false,
  "error": {
    "code": "runtime_unavailable",
    "message": "tmux server unavailable for session_spawn.",
    "details": {
      "adapter": "tmux",
      "operation": "session_spawn"
    },
    "http_status": 503,
    "retryable": true
  }
}
```

### MCP implementation guidance

- Keep tool-level `error.code` values aligned with shared service exceptions.
- Preserve structured `details` so agents can perform deterministic repair.
- Set `retryable` only for transient runtime/infrastructure conditions.
- If a tool wraps an internal REST call, propagate canonical codes instead of
  inventing transport-specific variants.


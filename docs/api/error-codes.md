# API Error Codes

This document defines the canonical HTTP and error-shape behavior for the ACP
REST API.

The API is backed by shared service-layer logic in `packages/core`, so these
mappings apply consistently across handlers.

## Error response shape

Unless otherwise noted, error responses should use a structured JSON payload:

```json
{
  "error": {
    "code": "transition_blocked",
    "message": "Task cannot move to done because completion readiness failed.",
    "details": {
      "task_id": "task_123",
      "missing": ["acceptance_checks", "artifacts"]
    }
  }
}
```

Guidance:

- `error.code`: stable machine-readable identifier.
- `error.message`: operator-readable summary.
- `error.details`: optional structured context for UI and agent repair flows.

## HTTP status mapping

| HTTP status | When to use | Typical `error.code` |
| --- | --- | --- |
| `400 Bad Request` | Request is syntactically valid JSON but semantically invalid for endpoint contract (missing required relationship, malformed transition payload, unknown enum in permissive parser paths). | `bad_request`, `invalid_argument` |
| `401 Unauthorized` | Missing/invalid auth credentials (when auth is enabled). | `unauthorized` |
| `403 Forbidden` | Caller is authenticated but not allowed to perform operation. | `forbidden` |
| `404 Not Found` | Target project/task/session/question/worktree does not exist in canonical state. | `*_not_found` |
| `409 Conflict` | State conflict: illegal transition, duplicate dependency edge, idempotency conflict, or operation blocked by current state. | `transition_blocked`, `already_exists`, `state_conflict` |
| `422 Unprocessable Entity` | Schema/domain validation failed after parsing succeeded (field constraints, invariants, completion gate checks exposed as validation-style failures). | `validation_error`, `completion_readiness_failed` |
| `500 Internal Server Error` | Unhandled internal errors. | `internal_error` |
| `502 Bad Gateway` | Runtime adapter/tooling dependency failed while API remained healthy (tmux/git process bridge errors surfaced through adapter layer). | `runtime_adapter_failure` |
| `503 Service Unavailable` | Runtime subsystem temporarily unavailable (tmux server down, adapter startup race, transient local infra outage). | `runtime_unavailable` |
| `504 Gateway Timeout` | Runtime adapter operation timed out waiting on subprocess/session activity. | `runtime_timeout` |

## Validation errors (`422`)

Validation errors should include field-level details when available.

Example:

```http
HTTP/1.1 422 Unprocessable Entity
```

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": {
      "fields": [
        {
          "field": "title",
          "issue": "must not be empty"
        },
        {
          "field": "priority",
          "issue": "must be one of: low, medium, high"
        }
      ]
    }
  }
}
```

## Not-found behavior (`404`)

Not-found responses should be explicit and resource-specific.

Example (task lookup):

```http
HTTP/1.1 404 Not Found
```

```json
{
  "error": {
    "code": "task_not_found",
    "message": "Task 'task_999' was not found.",
    "details": {
      "task_id": "task_999"
    }
  }
}
```

Guidance:

- Return `404` for absent resources, not `200` with null payloads.
- Avoid leaking internal storage details; include only safe identifiers.

## Transition errors (`409`)

When a workflow transition is disallowed by canonical state-machine rules,
return `409 Conflict` with actionable details.

Example (blocked move to `done`):

```http
HTTP/1.1 409 Conflict
```

```json
{
  "error": {
    "code": "transition_blocked",
    "message": "Cannot transition task from 'in_progress' to 'done'.",
    "details": {
      "task_id": "task_123",
      "from": "in_progress",
      "to": "done",
      "reasons": [
        "completion_readiness_failed",
        "missing_artifacts"
      ]
    }
  }
}
```

Common transition-related codes:

- `transition_blocked`
- `invalid_transition`
- `completion_readiness_failed`
- `dependency_incomplete`

## Runtime adapter failures (`5xx`)

Errors from tmux/git/session runtime operations should be mapped to runtime
error codes rather than collapsed into generic `500` whenever classification is
possible.

Example (tmux server unavailable):

```http
HTTP/1.1 503 Service Unavailable
```

```json
{
  "error": {
    "code": "runtime_unavailable",
    "message": "Runtime adapter could not connect to tmux.",
    "details": {
      "adapter": "tmux",
      "operation": "session_spawn"
    }
  }
}
```

Example (runtime operation timeout):

```http
HTTP/1.1 504 Gateway Timeout
```

```json
{
  "error": {
    "code": "runtime_timeout",
    "message": "Timed out waiting for session output.",
    "details": {
      "operation": "session_tail",
      "timeout_seconds": 30
    }
  }
}
```

## Implementation notes

- Prefer raising typed domain/service exceptions and mapping them centrally in
  API error middleware.
- Keep error-code naming stable once published; clients can key retries and
  repair logic on them.
- Include `client_request_id` (when present) in logs and optionally
  `error.details` to support idempotent retry diagnostics.

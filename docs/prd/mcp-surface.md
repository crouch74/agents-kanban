# MCP Surface

The MCP server is task-board scoped.

## Tools

- `project_list`
- `project_get`
- `project_create`
- `board_get`
- `task_list`
- `task_get`
- `task_create`
- `task_update`
- `task_comment_add`
- `context_search`
- `dashboard_get`

## Resources

- `taskboard://projects/{project_id}/board`
- `taskboard://tasks/{task_id}`
- `taskboard://events/project/{project_id}`
- `taskboard://events/task/{task_id}`

## Contract Notes

- MCP is a coordination interface, not a runtime launcher.
- Agent progress is represented as task updates/comments.
- `client_request_id` remains supported for idempotent writes.

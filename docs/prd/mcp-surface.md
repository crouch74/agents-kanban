# MCP Surface

## Tools

- `project_list`
- `project_get`
- `board_get`
- `task_get`
- `task_create`
- `subtask_create`
- `task_update`
- `task_claim`
- `task_comment_add`
- `task_check_add`
- `task_next`
- `task_dependencies_get`
- `session_spawn`
- `session_status`
- `session_tail`
- `session_list`
- `question_open`
- `question_answer_get`
- `worktree_create`
- `worktree_list`
- `worktree_get`
- `context_search`

## Resources

- `control-plane://projects/{id}/board`
- `control-plane://tasks/{id}`
- `control-plane://sessions/{id}/timeline`
- `control-plane://questions/{id}`
- `control-plane://projects/{id}/repos`
- `control-plane://events?project_id={id}`

## Tool Contract Rules

- predictable names
- strongly typed input and output
- clear side effects on writes
- cheap reads
- idempotent write options through `client_request_id`
- audit event emission for every write


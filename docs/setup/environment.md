# Environment Configuration

Agent Control Plane loads environment variables through `packages/core/src/acp_core/settings.py` with an `ACP_` prefix.

- Copy `.env.example` to `.env` for local development.
- Values shown below are the current code defaults.
- If a variable is omitted, ACP falls back to the default from `Settings`.
- For domain vocabulary used throughout onboarding and module guides, see the [shared glossary](../glossary.md).

## Variables

| Variable | Type | Default | Description | Local usage | CI usage |
| --- | --- | --- | --- | --- | --- |
| `ACP_APP_ENV` | `str` | `development` | Environment label used for runtime mode and logging context. | Keep `development`. | Set to `test` when you want explicit test context (optional; current CI works with defaults). |
| `ACP_APP_NAME` | `str` | `Agent Control Plane` | Human-readable app name used by backend metadata and logs. | Usually unchanged. | Usually unchanged. |
| `ACP_API_HOST` | `str` | `127.0.0.1` | Bind host for API server and source for derived API base URL. | Keep loopback (`127.0.0.1`) unless you need LAN access. | Keep loopback in runners. |
| `ACP_API_PORT` | `int` | `8000` | API listen port and source for derived API base URL. | Change if `8000` is busy. | Usually unchanged. |
| `ACP_WEB_ORIGINS` | `list[str]` | `["http://127.0.0.1:5173", "http://localhost:5173"]` | CORS allow-list for the web app. | Use JSON array syntax; add additional local web origins if needed. | Keep default unless test harness uses a different origin. |
| `ACP_RUNTIME_HOME` | `path` | `.acp` under current working directory | Root runtime folder for DB, logs, and artifacts. | Usually keep `.acp` in repo root for easy cleanup. | CI commonly leaves default; override only when isolating artifacts per step. |
| `ACP_DATABASE_NAME` | `str` | `acp.sqlite3` | SQLite database filename inside `ACP_RUNTIME_HOME`. | Change only if you need multiple side-by-side local databases. | Optional; can be overridden for matrix/isolation scenarios. |
| `ACP_BOOTSTRAP_AGENT_MCP_NAME` | `str` | `agent-control-plane` | MCP server name used by bootstrap agent setup commands. | Usually unchanged. | Usually unchanged. |
| `ACP_BOOTSTRAP_AGENT_COMMAND_TEMPLATE` | `str` | `codex mcp get {mcp_name} >/dev/null 2>&1 || codex mcp add {mcp_name} --env PYTHONPATH={mcp_pythonpath} -- {python_executable} -m acp_mcp_server.server && codex exec --full-auto - < {prompt_file}` | Command template used for bootstrap agent execution. | Keep default unless you intentionally customize Codex bootstrap behavior. | Usually unchanged; only override in specialized CI bootstrap experiments. |

## Local setup flow

1. Copy template values:

   ```bash
   cp .env.example .env
   ```

2. Adjust only what you need (typically `ACP_API_PORT` or `ACP_RUNTIME_HOME`).
3. Start stack via `scripts/dev-stack.sh`.

## CI guidance

The repository CI pipeline in `.github/workflows/ci.yml` does not require custom ACP variables for standard verification (`scripts/bootstrap.sh`, `scripts/verify.sh`). Keep CI simple by relying on defaults unless a job has a concrete isolation or port-conflict reason to override values.

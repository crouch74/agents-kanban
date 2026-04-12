## [Unreleased] 
- Fixed ACP_RUNTIME_HOME environment missing for bootstrap MCP connection.
- Reverted to -a never flag for properly pipelined stdin sandbox mode.
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- 🧭 Stale session status: Sessions that finish their agent turn and return to a shell prompt in tmux are now correctly reconciled from `running` to `done`.
- 🧭 Stale task blockers: Tasks now explicitly clear their `blocked_reason` and `waiting_for_human` flag when the last pending waiting question is answered.

### Added
- 🧭 Session activity detection: Added `is_session_active` to `TmuxRuntimeAdapter` to detect idle shell prompts vs active agent turns.
- 📥 Inbox "Next Actions": The waiting question triage panel now suggests follow-up actions (Go to Board, Inspect Task) after a question is closed.
- 📥 Inbox auto-selection: The next open question in the queue is now automatically selected after answering the current one.

### Fixed
- 🤖 Bootstrap command used interactive `codex` CLI piped via stdin, which errors
  with "stdin is not a terminal" inside a non-interactive tmux session. Switched to
  `codex exec` — the explicit non-interactive subcommand that accepts piped stdin.
- 🤖 Bootstrap command used `codex exec --full-auto`, which still maps to
  `-a on-request` and can leave non-interactive kickoff MCP calls stuck behind
  approval prompts. Switched the default bootstrap command to
  `codex -a never exec -s workspace-write`.
- 🌿 `bootstrap_project` raised a `ValueError` when the repo path did not yet
  exist, even when `initialize_repo=true` was set. Directory is now created
  automatically before git init when the flag is enabled.
- 🌐 CORS `web_origin` (single string) replaced with `web_origins` (list) to
  allow both `http://127.0.0.1:5173` and `http://localhost:5173` during
  development.

### Added
- 🐳 Docker support for local development with `docker-compose.yml`.
- 📦 Dockerfiles for `apps/api` and `apps/web`.
- 🩺 Health checks for the API service in Docker.

### Changed
- 🔥 Backend hot reload now watches both `apps/api` and `packages/core/src`.
- 📡 Frontend Vite server listens on `0.0.0.0` inside Docker for HMR.
- 🧭 Updated `scripts/dev-api.sh` to include `packages/core/src` in uvicorn reload dirs.

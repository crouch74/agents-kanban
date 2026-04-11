# `scripts` Module Guide

## Purpose
`scripts` contains repository automation entrypoints for bootstrap, development stack startup, verification, linting, and screenshot/evidence workflows.

## Key Inputs / Outputs
- **Inputs**
  - Local environment tooling availability (Python, npm, Playwright, tmux, git).
  - Repository checkout state and dependency lockfiles.
  - Optional flags for selective stack startup/verification behavior.
- **Outputs**
  - Installed dependencies and bootstrapped local dev environment.
  - Running dev services (API/web/MCP) with logs under `.acp/logs/dev/`.
  - Verification exit codes and artifacts (coverage XML, Playwright reports/results).

## Dependencies
- Bash
- Python 3.12+ and virtualenv
- Node.js/npm
- Playwright (for UI smoke/e2e)

## Local Run Command(s)
- Bootstrap dependencies:
  - `bash scripts/bootstrap.sh`
- Start full local stack:
  - `bash scripts/dev-stack.sh`
- Helpful variants:
  - `bash scripts/dev-stack.sh --api-only`
  - `bash scripts/dev-stack.sh --web-only`
  - `bash scripts/dev-stack.sh --mcp-only`

## Test Command(s)
- Canonical verification:
  - `bash scripts/verify.sh`
- Focused subsets:
  - `bash scripts/test_integration.sh`
  - `bash scripts/test_ui.sh`
  - `bash scripts/lint_python.sh`

## Known Limitations
- Scripts assume a local Unix-like shell environment and may require adaptation on non-POSIX setups.
- UI verification requires Playwright browser installation and can be slower/flake-prone in constrained CI or remote environments.
- Some scripts depend on runtime tools (`tmux`, `git`) being installed and available in `PATH`.

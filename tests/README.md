# `tests` Module Guide

## Purpose
`tests` contains repository verification coverage across backend integration behavior, frontend browser workflows, and focused unit checks for core service compatibility layers.

## Key Inputs / Outputs
- **Inputs**
  - Running or in-process API/MCP app fixtures.
  - Test fixtures/mocks for runtime and control-plane state.
  - Local dependencies installed via `scripts/bootstrap.sh`.
- **Outputs**
  - Pass/fail results for integration, unit, and e2e scenarios.
  - Coverage artifacts (`coverage.xml`, web coverage outputs) and Playwright reports/results.

## Dependencies
- pytest, pytest-asyncio, pytest-cov, httpx
- Playwright test runner
- Node/npm for web and e2e execution
- Python virtual environment (`.venv`)

## Local Run Command(s)
- Integration suite:
  - `.venv/bin/python -m pytest tests/integration -q`
- Unit subset:
  - `.venv/bin/python -m pytest tests/unit -q`
- E2E suite:
  - `npm run test:e2e`

## Test Command(s)
- Canonical project-level test commands:
  - `bash scripts/test_integration.sh`
  - `bash scripts/test_ui.sh`
  - `bash scripts/verify.sh`

## Known Limitations
- E2E coverage relies on browser tooling and can be sensitive to environment/network/display constraints.
- Integration tests include runtime-oriented flows; failures may reflect local machine prerequisites rather than purely application logic.
- Unit test coverage is currently selective, with heavier emphasis on integration behavior.

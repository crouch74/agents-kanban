# `packages/mcp-server` Module Guide

## Purpose
`packages/mcp-server` provides the MCP-native surface for Agent Control Plane, exposing tools/resources for agents while reusing shared domain logic from `packages/core`.

## Key Inputs / Outputs
- **Inputs**
  - MCP tool/resource requests from connected MCP clients.
  - Optional idempotency tokens (`client_request_id`) for write operations.
  - Shared settings/runtime configuration and database state.
- **Outputs**
  - Structured MCP tool results for reads/writes over the control-plane domain.
  - Error responses aligned with backend validation semantics.
  - Side effects persisted via shared services (including events).

## Dependencies
- Python 3.12+
- `mcp` Python SDK
- Local package dependency: `acp-core`

## Local Run Command(s)
- Start full stack including MCP:
  - `bash scripts/dev-stack.sh`
- MCP only:
  - `bash scripts/dev-stack.sh --mcp-only`

## Test Command(s)
- Integration tests including MCP handler behavior:
  - `bash scripts/test_integration.sh`
- Focused MCP integration test file:
  - `.venv/bin/python -m pytest tests/integration/test_mcp_handlers.py -q`

## Known Limitations
- MCP surface parity with REST is strong but still evolving; new behavior should continue to land in shared services first.
- Transport/runtime behavior depends on local environment configuration (host/port/transport env vars).
- End-to-end verification typically occurs through integration tests instead of an isolated package-level test harness.

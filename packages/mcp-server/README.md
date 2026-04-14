# `packages/mcp-server` Module Guide

## Purpose

`packages/mcp-server` exposes the task-board MCP surface for external agents.

## Scope

MCP tools/resources support:

- project and board reads
- task list/get/create/update
- task comments
- search and dashboard reads
- event resources

MCP does not launch or supervise agent runtimes.

## Local Run

```bash
bash scripts/dev-stack.sh --mcp-only
```

## Tests

```bash
.venv/bin/python -m pytest tests/integration -q
```

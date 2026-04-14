# `packages/core` Module Guide

## Purpose

`packages/core` is the shared domain/service layer for the Shared Task Board.

It owns canonical behavior for:

- projects
- board columns
- tasks
- task comments
- event history
- search and dashboard read models

## Boundaries

- No runtime orchestration (tmux/session/worktree/repository control plane concerns removed from active product boundary).
- Services are reusable by both REST and MCP adapters.

## Local Usage

Run through consumer apps:

```bash
bash scripts/dev-stack.sh
```

## Tests

```bash
.venv/bin/python -m pytest tests/unit/core -q
.venv/bin/python -m pytest tests/integration -q
```

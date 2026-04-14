# `apps/api` Module Guide

## Purpose

`apps/api` provides the REST/WebSocket API for the Shared Task Board.

## Active Domains

- projects
- board views
- tasks
- task comments
- events
- search
- dashboard

## Removed Domains

The API no longer exposes control-plane runtime domains:

- sessions
- worktrees
- repositories
- waiting questions
- bootstrap execution
- runtime diagnostics/reconciliation

## Run

```bash
bash scripts/dev-stack.sh --api-only
```

## Test

```bash
.venv/bin/python -m pytest tests/integration -q
```

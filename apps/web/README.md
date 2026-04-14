# `apps/web` Module Guide

## Purpose

`apps/web` is the operator interface for the Shared Task Board.

## Main UI Areas

- Home dashboard (`task_counts` summary)
- Projects and board view (drag/move tasks)
- Task detail (description + comments)
- Search
- Activity timeline

## Product Boundary

The UI is a collaboration surface for operators and external agents updating the same task store.

It does not include runtime/session/worktree/waiting-inbox control-plane behavior.

## Local Run

```bash
bash scripts/dev-stack.sh --web-only
```

## Tests

```bash
npm --workspace @acp/web run test
npm run test:e2e
```

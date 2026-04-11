# Contributing to Agent Control Plane

Thanks for contributing to Agent Control Plane. This project is intentionally local-first and operator-focused. Keep changes explicit, reviewable, and aligned with backend-driven source-of-truth semantics.

## Setup Prerequisites

Before opening a pull request, make sure your local environment includes:

- Linux/macOS shell environment
- Python 3.12+
- Node.js 22+
- npm (workspaces enabled)
- `tmux`
- `git`

From a clean checkout, run:

```bash
bash scripts/bootstrap.sh
```

This repository treats bootstrap as a required setup gate for contributors.

## Branching Strategy

- Branch from `main`.
- Use short-lived topic branches for one logical slice of work.
- Prefer branch names that map to scope and intent, for example:
  - `feat/task-export`
  - `fix/worktree-cleanup`
  - `docs/contributing-guide`
- Rebase or merge `main` regularly to avoid drift before requesting review.

## Commit Message Convention (Required)

Use **Conventional Commits** for every commit.

Format:

```text
type(scope): summary
```

Examples:

- `feat(api): add task dependency validation`
- `fix(web): preserve project filter on refresh`
- `docs(readme): clarify verification flow`

Recommended types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.

## Required Verification Gates

Both of the following are required before opening or updating a PR:

1. Bootstrap dependencies and local tooling:

   ```bash
   bash scripts/bootstrap.sh
   ```

2. Run full verification:

   ```bash
   bash scripts/verify.sh
   ```

Do not open a PR with skipped or partially run verification unless explicitly coordinated with maintainers.

## Pull Request Checklist

Before requesting review, verify all items below:

- [ ] Scope is focused and intentionally limited.
- [ ] Branch is up to date with `main`.
- [ ] Commits follow Conventional Commit format.
- [ ] `bash scripts/bootstrap.sh` completed successfully.
- [ ] `bash scripts/verify.sh` completed successfully.
- [ ] Docs were updated when behavior or operator workflow changed.
- [ ] PR description explains intent, change summary, and verification evidence.
- [ ] UI-impacting changes include screenshot evidence via CI artifacts.

## Reviewer Expectations

Reviewers are expected to:

- Validate architectural guardrails:
  - backend/service layer remains the source of truth
  - no workflow/state-machine bypasses
  - no unnecessary API/MCP behavior drift
- Confirm change scope matches the PR description.
- Verify contributor-provided command outputs for required gates.
- Request tests/docs when behavior changes without corresponding coverage or documentation.
- Prefer small follow-up PRs over approving oversized, mixed-concern changes.

## Notes for High-Care Changes

Apply extra scrutiny for:

- schema or migration changes
- workflow transition semantics
- session/worktree ownership behavior
- hidden state that exists only in UI and not backend state

When in doubt, choose the simpler local-first implementation and keep service-layer logic central.

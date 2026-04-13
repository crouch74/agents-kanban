# Project creation user flows (Playwright e2e coverage)

This document maps currently implemented project creation flows to Playwright end-to-end tests for the operator UI, using the mocked control-plane API layer under `tests/e2e/support/mockControlPlane.ts`.

## Flows covered by e2e tests

1. **Default bootstrap dialog flow (`+ New Project`)**
   - Opens the New Project dialog from the Projects section.
   - Fills name, repo path, and initial prompt.
   - Reviews bootstrap and verifies kickoff task appears in the board context.

2. **Existing-repository confirmation flow**
   - Preview response marks `confirmation_required=true`.
   - UI shows planned repo changes and switches CTA to `Confirm + launch bootstrap`.
   - Confirm action successfully completes bootstrap and closes the dialog.

3. **API-only project creation contract (from browser context)**
   - Executes `POST /api/v1/projects` via browser `fetch`.
   - Reloads the page and verifies the new project appears in the project switcher.

## Test file

- `tests/e2e/project-creation-user-flows.spec.ts`

## How to run

```bash
npx playwright test tests/e2e/project-creation-user-flows.spec.ts
```

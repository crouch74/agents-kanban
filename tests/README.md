# Tests

This suite validates the Shared Task Board boundary.

## Coverage Focus

- Project creation and board retrieval
- Task creation, movement, and detail reads
- Task comments with actor/source metadata
- Search and events read models
- Browser flow for create/add/comment lifecycle

## Commands

```bash
.venv/bin/python -m pytest tests/integration -q
.venv/bin/python -m pytest tests/unit -q
npm run test:e2e
```

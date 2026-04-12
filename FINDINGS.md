## 2026-04-12

- `bash scripts/verify.sh --skip-bootstrap` currently fails due to a mismatch between
  `tests/integration/test_bootstrap_service.py` expectations and
  `acp_core.settings.Settings.bootstrap_agent_command_template` (expects
  `codex -a never exec -s workspace-write`, but settings uses
  `codex --dangerously-bypass-approvals-and-sandbox exec`).

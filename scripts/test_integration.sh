#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT/.venv/bin/python"
PY_COV_MIN="${ACP_PY_COV_FAIL_UNDER:-85}"

log() {
  echo "$1 $2"
}

cd "$ROOT"

if [ ! -x "$VENV_PYTHON" ]; then
  log "❌" "Missing .venv. Run scripts/bootstrap.sh first."
  exit 1
fi

log "🧪" "Running Python integration tests with coverage (fail-under=${PY_COV_MIN})"
"$VENV_PYTHON" -m pytest tests/integration -q \
  --cov=app \
  --cov=acp_core \
  --cov=acp_mcp_server \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-branch \
  --cov-fail-under="${PY_COV_MIN}"

log "✅" "Python integration tests passed"

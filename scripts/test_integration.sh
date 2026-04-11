#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT/.venv/bin/python"

log() {
  echo "$1 $2"
}

cd "$ROOT"

if [ ! -x "$VENV_PYTHON" ]; then
  log "❌" "Missing .venv. Run scripts/bootstrap.sh first."
  exit 1
fi

log "🧪" "Running Python integration tests with coverage"
"$VENV_PYTHON" -m pytest tests/integration -q \
  --cov=app \
  --cov=acp_core \
  --cov=acp_mcp_server \
  --cov-fail-under=84 \
  --cov-report=term-missing \
  --cov-report=xml

log "✅" "Python integration tests passed"

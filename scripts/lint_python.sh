#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT/.venv/bin/python"

cd "$ROOT"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "❌ Python virtual environment not found at .venv. Run scripts/bootstrap.sh first."
  exit 1
fi

echo "🧹 Running Python import hygiene checks (unused imports)."
"$VENV_PYTHON" -m ruff check \
  apps/api \
  packages/core/src \
  packages/mcp-server/src \
  tests \
  --select F401

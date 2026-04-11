#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_BOOTSTRAP=0

log() {
  echo "$1 $2"
}

usage() {
  cat <<'USAGE'
Usage: scripts/verify.sh [options]

Run canonical repository verification.

Options:
  --skip-bootstrap   Assume dependencies are already installed.
  -h, --help         Show this help text.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --skip-bootstrap)
      SKIP_BOOTSTRAP=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log "❌" "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

cd "$ROOT"

if [ "$SKIP_BOOTSTRAP" -eq 0 ]; then
  log "📦" "Bootstrapping dependencies"
  bash "$ROOT/scripts/bootstrap.sh" --with-browser
fi

log "🧪" "Running integration verification"
bash "$ROOT/scripts/test_integration.sh"

log "🧪" "Running Python lint checks"
bash "$ROOT/scripts/lint_python.sh"

log "🧪" "Running UI verification"
bash "$ROOT/scripts/test_ui.sh"

log "✅" "Verification complete"

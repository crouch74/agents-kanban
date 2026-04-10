#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT/.venv/bin/python"
INSTALL_BROWSER=0
INSTALL_BROWSER_DEPS=0

log() {
  echo "$1 $2"
}

usage() {
  cat <<'USAGE'
Usage: scripts/bootstrap.sh [options]

Bootstraps Python + Node dependencies from a clean checkout.

Options:
  --with-browser        Install Playwright Chromium browser.
  --with-browser-deps   Install Playwright Chromium plus OS browser deps.
  -h, --help            Show this help text.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --with-browser)
      INSTALL_BROWSER=1
      ;;
    --with-browser-deps)
      INSTALL_BROWSER=1
      INSTALL_BROWSER_DEPS=1
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

log "🔎" "Checking required tooling"
command -v python3 >/dev/null || { log "❌" "python3 is required"; exit 1; }
command -v npm >/dev/null || { log "❌" "npm is required"; exit 1; }
python3 - <<'PYVERSION'
import sys
if sys.version_info < (3, 12):
    raise SystemExit("❌ Python 3.12+ is required")
print("✅ Python version is compatible")
PYVERSION

if [ ! -x "$VENV_PYTHON" ]; then
  log "🐍" "Creating Python virtual environment at .venv"
  python3 -m venv .venv
else
  log "🐍" "Using existing Python virtual environment"
fi

log "📦" "Upgrading pip"
"$VENV_PYTHON" -m pip install --upgrade pip

log "📦" "Installing Python dependencies"
"$VENV_PYTHON" -m pip install -r apps/api/requirements-dev.txt

if [ -f "$ROOT/package-lock.json" ]; then
  log "📦" "Installing Node dependencies with npm ci"
  npm ci
else
  log "📦" "Installing Node dependencies with npm install"
  npm install
fi

if [ "$INSTALL_BROWSER" -eq 1 ]; then
  if [ "$INSTALL_BROWSER_DEPS" -eq 1 ]; then
    log "🌐" "Installing Playwright Chromium and system dependencies"
    npx playwright install --with-deps chromium
  else
    log "🌐" "Installing Playwright Chromium"
    npx playwright install chromium
  fi
fi

log "✅" "Bootstrap complete"

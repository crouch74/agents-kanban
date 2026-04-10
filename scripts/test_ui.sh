#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() {
  echo "$1 $2"
}

cd "$ROOT"

if [ ! -d "$ROOT/node_modules" ]; then
  log "❌" "Missing node_modules. Run scripts/bootstrap.sh first."
  exit 1
fi

log "🧪" "Running web unit tests"
npm --workspace @acp/web run test

log "🧪" "Building web app"
npm --workspace @acp/web run build

if [ "${ACP_SKIP_PLAYWRIGHT_INSTALL:-0}" != "1" ]; then
  log "🌐" "Installing Playwright Chromium"
  npx playwright install chromium
else
  log "🌐" "Skipping Playwright install (ACP_SKIP_PLAYWRIGHT_INSTALL=1)"
fi

log "🌐" "Running Playwright smoke tests"
npx playwright test

log "✅" "UI verification passed"

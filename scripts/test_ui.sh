#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() {
  echo "$1 $2"
}

playwright_chromium_path() {
  node -e "const { chromium } = require('playwright'); console.log(chromium.executablePath())"
}

has_playwright_chromium() {
  local executable_path
  executable_path="$(playwright_chromium_path 2>/dev/null || true)"
  [ -n "$executable_path" ] && [ -x "$executable_path" ]
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

if has_playwright_chromium; then
  log "✅" "Playwright Chromium is already installed; skipping download."
else
  log "🌐" "Installing Playwright Chromium"
  timeout 120s npx playwright install chromium
fi

log "🌐" "Running Playwright smoke tests"
npx playwright test

log "✅" "UI verification passed"

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() {
  echo "$1 $2"
}

cd "$ROOT"
mkdir -p "$ROOT/artifacts/screenshots"

log "📸" "Capturing UI screenshots with dummy project fixtures"
npx playwright test tests/e2e/design-screenshots.spec.ts

log "✅" "Screenshots saved under artifacts/screenshots/"

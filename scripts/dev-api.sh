#!/usr/bin/env bash
set -euo pipefail

API_PORT="${ACP_API_PORT:-8000}"
API_HOST="${ACP_API_HOST:-127.0.0.1}"

export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/apps/api:$(pwd)/packages/core/src"
python3 -m uvicorn app.main:app --reload --app-dir apps/api --host "$API_HOST" --port "$API_PORT" --reload-dir apps/api --reload-dir packages/core/src

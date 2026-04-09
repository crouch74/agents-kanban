#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/apps/api:$(pwd)/packages/core/src"
python3 -m uvicorn app.main:app --reload --app-dir apps/api --port 8000


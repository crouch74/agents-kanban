#!/usr/bin/env bash
set -euo pipefail

WEB_PORT="${ACP_WEB_PORT:-5173}"

npm --workspace @acp/web run dev -- --host 127.0.0.1 --port "$WEB_PORT"

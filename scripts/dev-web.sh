#!/usr/bin/env bash
set -euo pipefail

npm --workspace @acp/web run dev -- --host 127.0.0.1 --port 5173


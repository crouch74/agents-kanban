#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT/.venv/bin/python"
VENV_BIN_DIR="$ROOT/.venv/bin"
RUNTIME_HOME="${ACP_RUNTIME_HOME:-$ROOT/.acp}"
LOGS_DIR="$RUNTIME_HOME/logs/dev"
PYTHONPATH_COMMON="$ROOT/apps/api:$ROOT/packages/core/src:$ROOT/packages/mcp-server/src${PYTHONPATH:+:$PYTHONPATH}"
MCP_TRANSPORT="${ACP_MCP_TRANSPORT:-streamable-http}"
MCP_HOST="${FASTMCP_HOST:-127.0.0.1}"
MCP_PORT="${FASTMCP_PORT:-8001}"
MCP_PATH="${FASTMCP_STREAMABLE_HTTP_PATH:-/mcp}"
API_PORT="${ACP_API_PORT:-8000}"
API_HOST="${ACP_API_HOST:-127.0.0.1}"
WEB_PORT="${ACP_WEB_PORT:-5173}"

ENABLE_API=1
ENABLE_WEB=1
ENABLE_MCP=1
NO_BOOTSTRAP=0
SHUTTING_DOWN=0

SERVICE_NAMES=()
SERVICE_PIDS=()
MONITOR_PIDS=()
TARGET_PORTS=()

usage() {
  cat <<'EOF'
Usage: scripts/dev-stack.sh [options]

Starts the local development stack, bootstrapping prerequisites when needed.

Options:
  --no-bootstrap       Do not auto-bootstrap missing prerequisites.
  --no-mcp             Start API and web only.
  --api-only           Start only the API service.
  --web-only           Start only the web service.
  --mcp-only           Start only the MCP server.
  --logs-dir <path>    Write per-service logs to this directory.
  -h, --help           Show this help text.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-bootstrap)
      NO_BOOTSTRAP=1
      ;;
    --no-mcp)
      ENABLE_MCP=0
      ;;
    --api-only)
      ENABLE_API=1
      ENABLE_WEB=0
      ENABLE_MCP=0
      ;;
    --web-only)
      ENABLE_API=0
      ENABLE_WEB=1
      ENABLE_MCP=0
      ;;
    --mcp-only)
      ENABLE_API=0
      ENABLE_WEB=0
      ENABLE_MCP=1
      ;;
    --logs-dir)
      if [ "$#" -lt 2 ]; then
        echo "Missing value for --logs-dir" >&2
        exit 1
      fi
      LOGS_DIR="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

load_env_config() {
  if [ -f "$ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ROOT/.env"
    set +a
  fi

  API_PORT="${ACP_API_PORT:-$API_PORT}"
  API_HOST="${ACP_API_HOST:-$API_HOST}"
  WEB_PORT="${ACP_WEB_PORT:-$WEB_PORT}"
  MCP_PORT="${FASTMCP_PORT:-$MCP_PORT}"
  MCP_HOST="${FASTMCP_HOST:-$MCP_HOST}"
  MCP_PATH="${FASTMCP_STREAMABLE_HTTP_PATH:-$MCP_PATH}"
}

if [ "$ENABLE_API" -eq 0 ] && [ "$ENABLE_WEB" -eq 0 ] && [ "$ENABLE_MCP" -eq 0 ]; then
  echo "No services selected." >&2
  exit 1
fi

case "$LOGS_DIR" in
  /*) ;;
  *) LOGS_DIR="$ROOT/$LOGS_DIR" ;;
esac

python_service_requested() {
  [ "$ENABLE_API" -eq 1 ] || [ "$ENABLE_MCP" -eq 1 ]
}

node_service_requested() {
  [ "$ENABLE_WEB" -eq 1 ]
}

run_bootstrap() {
  echo "Bootstrapping local dependencies..."
  (
    cd "$ROOT"
    bash "$ROOT/scripts/bootstrap.sh"
  )
}

check_python_deps() {
  PYTHONPATH="$PYTHONPATH_COMMON" "$VENV_PYTHON" -c \
    "import fastapi, uvicorn, pydantic, pydantic_settings, sqlalchemy, structlog, mcp, watchfiles, git, libtmux, acp_core, acp_mcp_server"
}

ensure_prerequisites() {
  local needs_bootstrap=0

  if python_service_requested && [ ! -x "$VENV_PYTHON" ]; then
    needs_bootstrap=1
  fi

  if node_service_requested && [ ! -d "$ROOT/node_modules" ]; then
    needs_bootstrap=1
  fi

  if [ "$needs_bootstrap" -eq 1 ]; then
    if [ "$NO_BOOTSTRAP" -eq 1 ]; then
      echo "Missing prerequisites and --no-bootstrap was set." >&2
      exit 1
    fi
    run_bootstrap
  fi

  if python_service_requested; then
    if [ ! -x "$VENV_PYTHON" ]; then
      echo "Python virtual environment is still missing after bootstrap." >&2
      exit 1
    fi

    if ! check_python_deps >/dev/null 2>&1; then
      if [ "$NO_BOOTSTRAP" -eq 1 ]; then
        echo "Python dependencies are incomplete and --no-bootstrap was set." >&2
        exit 1
      fi
      echo "Installing missing Python dependencies..."
      (
        cd "$ROOT"
        "$VENV_PYTHON" -m pip install -r apps/api/requirements-dev.txt
      )
    fi
  fi

  if node_service_requested && [ ! -d "$ROOT/node_modules" ]; then
    echo "node_modules is still missing after bootstrap." >&2
    exit 1
  fi
}

start_log_monitor() {
  local service_name="$1"
  local log_file="$2"

  (
    tail -n 0 -F "$log_file" 2>/dev/null | while IFS= read -r line; do
      printf '[%s] %s\n' "$service_name" "$line"
    done
  ) &
  MONITOR_PIDS+=("$!")
}

start_service() {
  local service_name="$1"
  local log_file="$2"

  mkdir -p "$(dirname "$log_file")"
  : > "$log_file"

  case "$service_name" in
    api)
      (
        cd "$ROOT"
        export PATH="$VENV_BIN_DIR:$PATH"
        export PYTHONPATH="$PYTHONPATH_COMMON"
        export ACP_API_PORT="$API_PORT"
        export ACP_API_HOST="$API_HOST"
        bash "$ROOT/scripts/dev-api.sh"
      ) >>"$log_file" 2>&1 &
      ;;
    web)
      (
        cd "$ROOT"
        export PATH="$VENV_BIN_DIR:$PATH"
        export ACP_WEB_PORT="$WEB_PORT"
        bash "$ROOT/scripts/dev-web.sh"
      ) >>"$log_file" 2>&1 &
      ;;
    mcp)
      (
        cd "$ROOT"
        export PATH="$VENV_BIN_DIR:$PATH"
        export PYTHONPATH="$PYTHONPATH_COMMON"
        export ACP_MCP_TRANSPORT="$MCP_TRANSPORT"
        export FASTMCP_HOST="$MCP_HOST"
        export FASTMCP_PORT="$MCP_PORT"
        export FASTMCP_STREAMABLE_HTTP_PATH="$MCP_PATH"
        python3 -c 'import os; from acp_mcp_server.server import mcp; mcp.settings.host = os.environ["FASTMCP_HOST"]; mcp.settings.port = int(os.environ["FASTMCP_PORT"]); mcp.settings.streamable_http_path = os.environ["FASTMCP_STREAMABLE_HTTP_PATH"]; mcp.run(transport=os.environ["ACP_MCP_TRANSPORT"])'
      ) >>"$log_file" 2>&1 &
      ;;
    *)
      echo "Unsupported service: $service_name" >&2
      exit 1
      ;;
  esac

  SERVICE_NAMES+=("$service_name")
  SERVICE_PIDS+=("$!")
  start_log_monitor "$service_name" "$log_file"
}

add_port_to_kill_list() {
  local port="$1"
  local existing

  if [ -z "$port" ]; then
    return
  fi

  for existing in "${TARGET_PORTS[@]:-}"; do
    if [ "$existing" = "$port" ]; then
      return
    fi
  done

  TARGET_PORTS+=("$port")
}

kill_configured_port_listeners() {
  local port pid
  local -a pids=()

  for port in "${TARGET_PORTS[@]:-}"; do
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
      continue
    fi

    for pid in $(lsof -ti :$port -sTCP:LISTEN -P -n 2>/dev/null || true); do
      pids+=("$pid")
    done
  done

  if [ "${#pids[@]}" -eq 0 ]; then
    return
  fi

  for pid in "${pids[@]}"; do
    kill -9 "$pid" 2>/dev/null || true
  done
}

cleanup() {
  SHUTTING_DOWN=1

  local pid
  for pid in "${SERVICE_PIDS[@]:-}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done

  sleep 1

  for pid in "${SERVICE_PIDS[@]:-}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  done

  for pid in "${MONITOR_PIDS[@]:-}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
}

trap 'cleanup; exit 0' INT TERM

print_summary() {
  echo "Dev stack starting from $ROOT"
  echo "Runtime home: $RUNTIME_HOME"
  echo "Logs directory: $LOGS_DIR"
  if [ "$ENABLE_API" -eq 1 ]; then
    echo "API: http://$API_HOST:$API_PORT"
    echo "Health: http://$API_HOST:$API_PORT/api/v1/health"
  fi
  if [ "$ENABLE_WEB" -eq 1 ]; then
    echo "Web: http://127.0.0.1:$WEB_PORT"
  fi
  if [ "$ENABLE_MCP" -eq 1 ]; then
    echo "MCP: http://$MCP_HOST:$MCP_PORT$MCP_PATH"
  fi
  echo "Press Ctrl-C to stop all services."
}

monitor_services() {
  local i
  local pid
  local service_name
  local status

  while true; do
    i=0
    while [ "$i" -lt "${#SERVICE_PIDS[@]}" ]; do
      pid="${SERVICE_PIDS[$i]}"
      service_name="${SERVICE_NAMES[$i]}"

      if ! kill -0 "$pid" 2>/dev/null; then
        wait "$pid" || status=$?
        status="${status:-0}"
        if [ "$SHUTTING_DOWN" -eq 0 ]; then
          echo "[$service_name] exited unexpectedly with status $status" >&2
          cleanup
          exit 1
        fi
      fi

      i=$((i + 1))
      status=0
    done

    sleep 1
  done
}

mkdir -p "$RUNTIME_HOME" "$LOGS_DIR"
load_env_config

if [ "$ENABLE_API" -eq 1 ]; then
  add_port_to_kill_list "$API_PORT"
fi

if [ "$ENABLE_WEB" -eq 1 ]; then
  add_port_to_kill_list "$WEB_PORT"
fi

if [ "$ENABLE_MCP" -eq 1 ]; then
  add_port_to_kill_list "$MCP_PORT"
fi

kill_configured_port_listeners
ensure_prerequisites
print_summary

if [ "$ENABLE_API" -eq 1 ]; then
  start_service "api" "$LOGS_DIR/api.log"
fi

if [ "$ENABLE_WEB" -eq 1 ]; then
  start_service "web" "$LOGS_DIR/web.log"
fi

if [ "$ENABLE_MCP" -eq 1 ]; then
  start_service "mcp" "$LOGS_DIR/mcp.log"
fi

monitor_services

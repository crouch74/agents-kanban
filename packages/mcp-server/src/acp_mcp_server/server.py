import logging
import sys

from mcp.server.fastmcp import FastMCP

from acp_mcp_server import handlers
from acp_mcp_server.registry import register_mcp_handlers

# MCP SDK (FastMCP) has a bug where it often redirects INFO logs to stdout,
# corrupting the JSON-RPC transport. We force-silence all loggers and
# ensure a stderr-only root logger.
logging.root.handlers = []
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

mcp = FastMCP("Agent Control Plane", json_response=True, log_level="WARNING")

# Specifically target the noisy low-level server logger
_lowlevel_logger = logging.getLogger("mcp.server.lowlevel.server")
_lowlevel_logger.setLevel(logging.WARNING)
_lowlevel_logger.propagate = False
_lowlevel_logger.handlers = [logging.StreamHandler(sys.stderr)]

register_mcp_handlers(mcp)


def __getattr__(name: str):
    """Backward-compatible handler passthrough used by tests and external callers."""
    return getattr(handlers, name)


def project_list() -> list[dict]:
    """Normalize project list handler output to plain payloads."""
    items = handlers.project_list()
    return [item.model_dump() if hasattr(item, "model_dump") else item for item in items]


def project_board_state(project_id: str) -> object:
    return handlers.project_board_resource(project_id)


def task_detail_state(task_id: str) -> object:
    return handlers.task_detail_resource(task_id)


def task_completion_state(task_id: str) -> object:
    return handlers.task_completion_resource(task_id)


def session_timeline_state(session_id: str) -> object:
    return handlers.session_timeline_resource(session_id)


def waiting_question_state(question_id: str) -> object:
    return handlers.question_resource(question_id)


def repo_inventory_state(project_id: str) -> object:
    return handlers.repo_inventory_resource(project_id)


def local_diagnostics_state() -> object:
    return handlers.diagnostics_resource()


def recent_project_events(project_id: str) -> object:
    return handlers.recent_events_resource(project_id=project_id)


def recent_task_events(task_id: str) -> object:
    return handlers.recent_events_resource(task_id=task_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

import logging
import sys

from mcp.server.fastmcp import FastMCP

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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

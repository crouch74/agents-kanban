import logging
import sys

from mcp.server.fastmcp import FastMCP

from acp_mcp_server import handlers
from acp_mcp_server.registry import register_mcp_handlers

logging.root.handlers = []
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

mcp = FastMCP("Shared Task Board", json_response=True, log_level="WARNING")

_lowlevel_logger = logging.getLogger("mcp.server.lowlevel.server")
_lowlevel_logger.setLevel(logging.WARNING)
_lowlevel_logger.propagate = False
_lowlevel_logger.handlers = [logging.StreamHandler(sys.stderr)]

register_mcp_handlers(mcp)


def __getattr__(name: str):
    return getattr(handlers, name)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

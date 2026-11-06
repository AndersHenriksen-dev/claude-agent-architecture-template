"""The MCP server: the statement tools, served over stdio to whoever launches it.

`.mcp.json` tells Claude Code how to launch it. Claude Code then sees each tool as `mcp__subfinder__<tool>`, which is
the name the hooks in `.claude/settings.json` match on.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from subfinder.lib.shared.settings import Strict, config_for
from subfinder.lib.statement import tools


class _Config(Strict):
    name: str
    instructions: str
    read_tools: dict[str, str]
    write_tools: dict[str, str]


CONFIG = config_for(__name__, _Config)

# Any: tools have different signatures, and MCPServer reads each one's own to build its schema.
_READ_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "list_transactions": tools.list_transactions,
    "get_merchant": tools.get_merchant,
    "get_summary": tools.get_summary,
}
_WRITE_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "tag_subscription": tools.tag_subscription,
    "save_summary": tools.save_summary,
}


def add_read_tools(server: MCPServer) -> None:
    """Add the tools that change nothing. The connector serves only these."""
    annotations = ToolAnnotations(read_only_hint=True)
    for name, function in _READ_FUNCTIONS.items():
        server.add_tool(function, name=name, description=CONFIG.read_tools[name], annotations=annotations)


def _add_write_tools(server: MCPServer) -> None:
    annotations = ToolAnnotations(read_only_hint=False)
    for name, function in _WRITE_FUNCTIONS.items():
        server.add_tool(function, name=name, description=CONFIG.write_tools[name], annotations=annotations)


def build_server() -> MCPServer:
    """The full server: every tool, for a client that runs on this machine with your hooks around it."""
    server = MCPServer(CONFIG.name, instructions=CONFIG.instructions)
    add_read_tools(server)
    _add_write_tools(server)
    return server

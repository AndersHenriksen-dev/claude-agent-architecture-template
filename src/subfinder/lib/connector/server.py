"""The server a connector talks to: the read tools only, over HTTP.

A connector call goes from Anthropic's cloud straight to this server. It passes through no Claude Code and none of our
code on the way, so no hook can check it. Tools that write therefore stay on the stdio server, where hooks run.
"""

from __future__ import annotations

import secrets
import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

import uvicorn
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from subfinder.lib.mcp_server.server import CONFIG as MCP_CONFIG
from subfinder.lib.mcp_server.server import add_read_tools
from subfinder.lib.shared.settings import Strict, config_for


class _Config(Strict):
    path: str
    default_port: int
    host: str


CONFIG = config_for(__name__, _Config)


class _RequireBearerToken:
    """Refuse any HTTP request without the token. It wraps the whole app, so nothing behind it needs to know."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self._app = app
        self._expected = f"Bearer {token}".encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass the request on only if its Authorization header matches."""
        if scope["type"] == "http":
            sent = dict(scope["headers"]).get(b"authorization", b"")
            if not secrets.compare_digest(sent, self._expected):
                await PlainTextResponse("Missing or wrong token.", status_code=401)(scope, receive, send)
                return
        await self._app(scope, receive, send)


def build_read_only_server() -> MCPServer:
    """The same server as over stdio, with the write tools left out."""
    server = MCPServer(MCP_CONFIG.name, instructions=MCP_CONFIG.instructions, log_level="WARNING")
    add_read_tools(server)
    return server


def build_app(token: str | None, public_host: str | None) -> ASGIApp:
    """Build the web app.

    Args:
        token: The bearer token every request must carry. None serves with no authentication, which is only for a
            claude.ai custom connector during a demo on made-up data: those accept no authentication or OAuth.
        public_host: The host name the server is reached at through a tunnel, if any. The MCP library refuses other
            Host headers, which is its protection against DNS rebinding.

    Returns:
        The app, ready to give to uvicorn.
    """
    hosts = [f"{CONFIG.host}:*", "localhost:*"] + ([public_host] if public_host else [])
    app = build_read_only_server().streamable_http_app(
        streamable_http_path=CONFIG.path,
        # Each request stands alone, so the server can restart and sit behind a proxy with nothing to lose.
        stateless_http=True,
        transport_security=TransportSecuritySettings(allowed_hosts=hosts),
    )
    return _RequireBearerToken(app, token) if token else app


def serve(app: ASGIApp, port: int) -> None:
    """Serve until stopped."""
    uvicorn.run(app, host=CONFIG.host, port=port, log_level="warning")


@contextmanager
def serving_in_background(app: ASGIApp) -> Iterator[str]:
    """Serve on a free local port for the length of a `with` block, and give back the URL. For the demo and the tests.

    Yields:
        The URL to connect to.
    """
    with socket.socket() as probe:
        probe.bind((CONFIG.host, 0))
        port: int = probe.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host=CONFIG.host, port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    try:
        yield f"http://{CONFIG.host}:{port}{CONFIG.path}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)

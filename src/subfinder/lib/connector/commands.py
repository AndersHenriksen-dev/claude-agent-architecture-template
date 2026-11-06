"""The connector commands: serve the read tools, and ask a question through the Messages API."""

from __future__ import annotations

import os

import anthropic
from dotenv import load_dotenv

from subfinder.lib.connector.request import ask
from subfinder.lib.connector.server import CONFIG, build_app, serve
from subfinder.lib.shared.settings import model_from_env

_TOKEN_VARIABLE = "SUBFINDER_CONNECTOR_TOKEN"


def cmd_serve(port: int, public_host: str | None, no_auth: bool) -> int:
    """Serve the read tools over HTTP on this machine. A tunnel is what makes them reachable from outside.

    Args:
        port: The local port.
        public_host: The host name of the tunnel, if there is one.
        no_auth: Serve with no token, which a claude.ai custom connector without OAuth needs.

    Returns:
        The exit code.
    """
    load_dotenv()
    token = os.environ.get(_TOKEN_VARIABLE)
    if not token and not no_auth:
        print(f"Set {_TOKEN_VARIABLE} first, or pass --no-auth to serve this made-up data with no token.")
        return 2
    print(f"Serving the read tools at http://{CONFIG.host}:{port}{CONFIG.path}. Stop with Ctrl+C.")
    serve(build_app(None if no_auth else token, public_host), port)
    return 0


def cmd_ask(url: str, question: str, yes: bool) -> int:
    """Ask a question through the MCP connector. Anthropic's cloud must be able to reach the URL.

    Args:
        url: The server's public URL.
        question: What to ask.
        yes: Whether to make the paid call. Without it, this only prints the plan.

    Returns:
        The exit code.
    """
    if not url.startswith("https://"):
        print("The URL must start with https://, because the request sends the token to it.")
        return 2
    print(f"Plan: 1 question on {model_from_env()} through the connector at {url}, usually a few cents or less.")
    if not yes:
        print("That costs money, so nothing was sent. Add --yes to run it.")
        return 0
    load_dotenv()
    answer = ask(anthropic.Anthropic(), url, os.environ.get(_TOKEN_VARIABLE), question)
    print(answer.text)
    print(f"Tools the cloud called on the server: {answer.tools_called}")
    print(f"Tokens: {answer.input_tokens} in, {answer.output_tokens} out.")
    return 0

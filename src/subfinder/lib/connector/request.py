"""The Messages API request that reaches the server through the MCP connector.

We never see the tool calls happen. Anthropic's cloud calls the server and the response reports what it did, which is
why this file has no tool loop and no checks.
"""

from __future__ import annotations

from typing import Any, Literal

import anthropic

from subfinder.lib.mcp_server.server import CONFIG as MCP_CONFIG
from subfinder.lib.shared.settings import Strict, config_for, model_from_env


class _Config(Strict):
    server_name: str
    max_tokens: int
    effort: Literal["low", "medium", "high", "xhigh", "max"]
    betas: list[str]
    fallbacks: Literal["default"]
    max_resumes: int
    system: str


CONFIG = config_for(__name__, _Config)


class Answer(Strict):
    """What came back: the text, which tools the cloud called on our server, and the tokens spent."""

    text: str
    tools_called: list[str]
    input_tokens: int
    output_tokens: int


def build_request(url: str, token: str | None, question: str) -> dict[str, Any]:
    """Build the request. Any: this is the keyword arguments of an SDK call, with fields of many types.

    It takes both halves the API requires: `mcp_servers` says where the server is, and a matching `mcp_toolset` in
    `tools` says what may be used. The toolset allows only the read tools by name. The server already offers no others,
    so a mistake on one side is not enough to expose a write.

    Args:
        url: The server's public URL. The API cannot reach localhost or a stdio server.
        token: The bearer token the server requires, if any.
        question: What to ask.

    Returns:
        The keyword arguments for `client.beta.messages.create`.
    """
    server: dict[str, str] = {"type": "url", "url": url, "name": CONFIG.server_name}
    if token:
        server["authorization_token"] = token
    return {
        "model": model_from_env(),
        "max_tokens": CONFIG.max_tokens,
        "system": CONFIG.system,
        "messages": [{"role": "user", "content": question}],
        "mcp_servers": [server],
        "tools": [
            {
                "type": "mcp_toolset",
                "mcp_server_name": CONFIG.server_name,
                "default_config": {"enabled": False},
                "configs": {name: {"enabled": True} for name in MCP_CONFIG.read_tools},
            },
        ],
        "output_config": {"effort": CONFIG.effort},
        "betas": CONFIG.betas,
        "fallbacks": CONFIG.fallbacks,
    }


def ask(client: anthropic.Anthropic, url: str, token: str | None, question: str) -> Answer:
    """Ask one question through the connector. This costs money.

    Raises:
        ValueError: If the model refused.
    """
    request = build_request(url, token, question)
    text: list[str] = []
    tools_called: list[str] = []
    input_tokens = output_tokens = 0
    for _ in range(CONFIG.max_resumes + 1):
        response = client.beta.messages.create(**request)
        if response.stop_reason == "refusal":
            raise ValueError("The model refused this question.")
        input_tokens += response.usage.input_tokens
        output_tokens += response.usage.output_tokens
        text += [block.text for block in response.content if block.type == "text"]
        tools_called += [block.name for block in response.content if block.type == "mcp_tool_use"]
        if response.stop_reason != "pause_turn":
            break
        # A paused turn carries on from exactly what it returned, so the content goes back unchanged.
        request["messages"] = [*request["messages"], {"role": "assistant", "content": response.content}]
    return Answer(
        text="\n".join(text),
        tools_called=tools_called,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

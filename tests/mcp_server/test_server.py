"""The MCP server, reached the way a real client reaches it: a subprocess speaking MCP over stdio."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters

from subfinder.lib.shared.settings import REPO_ROOT

MODULE = "subfinder.lib.mcp_server"


def _with_client[T](use: Callable[[Client], Awaitable[T]]) -> T:
    """Launch the real server as a subprocess, and hand a connected client to `use`."""

    async def main() -> T:
        parameters = StdioServerParameters(command=sys.executable, args=["-m", MODULE], env=dict(os.environ))
        async with Client(parameters) as client:
            return await use(client)

    return anyio.run(main)


def _tool_names(client: Client) -> Awaitable[list[str]]:
    async def names() -> list[str]:
        return [tool.name for tool in (await client.list_tools()).tools]

    return names()


def test_offers_every_tool() -> None:
    assert set(_with_client(_tool_names)) == {
        "list_transactions",
        "get_merchant",
        "get_summary",
        "tag_subscription",
        "save_summary",
    }


def test_read_tools_are_marked_read_only() -> None:
    async def read_only(client: Client) -> dict[str, bool | None]:
        tools = (await client.list_tools()).tools
        return {tool.name: tool.annotations.read_only_hint if tool.annotations else None for tool in tools}

    hints = _with_client(read_only)
    assert hints["list_transactions"] is True
    assert hints["save_summary"] is False


def test_a_read_returns_the_lines_with_amounts_as_strings() -> None:
    async def call(client: Client) -> object:
        return (await client.call_tool("get_merchant", {"name": "tunebox"})).structured_content

    content = _with_client(call)
    assert isinstance(content, dict)
    assert [(line["id"], line["amount"]) for line in content["result"]] == [("T05", "-109.00"), ("T30", "-109.00")]


def test_writes_land_in_the_workbook_on_disk(workspace: Path) -> None:
    async def call(client: Client) -> None:
        await client.call_tool("tag_subscription", {"merchant": "Tunebox", "transaction_ids": ["T05", "T18", "T30"]})
        await client.call_tool(
            "save_summary",
            {
                "lines": [{"merchant": "Tunebox", "monthly_saving": "109.00", "note": "Music."}],
                "total_monthly_saving": "109.00",
            },
        )

    _with_client(call)
    workbook = json.loads((workspace / "workbook.json").read_text(encoding="utf-8"))
    assert workbook["tags"][0]["merchant"] == "Tunebox"
    assert workbook["summary"]["total_monthly_saving"] == "109.00"


def test_a_float_amount_is_refused() -> None:
    async def call(client: Client) -> bool:
        result = await client.call_tool(
            "save_summary",
            {"lines": [], "total_monthly_saving": 109.0},
        )
        return result.is_error

    assert _with_client(call) is True


def test_mcp_json_launches_this_module() -> None:
    config = json.loads((REPO_ROOT / ".mcp.json").read_text(encoding="utf-8"))
    entry = config["mcpServers"]["subfinder"]
    assert entry["command"] == "uv"
    assert entry["args"][-2:] == ["-m", MODULE]

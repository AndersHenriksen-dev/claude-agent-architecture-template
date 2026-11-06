"""The connector's server, over real HTTP on this machine: what a remote client can and cannot reach."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import anyio
import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import MCPError

from subfinder.lib.connector.server import build_app, serving_in_background
from subfinder.lib.mcp_server.server import CONFIG as MCP_CONFIG
from subfinder.lib.statement.workbook import load_workbook

TOKEN = "made-up-test-value"


def _with_client[T](url: str, token: str | None, use: Callable[[Client], Awaitable[T]]) -> T:
    """Connect over HTTP, sending the token if there is one, and hand the client to `use`."""

    async def main() -> T:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with (
            httpx2.AsyncClient(headers=headers) as http_client,
            Client(streamable_http_client(url, http_client=http_client)) as client,
        ):
            return await use(client)

    return anyio.run(main)


async def _tool_names(client: Client) -> set[str]:
    return {tool.name for tool in (await client.list_tools()).tools}


class TestReadOnly:
    def test_offers_exactly_the_read_tools(self) -> None:
        with serving_in_background(build_app(TOKEN, None)) as url:
            assert _with_client(url, TOKEN, _tool_names) == set(MCP_CONFIG.read_tools)

    def test_has_no_write_tool_to_call(self) -> None:
        async def write_was_refused(client: Client) -> bool:
            try:
                result = await client.call_tool("save_summary", {"lines": [], "total_monthly_saving": "0.00"})
            except MCPError:
                return True
            return result.is_error

        with serving_in_background(build_app(TOKEN, None)) as url:
            assert _with_client(url, TOKEN, write_was_refused) is True
        assert load_workbook().summary is None

    def test_a_read_works_over_http(self) -> None:
        async def read(client: Client) -> object:
            return (await client.call_tool("get_merchant", {"name": "fitzone"})).structured_content

        with serving_in_background(build_app(TOKEN, None)) as url:
            content = _with_client(url, TOKEN, read)
        assert isinstance(content, dict)
        assert len(content["result"]) == 3


class TestToken:
    @pytest.mark.parametrize("sent", [{}, {"Authorization": "Bearer wrong"}])
    def test_refuses_a_missing_or_wrong_token(self, sent: dict[str, str]) -> None:
        with serving_in_background(build_app(TOKEN, None)) as url:
            assert httpx2.post(url, headers=sent, json={}).status_code == 401

    def test_serves_without_a_token_only_when_told_to(self) -> None:
        with serving_in_background(build_app(None, None)) as url:
            assert _with_client(url, None, _tool_names) == set(MCP_CONFIG.read_tools)


class TestHost:
    def test_refuses_an_unknown_host_name(self) -> None:
        with serving_in_background(build_app(None, None)) as url:
            assert httpx2.post(url, headers={"Host": "evil.example"}, json={}).status_code == 421

    def test_accepts_the_public_host_it_was_given(self) -> None:
        with serving_in_background(build_app(None, "tunnel.example")) as url:
            status = httpx2.post(url, headers={"Host": "tunnel.example"}, json={}).status_code
        assert status != 421

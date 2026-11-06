"""The connector request, with the client replaced: its shape must match what the API validates."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from subfinder.lib.connector.request import ask, build_request
from subfinder.lib.mcp_server.server import CONFIG as MCP_CONFIG

URL = "https://tunnel.example/mcp"


def _response(stop_reason: str, *blocks: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=list(blocks),
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )


def _text(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _tool(name: str) -> SimpleNamespace:
    return SimpleNamespace(type="mcp_tool_use", name=name)


class TestBuildRequest:
    def test_has_both_halves_and_they_match(self) -> None:
        request = build_request(URL, None, "Question")
        assert request["tools"][0]["type"] == "mcp_toolset"
        assert request["tools"][0]["mcp_server_name"] == request["mcp_servers"][0]["name"]

    def test_sends_the_beta_header_for_the_connector(self) -> None:
        assert "mcp-client-2025-11-20" in build_request(URL, None, "Question")["betas"]

    def test_allows_only_the_read_tools_by_name(self) -> None:
        toolset = build_request(URL, None, "Question")["tools"][0]
        assert toolset["default_config"] == {"enabled": False}
        assert set(toolset["configs"]) == set(MCP_CONFIG.read_tools)

    def test_sends_the_token_only_if_there_is_one(self) -> None:
        assert "authorization_token" not in build_request(URL, None, "Question")["mcp_servers"][0]
        assert build_request(URL, "abc", "Question")["mcp_servers"][0]["authorization_token"] == "abc"


class TestAsk:
    def test_reads_text_and_which_tools_ran(self) -> None:
        client = MagicMock()
        client.beta.messages.create.return_value = _response("end_turn", _tool("get_summary"), _text("Total 506.00."))
        answer = ask(client, URL, None, "Question")
        assert answer.text == "Total 506.00."
        assert answer.tools_called == ["get_summary"]
        assert (answer.input_tokens, answer.output_tokens) == (10, 5)

    def test_resumes_a_paused_turn_with_the_content_unchanged(self) -> None:
        client = MagicMock()
        paused = _response("pause_turn", _tool("list_transactions"))
        client.beta.messages.create.side_effect = [paused, _response("end_turn", _text("Done."))]
        answer = ask(client, URL, None, "Question")
        assert answer.tools_called == ["list_transactions"]
        assert answer.input_tokens == 20
        second_messages = client.beta.messages.create.call_args.kwargs["messages"]
        assert second_messages[-1] == {"role": "assistant", "content": paused.content}

    def test_stops_resuming_at_the_limit(self) -> None:
        client = MagicMock()
        client.beta.messages.create.return_value = _response("pause_turn")
        ask(client, URL, None, "Question")
        assert client.beta.messages.create.call_count == 4

    def test_a_refusal_is_an_error(self) -> None:
        client = MagicMock()
        client.beta.messages.create.return_value = _response("refusal")
        with pytest.raises(ValueError, match="refused"):
            ask(client, URL, None, "Question")

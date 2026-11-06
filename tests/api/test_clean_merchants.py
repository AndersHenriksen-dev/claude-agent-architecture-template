"""The Messages API call, with the client replaced: the request it sends and how it reads each kind of answer."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from subfinder.lib.api.clean_merchants import CleanedLines, clean_with_claude
from subfinder.lib.statement.recurring import CleanedLine

LINE = CleanedLine(description="VIEWLY *MONTHLY", merchant="Viewly", category="subscription")


def _client(stop_reason: str = "end_turn", parsed: CleanedLines | None = None) -> MagicMock:
    client = MagicMock()
    client.beta.messages.parse.return_value = SimpleNamespace(
        stop_reason=stop_reason,
        parsed_output=parsed,
        usage=SimpleNamespace(input_tokens=100, output_tokens=20),
    )
    return client


class TestCleanWithClaude:
    def _request(self) -> dict[str, Any]:
        client = _client(parsed=CleanedLines(lines=[LINE]))
        clean_with_claude(client, ["VIEWLY *MONTHLY"])
        return client.beta.messages.parse.call_args.kwargs

    def test_asks_for_the_structured_shape(self) -> None:
        assert self._request()["output_format"] is CleanedLines

    def test_sends_the_lines_as_data_in_the_user_message(self) -> None:
        request = self._request()
        assert "VIEWLY *MONTHLY" in request["messages"][0]["content"]
        assert "VIEWLY *MONTHLY" not in request["system"]

    def test_uses_the_configured_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SUBFINDER_MODEL", "claude-haiku-5-5")
        assert self._request()["model"] == "claude-haiku-5-5"

    def test_sends_no_parameter_the_current_models_reject(self) -> None:
        request = self._request()
        for rejected in ("temperature", "top_p", "top_k", "thinking", "tool_choice"):
            assert rejected not in request

    def test_turns_on_the_refusal_fallback_with_its_beta(self) -> None:
        request = self._request()
        assert request["fallbacks"] == "default"
        assert "server-side-fallback-2026-07-01" in request["betas"]

    def test_reports_tokens(self) -> None:
        cleaning = clean_with_claude(_client(parsed=CleanedLines(lines=[LINE])), ["VIEWLY *MONTHLY"])
        assert (cleaning.input_tokens, cleaning.output_tokens) == (100, 20)

    def test_a_refusal_is_an_error(self) -> None:
        with pytest.raises(ValueError, match="refusal"):
            clean_with_claude(_client(stop_reason="refusal"), ["VIEWLY *MONTHLY"])

    def test_a_line_left_out_is_an_error(self) -> None:
        with pytest.raises(ValueError, match="TUNEBOX"):
            clean_with_claude(_client(parsed=CleanedLines(lines=[LINE])), ["VIEWLY *MONTHLY", "TUNEBOX P2F3A1"])

"""The connector commands: no open server by accident, no token sent in clear, no paid call without --yes."""

from __future__ import annotations

import json

import pytest

from subfinder.lib.connector.commands import cmd_ask, cmd_serve
from subfinder.lib.shared.settings import REPO_ROOT


def _no_client(*_: object, **__: object) -> None:
    raise AssertionError("a client was created")


def test_ask_only_prints_the_plan_without_yes(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("subfinder.lib.connector.commands.anthropic.Anthropic", _no_client)
    assert cmd_ask("https://tunnel.example/mcp", "Question", yes=False) == 0
    assert "nothing was sent" in capsys.readouterr().out


def test_ask_refuses_a_url_that_would_send_the_token_in_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("subfinder.lib.connector.commands.anthropic.Anthropic", _no_client)
    assert cmd_ask("http://tunnel.example/mcp", "Question", yes=True) == 2


def test_serve_needs_a_token_or_an_explicit_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUBFINDER_CONNECTOR_TOKEN", raising=False)
    monkeypatch.setattr("subfinder.lib.connector.commands.load_dotenv", lambda: None)
    assert cmd_serve(port=1, public_host=None, no_auth=False) == 2


def test_claude_code_asks_before_a_paid_question() -> None:
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "Bash(uv run subfinder connector-ask:*)" in settings["permissions"]["ask"]

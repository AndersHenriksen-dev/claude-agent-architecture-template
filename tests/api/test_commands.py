"""The `run` command: it spends nothing without --yes, and it says what a call cost."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from subfinder.lib.api.clean_merchants import CleanedLines
from subfinder.lib.api.commands import cmd_run, cost_usd
from subfinder.lib.api.scripted import CONFIG as REFERENCE
from subfinder.lib.shared.settings import REPO_ROOT


def test_only_prints_the_plan_without_yes(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    def no_client(*_: object, **__: object) -> None:
        raise AssertionError("a client was created without --yes")

    monkeypatch.setattr("subfinder.lib.api.commands.anthropic.Anthropic", no_client)
    assert cmd_run(yes=False) == 0
    assert "nothing was sent" in capsys.readouterr().out


def test_with_yes_the_whole_paid_path_runs_and_reports(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    client.beta.messages.parse.return_value = SimpleNamespace(
        stop_reason="end_turn",
        parsed_output=CleanedLines(lines=REFERENCE.lines),
        usage=SimpleNamespace(input_tokens=1000, output_tokens=1000),
    )
    monkeypatch.setattr("subfinder.lib.api.commands.anthropic.Anthropic", lambda: client)
    monkeypatch.setattr("subfinder.lib.api.commands.load_dotenv", lambda: None)
    assert cmd_run(yes=True) == 0
    output = capsys.readouterr().out
    assert "506.00" in output
    assert f"{len(REFERENCE.lines)} of {len(REFERENCE.lines)} descriptions" in output
    assert "USD 0.0120" in output


def test_cost_adds_input_and_output_at_their_prices() -> None:
    assert cost_usd("claude-sonnet-5-5", 1_000_000, 1_000_000) == 12.0


def test_a_model_with_no_price_has_an_unknown_cost() -> None:
    assert cost_usd("made-up-model", 1, 1) is None


def test_claude_code_asks_before_running_it() -> None:
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "Bash(uv run subfinder run:*)" in settings["permissions"]["ask"]

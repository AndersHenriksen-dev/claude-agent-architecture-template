"""The commands from the outside: the free demo end to end, and that paid commands spend nothing without --yes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from subfinder.lib.api.commands import cmd_run, cost_usd
from subfinder.lib.connector.commands import cmd_ask, cmd_serve
from subfinder.lib.shared.settings import REPO_ROOT

RUN_CLI = [sys.executable, "-c", "from subfinder.cli import main; main()"]


def _cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*RUN_CLI, *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ.copy(),
        timeout=120,
    )


class TestDemo:
    def test_runs_end_to_end_with_no_key_and_covers_every_type(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = _cli("demo")
        assert result.returncode == 0, result.stderr
        for section in ("RULES", "SKILL", "API", "MCP", "HOOKS", "CONNECTOR"):
            assert f"=== {section}" in result.stdout
        assert "506.00" in result.stdout

    def test_leaves_the_real_workspace_alone(self, workspace: Path) -> None:
        assert _cli("demo").returncode == 0
        assert not workspace.exists()

    def test_prints_only_ascii_so_any_terminal_can_show_it(self) -> None:
        assert _cli("demo").stdout.isascii()


class TestPaidCommandsAskFirst:
    def test_run_only_prints_its_plan(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def no_client(*_: object, **__: object) -> None:
            raise AssertionError("a client was created without --yes")

        monkeypatch.setattr("subfinder.lib.api.commands.anthropic.Anthropic", no_client)
        assert cmd_run(yes=False) == 0
        assert "nothing was sent" in capsys.readouterr().out

    def test_connector_ask_only_prints_its_plan(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def no_client(*_: object, **__: object) -> None:
            raise AssertionError("a client was created without --yes")

        monkeypatch.setattr("subfinder.lib.connector.commands.anthropic.Anthropic", no_client)
        assert cmd_ask("https://tunnel.example/mcp", "Question", yes=False) == 0
        assert "nothing was sent" in capsys.readouterr().out


class TestServeRefusesToBeOpenByAccident:
    def test_needs_a_token_or_an_explicit_choice(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SUBFINDER_CONNECTOR_TOKEN", raising=False)
        monkeypatch.setattr("subfinder.lib.connector.commands.load_dotenv", lambda: None)
        assert cmd_serve(port=1, public_host=None, no_auth=False) == 2


class TestCost:
    def test_adds_input_and_output_at_their_prices(self) -> None:
        assert cost_usd("claude-sonnet-5-5", 1_000_000, 1_000_000) == 12.0

    def test_a_model_with_no_price_is_unknown(self) -> None:
        assert cost_usd("made-up-model", 1, 1) is None


def test_settings_ask_before_every_paid_command() -> None:
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "Bash(uv run subfinder run:*)" in settings["permissions"]["ask"]
    assert "Bash(uv run subfinder connector-ask:*)" in settings["permissions"]["ask"]

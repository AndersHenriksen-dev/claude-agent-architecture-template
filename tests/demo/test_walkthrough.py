"""The free demo from the outside: a fresh process with no key, as a stranger would run it."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

RUN_CLI = [sys.executable, "-c", "from subfinder.cli import main; main()"]


def _run_demo() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*RUN_CLI, "demo"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ.copy(),
        timeout=120,
        check=False,
    )


def test_runs_end_to_end_with_no_key_and_covers_every_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = _run_demo()
    assert result.returncode == 0, result.stderr
    for section in ("RULES", "SKILL", "API", "MCP", "HOOKS", "CONNECTOR"):
        assert f"=== {section}" in result.stdout
    assert "506.00" in result.stdout


def test_leaves_the_real_workspace_alone(workspace: Path) -> None:
    assert _run_demo().returncode == 0
    assert not workspace.exists()


def test_prints_only_ascii_so_any_terminal_can_show_it() -> None:
    assert _run_demo().stdout.isascii()

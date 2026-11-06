"""The hooks as Claude Code runs them: a new process, JSON on stdin, a decision on stdout."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import anyio

from subfinder.lib.mcp_server.server import build_server
from subfinder.lib.shared.settings import REPO_ROOT
from subfinder.lib.statement.tools import save_summary, tag_subscription

SETTINGS = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
SAVE = "mcp__subfinder__save_summary"
TAG = "mcp__subfinder__tag_subscription"


def _run(event: str, payload: dict[str, Any] | str) -> subprocess.CompletedProcess[str]:
    """Run the hook the way Claude Code does, with the common fields it always sends."""
    if isinstance(payload, dict):
        payload = json.dumps({"session_id": "s", "cwd": str(REPO_ROOT), "hook_event_name": event, **payload})
    return subprocess.run(
        [sys.executable, "-m", "subfinder.lib.hooks", event],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ.copy(),
        check=True,
    )


def _decision(result: subprocess.CompletedProcess[str]) -> dict[str, str]:
    return json.loads(result.stdout)["hookSpecificOutput"]


def _summary_input(saving: str) -> dict[str, Any]:
    return {
        "lines": [{"merchant": "Viewly", "monthly_saving": saving, "note": "Note."}],
        "total_monthly_saving": saving,
    }


class TestPreToolUse:
    def test_denies_an_overclaim_with_the_reason(self) -> None:
        tag_subscription("Viewly", ["T03", "T16", "T28"])
        result = _run("pre-tool-use", {"tool_name": SAVE, "tool_input": _summary_input("500.00")})
        decision = _decision(result)
        assert decision["hookEventName"] == "PreToolUse"
        assert decision["permissionDecision"] == "deny"
        assert "latest charge of 119.00" in decision["permissionDecisionReason"]

    def test_says_nothing_about_a_good_call(self) -> None:
        tag_subscription("Viewly", ["T03", "T16", "T28"])
        result = _run("pre-tool-use", {"tool_name": SAVE, "tool_input": _summary_input("119.00")})
        assert result.stdout == ""

    def test_denies_a_tag_of_a_made_up_charge(self) -> None:
        payload = {"tool_name": TAG, "tool_input": {"merchant": "Ghost", "transaction_ids": ["T99"]}}
        assert _decision(_run("pre-tool-use", payload))["permissionDecision"] == "deny"

    def test_denies_arguments_that_do_not_parse(self) -> None:
        payload = {"tool_name": SAVE, "tool_input": {"lines": [], "total_monthly_saving": 0.0}}
        assert _decision(_run("pre-tool-use", payload))["permissionDecision"] == "deny"

    def test_fails_closed_on_an_unreadable_event(self) -> None:
        assert _decision(_run("pre-tool-use", "{not json"))["permissionDecision"] == "deny"

    def test_reads_input_that_starts_with_a_byte_order_mark(self) -> None:
        payload = json.dumps({"tool_name": TAG, "tool_input": {"merchant": "Viewly", "transaction_ids": ["T03"]}})
        assert _run("pre-tool-use", "﻿" + payload).stdout == ""

    def test_ignores_fields_it_does_not_know(self) -> None:
        payload = {"tool_name": "mcp__subfinder__get_summary", "tool_input": {}, "mcp_server": {"source": "project"}}
        assert _run("pre-tool-use", payload).stdout == ""


class TestAudit:
    def _entries(self, workspace: Path) -> list[dict[str, Any]]:
        lines = (workspace / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines]

    def test_records_a_call_that_ran(self, workspace: Path) -> None:
        payload = {"tool_name": SAVE, "tool_input": _summary_input("1.00"), "tool_response": {}, "tool_use_id": "t"}
        _run("post-tool-use", payload)
        assert [(entry["outcome"], entry["tool"]) for entry in self._entries(workspace)] == [("ran", SAVE)]

    def test_records_a_denied_call(self, workspace: Path) -> None:
        _run("pre-tool-use", {"tool_name": SAVE, "tool_input": _summary_input("500.00")})
        assert self._entries(workspace)[0]["outcome"] == "denied"


class TestStop:
    def test_lets_an_ordinary_session_finish(self) -> None:
        assert _run("stop", {"stop_hook_active": False}).stdout == ""

    def test_sends_back_a_run_with_tags_but_no_summary(self) -> None:
        tag_subscription("Viewly", ["T03"])
        output = json.loads(_run("stop", {"stop_hook_active": False}).stdout)
        assert output["decision"] == "block"
        assert "save_summary" in output["reason"]

    def test_lets_a_finished_run_finish(self) -> None:
        tag_subscription("Viewly", ["T03"])
        save_summary([], Decimal("0.00"))
        assert _run("stop", {"stop_hook_active": False}).stdout == ""

    def test_does_not_send_back_twice(self) -> None:
        tag_subscription("Viewly", ["T03"])
        assert _run("stop", {"stop_hook_active": True}).stdout == ""


class TestSettingsWiring:
    def _commands(self, event: str) -> list[str]:
        return [hook["command"] for group in SETTINGS["hooks"][event] for hook in group["hooks"]]

    def test_each_event_runs_its_own_handler(self) -> None:
        assert any(command.endswith("subfinder.lib.hooks pre-tool-use") for command in self._commands("PreToolUse"))
        assert any(command.endswith("subfinder.lib.hooks post-tool-use") for command in self._commands("PostToolUse"))
        assert any(command.endswith("subfinder.lib.hooks stop") for command in self._commands("Stop"))

    def test_the_matchers_name_real_tools(self) -> None:
        tools = {tool.name for tool in anyio.run(build_server().list_tools)}
        group = next(group for group in SETTINGS["hooks"]["PreToolUse"] if "mcp__subfinder" in group["matcher"])
        assert {name.removeprefix("mcp__subfinder__") for name in group["matcher"].split("|")} <= tools

    def test_every_write_tool_has_a_check_in_front_of_it(self) -> None:
        group = next(group for group in SETTINGS["hooks"]["PreToolUse"] if "mcp__subfinder" in group["matcher"])
        assert set(group["matcher"].split("|")) == {SAVE, TAG}

    def test_a_broken_check_blocks_instead_of_letting_the_write_through(self) -> None:
        group = next(group for group in SETTINGS["hooks"]["PreToolUse"] if "mcp__subfinder" in group["matcher"])
        assert group["hooks"][0]["onFailure"] == "block"

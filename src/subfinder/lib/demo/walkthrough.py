"""The free walkthrough: every type doing its real job, in the order a run uses them.

Nothing is simulated except the model. The MCP server is a real subprocess, each hook is a real process fed the JSON
Claude Code sends, and the connector's server answers over real HTTP on this machine. It stops at the first result that
is not what it should be, so it doubles as an end-to-end check.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from decimal import Decimal
from typing import Any

import anyio
from mcp import Client, StdioServerParameters

from subfinder.lib.api.scripted import ScriptedCleaner
from subfinder.lib.connector.request import build_request
from subfinder.lib.connector.server import build_app, serving_in_background
from subfinder.lib.demo.project_files import (
    read_frontmatter,
    rule_applies_to,
    rule_files,
    skill_files,
    subfolder_instruction_files,
)
from subfinder.lib.shared.settings import REPO_ROOT, workspace_dir
from subfinder.lib.statement.recurring import Recurring, find_recurring
from subfinder.lib.statement.transactions import STATEMENT
from subfinder.lib.statement.workbook import load_workbook

_SAMPLE_FILE = "src/subfinder/lib/statement/recurring.py"
_TOOL = "mcp__subfinder__{}"


def _heading(text: str) -> None:
    print(f"\n=== {text}")


def _expect(condition: bool, what: str) -> None:
    """Say a result is right, or stop the walkthrough."""
    if not condition:
        raise RuntimeError(f"Expected: {what}")
    print(f"  ok: {what}")


def _show_rules() -> None:
    _heading("RULES: context Claude Code loads, which asks but does not enforce")
    for rule in rule_files():
        name = rule.relative_to(REPO_ROOT).as_posix()
        scope = "matching files only" if read_frontmatter(rule)[0].get("paths") else "every session"
        print(f"  {name}: loads for {scope}")
    money, advice = rule_files()
    _expect(rule_applies_to(money, _SAMPLE_FILE), f"money.md loads for {_SAMPLE_FILE}")
    _expect(not rule_applies_to(money, "README.md"), "money.md stays out of context for README.md")
    _expect(rule_applies_to(advice, "README.md"), "no-advice.md loads everywhere")
    print("  CLAUDE.md at the root loads at launch. Each of these loads only when its folder is touched:")
    subfolder_files = subfolder_instruction_files()
    for path in subfolder_files:
        print(f"    {path.relative_to(REPO_ROOT).as_posix()}")
    _expect(bool(subfolder_files), "the repo shows a subfolder CLAUDE.md")


def _show_skill() -> None:
    _heading("SKILL: a procedure that loads only when it is used")
    skill = skill_files()[0]
    header, body = read_frontmatter(skill)
    print(f"  /{header['name']}")
    print(f"  Always in context: {len(header['description'])} characters of description")
    print(f"  Loaded on use: {len(body)} characters of steps, and summary-format.md if it is read")
    _expect(len(header["description"]) < len(body), "the part always in context is the smaller part")


def _clean_with_scripted_model() -> list[Recurring]:
    _heading("API: one Messages API call cleans the names (scripted here: `subfinder run` calls Claude)")
    descriptions = sorted({line.description for line in STATEMENT.transactions})
    lines = ScriptedCleaner().clean(descriptions).lines
    print(f"  {len(STATEMENT.transactions)} statement lines, {len(descriptions)} different descriptions")
    for line in lines:
        if line.merchant == "Viewly":
            print(f"  {line.description!r} -> {line.merchant} ({line.category})")
    recurring = find_recurring(STATEMENT.transactions, lines)
    print("  Then plain arithmetic, no model:")
    for item in recurring:
        state = f"{item.monthly_cost} a month" if item.active else "ended"
        rise = f", up {item.price_rise}" if item.price_rise else ""
        print(f"    {item.merchant}: {state}{rise}")
    _expect([item.merchant for item in recurring if not item.active] == ["NewsDaily"], "NewsDaily is seen as ended")
    return [item for item in recurring if item.active]


def _call_stdio_server(calls: list[tuple[str, dict[str, Any]]]) -> list[str]:
    """Launch the real MCP server, make the calls, and give back its tool names. Any: tool arguments are JSON."""

    async def main() -> list[str]:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "subfinder.lib.mcp_server"],
            env=dict(os.environ),
        )
        async with Client(parameters) as client:
            for tool, arguments in calls:
                result = await client.call_tool(tool, arguments)
                if result.is_error:
                    raise RuntimeError(f"{tool} failed: {result.content}")
            return [tool.name for tool in (await client.list_tools()).tools]

    return anyio.run(main)


def _tag_over_mcp(active: list[Recurring]) -> None:
    _heading("MCP: the tools, reached by a real client over stdio")
    calls = [
        ("tag_subscription", {"merchant": item.merchant, "transaction_ids": item.transaction_ids}) for item in active
    ]
    tools = _call_stdio_server(calls)
    print(f"  The server offers: {', '.join(tools)}")
    print(f"  Claude Code sees each one as {_TOOL.format('<tool>')}")
    _expect(len(load_workbook().tags) == len(active), f"{len(active)} subscriptions tagged, in a file on disk")


def _run_hook(event: str, payload: dict[str, Any]) -> str:
    """Run a hook the way Claude Code does: a new process with JSON on stdin. Any: event payloads are JSON."""
    message = json.dumps({"session_id": "demo", "cwd": str(REPO_ROOT), "hook_event_name": event, **payload})
    result = subprocess.run(
        [sys.executable, "-m", "subfinder.lib.hooks", event],
        input=message,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ.copy(),
        check=True,
    )
    return result.stdout


def _summary_arguments(active: list[Recurring], extra: Decimal = Decimal("0.00")) -> dict[str, Any]:
    """The arguments of a save_summary call. With `extra`, its first line overclaims. Any: tool arguments are JSON."""
    savings = [item.monthly_cost + (extra if index == 0 else 0) for index, item in enumerate(active)]
    lines = [
        {"merchant": item.merchant, "monthly_saving": f"{saving:.2f}", "note": "Note."}
        for item, saving in zip(active, savings, strict=True)
    ]
    return {"lines": lines, "total_monthly_saving": f"{sum(savings):.2f}"}


def _save_through_hooks(active: list[Recurring]) -> None:
    _heading("HOOKS: code that runs at fixed points, whatever the model decides")
    save = _TOOL.format("save_summary")

    stopping_early = json.loads(_run_hook("stop", {"stop_hook_active": False}))
    print(f"  Stop, tags but no summary: {stopping_early['decision']}")
    _expect(stopping_early["decision"] == "block", "a half-done run is sent back to finish")

    overclaim = _summary_arguments(active, extra=Decimal("500.00"))
    denied = json.loads(_run_hook("pre-tool-use", {"tool_name": save, "tool_input": overclaim}))["hookSpecificOutput"]
    print(f"  PreToolUse, saving overstated by 500.00: {denied['permissionDecision']}")
    print(f"    Reason the model reads: {denied['permissionDecisionReason']}")
    _expect(denied["permissionDecision"] == "deny", "a saving above the latest charge never reaches the tool")

    honest = _summary_arguments(active)
    _expect(_run_hook("pre-tool-use", {"tool_name": save, "tool_input": honest}) == "", "the honest summary passes")
    _call_stdio_server([("save_summary", honest)])
    _run_hook("post-tool-use", {"tool_name": save, "tool_input": honest, "tool_response": {}})

    audit = (workspace_dir() / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    outcomes = [json.loads(line)["outcome"] for line in audit]
    print(f"  PostToolUse, audit log: {outcomes}")
    _expect(outcomes == ["denied", "ran"], "the audit log has the refused call and the one that ran")
    _expect(_run_hook("stop", {"stop_hook_active": False}) == "", "the finished run may stop")


def _read_over_connector() -> None:
    _heading("CONNECTOR: the same tools as a remote server, reached from Anthropic's cloud")

    async def read(url: str) -> tuple[set[str], object]:
        async with Client(url) as client:
            tools = {tool.name for tool in (await client.list_tools()).tools}
            return tools, (await client.call_tool("get_summary", {})).structured_content

    with serving_in_background(build_app(None, None)) as url:
        tools, summary = anyio.run(read, url)
    print(f"  Over HTTP the server offers: {', '.join(sorted(tools))}")
    print("  A connector call skips your hooks and your code, so it gets no tool that writes.")
    _expect("save_summary" not in tools and "tag_subscription" not in tools, "no write tool over HTTP")
    _expect(
        isinstance(summary, dict) and summary["result"]["total_monthly_saving"] == "506.00",
        "the summary reads back",
    )

    request = build_request("https://your-public-host.example/mcp", "your-token", "What did the run find?")
    print("  The Messages API request has two halves:")
    print(f"    mcp_servers: {json.dumps(request['mcp_servers'])}")
    enabled = list(request["tools"][0]["configs"])
    print(f"    tools: an mcp_toolset that enables only {enabled}")


def _show_result() -> None:
    _heading("RESULT")
    summary = load_workbook().summary
    if summary is None:
        raise RuntimeError("Expected a saved summary")
    for line in summary.lines:
        print(f"  {line.merchant:<12} {line.monthly_saving:>8} a month")
    print(f"  {'Total':<12} {summary.total_monthly_saving:>8} DKK a month if all were cancelled")
    print("\nEvery type did its job, and nothing here called the paid API.")


def run_walkthrough() -> None:
    """Run every step in a throwaway workspace, so the demo never touches a real run."""
    with tempfile.TemporaryDirectory() as folder:
        os.environ["SUBFINDER_WORKSPACE"] = folder
        _show_rules()
        _show_skill()
        active = _clean_with_scripted_model()
        _tag_over_mcp(active)
        _save_through_hooks(active)
        _read_over_connector()
        _show_result()

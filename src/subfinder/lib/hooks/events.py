"""What runs on each hook event: JSON from Claude Code in, a decision out.

Claude Code starts a new process for every event, gives it the event as JSON on stdin, and reads the answer from stdout.
`.claude/settings.json` says which event runs which command. See https://code.claude.com/docs/en/hooks.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ValidationError

from subfinder.lib.hooks.checks import Decision, check_summary, check_tag
from subfinder.lib.shared.settings import Strict, audit_log_path, config_for
from subfinder.lib.statement.transactions import STATEMENT
from subfinder.lib.statement.workbook import Summary, Tag, load_workbook


class _Config(Strict):
    tool_prefix: str
    stop_reason: str


CONFIG = config_for(__name__, _Config)


class _ToolEvent(BaseModel):
    """The fields of a tool event that matter here. Claude Code sends more, and may add others, so they are ignored."""

    tool_name: str
    # Any: arguments differ per tool. They are parsed into a typed model before use, in _check_call.
    tool_input: dict[str, Any]


class _StopEvent(BaseModel):
    """The field of a Stop event that matters here."""

    stop_hook_active: bool = False


def _check_call(event: _ToolEvent) -> Decision:
    """Run the check for a tool. A tool with no check is allowed, and arguments that do not parse are denied."""
    tool = event.tool_name.removeprefix(CONFIG.tool_prefix)
    try:
        if tool == "tag_subscription":
            return check_tag(Tag.model_validate(event.tool_input), load_workbook().tags, STATEMENT)
        if tool == "save_summary":
            return check_summary(Summary.model_validate(event.tool_input), load_workbook().tags, STATEMENT)
    except ValidationError as error:
        return Decision(allowed=False, reason=f"The arguments are not valid: {error}")
    return Decision(allowed=True)


def _audit(outcome: str, event: _ToolEvent) -> None:
    """Add one line to the audit log. The model cannot skip it, because it does not run this."""
    entry = {
        "time": datetime.now(UTC).isoformat(timespec="seconds"),
        "outcome": outcome,
        "tool": event.tool_name,
        "input": event.tool_input,
    }
    path = audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")


def _deny(reason: str) -> str:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }
    return json.dumps(output)


def on_pre_tool_use(raw: str) -> str:
    """Before a tool runs: deny it if its check fails. No output lets the normal permission rules decide.

    Anything unreadable is denied. This hook stands between the model and a write, so it fails closed.
    """
    try:
        event = _ToolEvent.model_validate_json(raw)
    except ValidationError as error:
        return _deny(f"The hook could not read this event: {error}")
    decision = _check_call(event)
    if decision.allowed:
        return ""
    _audit("denied", event)
    return _deny(decision.reason)


def on_post_tool_use(raw: str) -> str:
    """After a tool has run: record it. The tool has already happened, so this hook cannot stop anything."""
    _audit("ran", _ToolEvent.model_validate_json(raw))
    return ""


def on_stop(raw: str) -> str:
    """When the model wants to finish: send it back if the run is half done.

    A session with no tags is not a run, so ordinary work in this repo is never held up. `stop_hook_active` means this
    hook already sent the model back once, and asking again could loop forever.
    """
    if _StopEvent.model_validate_json(raw).stop_hook_active:
        return ""
    workbook = load_workbook()
    if workbook.tags and workbook.summary is None:
        return json.dumps({"decision": "block", "reason": CONFIG.stop_reason})
    return ""


EVENTS: dict[str, Callable[[str], str]] = {
    "pre-tool-use": on_pre_tool_use,
    "post-tool-use": on_post_tool_use,
    "stop": on_stop,
}

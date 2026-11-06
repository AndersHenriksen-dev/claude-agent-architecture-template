# 3. Hooks

## What a hook is

A hook is something Claude Code runs at a fixed point in its loop. The model does not choose it, does not see it unless it speaks, and cannot talk it out of anything. That is the whole reason to use one.

There are over 30 events. These three do most of the useful work:

| Event | When | What it can do |
|---|---|---|
| `PreToolUse` | Before a tool runs | Allow, deny, ask the user, or change the arguments |
| `PostToolUse` | After a tool ran | Log, or give the model feedback. It cannot undo the call |
| `Stop` | When the model wants to finish | Send it back to work |

## "Guard" is not a separate thing

You will see people say **guard** or **guardrail**. The Claude docs have no such type. In practice it means a check in code that can block something, and in Claude Code what runs that check is a hook. This repo keeps the two ideas apart in its files:

- **The check** decides. [checks.py](../../src/subfinder/lib/hooks/checks.py) has pure functions that know nothing about Claude Code.
- **The hook** decides when. [events.py](../../src/subfinder/lib/hooks/events.py) reads Claude Code's JSON and calls a check.

That split earns its keep: [the API path](05-the-api.md) has no hooks, so it calls the same check functions directly.

## The protocol

Hooks are wired in `.claude/settings.json`, in three levels: event, matcher, handler.

```json
"PreToolUse": [{
  "matcher": "mcp__subfinder__tag_subscription|mcp__subfinder__save_summary",
  "hooks": [{
    "type": "command",
    "command": "uv run --quiet --project \"$CLAUDE_PROJECT_DIR\" python -m subfinder.lib.hooks pre-tool-use",
    "timeout": 30,
    "onFailure": "block"
  }]
}]
```

Claude Code starts a **new process** for each event and writes JSON to its stdin:

```json
{
  "session_id": "abc123",
  "cwd": "/path/to/project",
  "hook_event_name": "PreToolUse",
  "tool_name": "mcp__subfinder__save_summary",
  "tool_input": { "lines": [], "total_monthly_saving": "506.00" }
}
```

It reads the answer from the exit code and stdout:

| Exit code | Meaning |
|---|---|
| 0 | Success. If stdout is a JSON object, its fields apply |
| 2 | Block, on events that can. Stderr is the reason |
| Other | A non-blocking error: the action goes ahead, unless `onFailure` is `block` |

To deny with a reason the model can act on:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Viewly: a saving of 500.00 is more than its latest charge of 119.00."
  }
}
```

## The three hooks here

**`PreToolUse`: check the write.** A tag must point at real outgoing lines. A summary line must name a tagged merchant and save no more than its latest charge, no merchant may appear twice, and the total must add up. All the problems go back in one reason, so the model can fix them in one try.

Because this hook stands in front of a write, it **fails closed**. An unreadable event or arguments that do not parse are denied. `onFailure: block` covers the hook not running at all, for example if `uv` is missing.

**`PostToolUse`: keep the record.** One line per call in `workspace/audit.jsonl`. `PreToolUse` also logs what it denies, so the log shows what the model tried as well as what ran. The model cannot skip this, because it does not run it.

**`Stop`: define done.** If a run has tags but no summary, it answers `{"decision": "block", "reason": "..."}` and the model keeps working. Two details matter:

- It does nothing in a session with no tags. This hook fires on every turn in the repo, including ordinary coding.
- It respects `stop_hook_active`, which is true when a Stop hook already sent the model back. Without that check, a condition that cannot be met would loop.

## How hooks fit with permissions

Claude Code checks a tool call in this order: hooks, deny rules, ask rules, permission mode, allow rules, then a prompt or callback.

- A hook's `deny` holds even in `bypassPermissions` mode.
- A hook's `allow` does **not** skip deny and ask rules.
- A hook that says nothing passes the call on, which is what this repo does for a good call.

## Settings files

Hooks and permission rules live in settings files, and those behave in the opposite way to `CLAUDE.md` files. Instruction files stack. Settings files override.

| Priority | File | Who it is for | In git? |
|---|---|---|---|
| Highest | Managed settings | Everyone in an organization | No |
| | `--settings` on the command line | This session | No |
| | `.claude/settings.local.json` | You, in this project | No |
| | `.claude/settings.json` | Everyone on the project | Yes |
| Lowest | `~/.claude/settings.json` | You, in every project | No |

- **A single value** comes from the highest level that sets it.
- **Lists combine.** `permissions.allow` adds up across files. A lower file can add to a list and cannot remove from it, and an `allow` in your local file does not cancel an `ask` in the shared one.
- **`settings.local.json` mostly writes itself.** Choosing "Yes, and don't ask again" saves an `allow` rule there, and Claude Code keeps the file out of git through your global excludes. If you make it by hand, add it to `.gitignore`.
- **Trust.** `deny` and `ask` rules in a shared file apply at once. Its `allow` rules wait until you trust the folder, so a cloned repo cannot pre-approve commands for you.

Put a hook that protects something in the shared file, as this repo does, so it runs for everyone. Put a personal convenience, such as a desktop notification, in your local or user file.

To see which files loaded, run `/status`.

## When not to use one

A hook is the wrong tool for anything needing judgement, such as "is this sentence financial advice?". That stays a [rule](02-rules-and-skills.md), or goes to a `prompt` hook, which asks a model and so gives up the guarantee. And remember a hook's reach: it runs in Claude Code and the Agent SDK, and nowhere else.

## Where to find this in the code

- The wiring: [settings.json](../../.claude/settings.json). What to remember when editing: [lib/hooks/CLAUDE.md](../../src/subfinder/lib/hooks/CLAUDE.md).
- The checks: `check_tag()` and `check_summary()` in [checks.py](../../src/subfinder/lib/hooks/checks.py).
- The events: `on_pre_tool_use()`, `on_post_tool_use()` and `on_stop()` in [events.py](../../src/subfinder/lib/hooks/events.py).
- The tests, which start a real process per event: [test_events.py](../../tests/hooks/test_events.py).

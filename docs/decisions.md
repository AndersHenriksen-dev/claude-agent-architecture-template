# Decisions

Why things are built the way they are.

## One idea that uses every type

Six small examples would show the syntax of each type and nothing about how they work together. One idea forces real questions, such as what a hook can do that a rule cannot, and what happens to your checks when a connector is involved. Finding subscriptions fits because each type has a job the others cannot do: messy text needs a model, money needs code, and the result is easy to judge. The data is made up, and no part of it comes from an employer.

## A hook is the guard

There is no "guard" type in the Claude docs. A check that blocks something is a hook doing its job, so the repo has six types, not seven. The check itself is a separate pure function, because the API path has no hooks and still needs it.

## Model for text, code for money

The model turns `TNBX*PREMIUM` into "Tunebox". It never adds up an amount in the API path, and in the Claude Code path every amount it writes is checked against the statement. A model is good at the first job and has no business being trusted with the second.

## The API path is one call, not an agent

Nothing in that job has to decide what to do next, so a loop would add cost and ways to fail with no gain. It shows the cheapest tier on purpose.

## The connector cannot write

A connector call goes from Anthropic's cloud straight to the server, so no hook sees it. Putting the checks in the server would work, and a real system that must write through a connector would do that. Here nothing needs to, so the write tools are simply not served. The request also allows the read tools by name. Either alone would be enough, and having both means one mistake does not expose a write.

## The connector server needs a token by default

It has to be public to be useful, so an open default would be a mistake waiting to happen. `--no-auth` exists because a claude.ai custom connector accepts either no authentication or OAuth, and OAuth would be more code than the rest of the connector. The data is made up, so that is fine for a demo. It would not be fine for real statements.

## `PreToolUse` fails closed, `PostToolUse` and `Stop` do not

`PreToolUse` stands between the model and a write, so an unreadable event is denied and `onFailure` is `block`. If the audit hook breaks, the tool has already run, and blocking the model would help nothing. If `Stop` blocked forever, a session could never end, so it honours `stop_hook_active`.

## `Stop` ignores a session with no tags

The hook runs at the end of every turn in this repo, including ordinary coding. It only acts on a half-done run, so nobody working on the code is sent back to save a summary.

## `reset` keeps the audit log

`subfinder reset` deletes the workbook and leaves `audit.jsonl`. An audit log is only worth having if the thing it records cannot wipe it, so it is append-only. Delete the file by hand to start a clean log.

## Hooks do not protect the stdio server from another client

The checks on writes run in Claude Code's hooks. Another MCP client on the same machine, or a session with hooks turned off, could call `save_summary` with no check. Here that risks one local file of made-up data, and a server that checks too would hide what a hook does. A real system that writes something that matters should also run the check inside the server, as with a connector.

## Classes hold data, functions do the work

Pydantic models check what comes in: config, tool arguments, and the model's answer. Inside, results are frozen dataclasses. The two cleaners are plain functions with one signature, not classes, because neither keeps state.

## Money crosses JSON as a string

A JSON number becomes a Python float, and 99.10 as a float is not 99.10. `Money` refuses floats and any string that is not an amount with two decimals, such as `1e5`, and its schema tells clients to send a string. So a bad value fails at the boundary instead of somewhere in the arithmetic.

## The workbook is a file

The MCP server and each hook are separate processes, and a hook process lives for milliseconds. A file is the simplest thing they can all read. A real system would use a database, and only `workbook.py` would change.

## Tests run real processes

The hooks and the MCP server are programs that another program starts, and tests that call their functions directly would miss how they fail. Starting the server as a subprocess found a real bug: under `python -m`, `__name__` is `__main__`, so `config_for` looked for the wrong file. That is why the launch lives in `__main__.py`. Only the model is replaced, because it costs money and cannot be asserted on.

## The demo is also a check

`subfinder demo` stops at the first wrong result and CI runs it. So what a stranger sees on a fresh clone is tested on every pull request.

## Sonnet by default

The paid example uses `claude-sonnet-5-5`, set in one YAML file and overridable with `SUBFINDER_MODEL`. Whoever runs it pays with their own key, and tests never call it.

## The refusal fallback is on

Every paid call sends `fallbacks: "default"`. It costs nothing unless a request is declined, and it uses the beta client. A list of merchant names should never be declined, but anyone copying this template for something else would want it.

## No sampling parameters, no forced tool choice

Current models reject `temperature`, `top_p`, `top_k` and a forced `tool_choice`. The tests assert they are not sent, so a change made from an old example fails here and not at the API.

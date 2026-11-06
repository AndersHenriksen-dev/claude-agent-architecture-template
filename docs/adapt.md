# Using this as a template

Click **Use this template** on GitHub, then replace the example with your own idea. Most of the change is in one folder and its matching config.

## What to change

1. **The domain.** Replace `src/subfinder/lib/statement/` and `src/subfinder/config/statement/`. Keep the split: data and pure functions in one place, and tools as plain functions in `tools.py`.
2. **The tools.** List your read and write tools in `lib/mcp_server/server.py`, with their descriptions in `config/mcp_server/server.yaml`.
3. **The checks.** Replace `lib/hooks/checks.py` with what must never happen in your domain. Update the matcher in `.claude/settings.json` so that every write tool has a check in front of it.
4. **The rules.** Rewrite `.claude/rules/`. Keep each file to one topic and scope it with `paths` where you can.
5. **The skill.** Rename `.claude/skills/find-subscriptions/` and rewrite its steps. The `name` must match the folder.
6. **The API call.** Change the output shape and prompt in `lib/api/clean_merchants.py` and its config, or delete the folder if nothing runs headless.
7. **The connector.** Decide what may be reached from outside. Delete `lib/connector/` if nothing may.
8. **The names.** Replace `subfinder` in `pyproject.toml`, `.mcp.json`, `.claude/settings.json`, `config/hooks/events.yaml` and the imports. The server key in `.mcp.json` is part of every `mcp__<server>__<tool>` name.

The tests in `tests/demo/` and `tests/hooks/test_events.py` check that this wiring still lines up, so they tell you what you missed.

## What to keep as it is

- `.claude/reference/`, `.claude/commands/`, `.claude/hooks/check_python_style_read.py`, `.pre-commit-config.yaml`, `.gitleaks.toml` and CI.
- `lib/shared/settings.py` and the mirrored `lib/` and `config/` folders.
- The demo idea: one free command that runs every part for real with only the model scripted.

## Questions to answer for your own project

- **What is the worst thing the model could write?** That is your first `PreToolUse` check.
- **What would you need to see afterwards to trust a run?** That is your `PostToolUse` log.
- **What does "finished" mean?** That is your `Stop` hook.
- **Which part needs judgement, and which part is arithmetic?** Only the first needs a model.
- **Who calls the tools from outside your machine?** Whatever they reach has no hooks around it.

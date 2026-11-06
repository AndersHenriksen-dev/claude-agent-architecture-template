# Hooks

Loaded only when you read or edit a file in this folder.

- `checks.py` holds pure functions. They must not read stdin, print, or know the shape of Claude Code's JSON, because `lib/api/run.py` calls them where no hook runs.
- `events.py` is the only file that knows Claude Code's JSON. A new check goes in `checks.py`, and only its wiring goes here.
- Claude Code reads a hook's stdout as its answer, so nothing else may print there. Keep `json.dumps` at its default ASCII output, so the Windows console encoding cannot change it.
- `on_pre_tool_use` fails closed: anything it cannot read is denied. `on_post_tool_use` and `on_stop` must never block on their own failure.

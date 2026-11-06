"""What Claude Code launches for a hook: `python -m subfinder.lib.hooks <event>`, with the event as JSON on stdin."""

from __future__ import annotations

import sys

from subfinder.lib.hooks.events import EVENTS

# utf-8-sig drops the byte order mark that PowerShell puts at the start of a pipe.
raw = sys.stdin.buffer.read().decode("utf-8-sig")
print(EVENTS[sys.argv[1]](raw), end="")

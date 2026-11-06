# CLAUDE.md

A template for agentic development with Claude. It holds one working example of each type (skill, hooks, rules, MCP, API, connector), all used by one small idea: finding subscriptions in a made-up bank statement. Write for a reader who has never seen it.

## Run things

```bash
uv sync                      # install
uv run pre-commit install    # once: ruff, mypy, line endings and gitleaks on every commit
uv run subfinder demo        # every type end to end with a scripted model: free, what CI runs
uv run subfinder reset       # forget the current run in workspace/
uv run subfinder run         # prints the plan; --yes makes one paid call: ask first
uv run subfinder connector-serve      # the read tools over HTTP on this machine
uv run subfinder connector-ask <url>  # prints the plan; --yes makes a paid call: ask first
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest   # what CI checks
```

## Index of `.claude/` and related files

| File | Read it when | What it covers |
|---|---|---|
| [.claude/reference/python-style.md](.claude/reference/python-style.md) | **Before writing or editing any `.py` file** | The single source of truth for Python here: PEP 8 via ruff, typing checked by mypy, Google-style docstrings, Pydantic models at boundaries, module structure, KISS/DRY/LEAN, comments, testing. |
| [.claude/reference/git-workflow.md](.claude/reference/git-workflow.md) | **Before creating a branch, a commit or a pull request** | Branch names, commit messages (`tag(scope): Header`, a body that says why), rebasing, pull request bodies, attribution. |
| [.claude/commands/commit-push-pr.md](.claude/commands/commit-push-pr.md) | Committing and opening a pull request | Command that runs the checks, commits, pushes and opens the pull request. |
| [.claude/rules/](.claude/rules/) | Changing what Claude is asked to follow | The example's rules. `money.md` loads for statement files, `no-advice.md` in every session. |
| [.claude/skills/find-subscriptions/](.claude/skills/find-subscriptions/SKILL.md) | Changing the procedure | The example's skill and its summary format. |
| [.mcp.json](.mcp.json) | Changing how the server starts | The MCP server. Its key is part of every `mcp__subfinder__<tool>` name. |
| [.claude/settings.json](.claude/settings.json) | Changing permissions or hooks | Allowed, asked and denied commands, and every hook. |
| [.claude/hooks/check_python_style_read.py](.claude/hooks/check_python_style_read.py) | Debugging why a Python edit was blocked | `PreToolUse` hook that blocks editing `.py` files until the style guide has been read in the session. |
| [.pre-commit-config.yaml](.pre-commit-config.yaml), [.github/workflows/ci.yml](.github/workflows/ci.yml) and [.gitleaks.toml](.gitleaks.toml) | Changing what runs on commit or in CI | The automatic half of the style guide, the demo and the secret scan. |
| [docs/types.md](docs/types.md) | Explaining or choosing a type | What each type is and when to use it. |
| [docs/decisions.md](docs/decisions.md) | Changing a design choice | Why things are built the way they are. |
| [docs/adapt.md](docs/adapt.md) | Starting another project from this one | What to change and what to keep. |
| [docs/learn/](docs/learn/README.md) | Learning or explaining how it works | Study guide: one chapter per type, one run traced, questions, exercises and reading. |

## Rules

- Synthetic data only. Names, merchants and amounts are made up. Nothing from Anders's current or past employers goes in this repo: no code, prompts, documents, internal names or data.
- Never commit keys or what a run writes: `.env` and `workspace/` are git-ignored. Never read `.env`.
- Tests and the demo never call the paid API. Run `run --yes` or `connector-ask --yes` only when asked, and say the number of calls, the model and the cost first.
- Every write tool has a check in `lib/hooks/checks.py` and a `PreToolUse` matcher in `.claude/settings.json`. The connector serves read tools only, because no hook sees its calls.
- A check is a pure function with no knowledge of Claude Code, so the run in `lib/api/run.py` can call the same one.
- Money is `Money` from `lib/statement/transactions.py`, never `float`.
- Prompts, tool descriptions, prices, limits and data go in `config/`, not in code. A Python file that needs config has one YAML file at the same path under `config/`, read with `config_for(__name__, ...)` and checked by a Pydantic model.
- A statement in `docs/types.md` or `docs/learn/` about how Claude works must match the current Claude docs. Check them when changing one, rather than relying on memory.
- When a type's behaviour changes, update the matching file in `docs/learn/`, including any numbers it quotes. Record design choices in `docs/decisions.md`.

## Attribution: the agent never credits itself

Anders is the only author of everything here: commits, pull request bodies, comments and docs. No `Co-Authored-By:` trailer naming a tool, agent or model, no "Generated with" line, and no text that says an AI tool built or helped with the work. Claude is what this repo teaches, so naming it as the subject is fine. Never override `user.name`, `user.email` or `--author`.

## Writing style (everything that is not Python)

- Never use em dashes anywhere: README, docs, comments, commit messages. Use commas, colons, full stops or parentheses.
- Plain English, short sentences, numbers instead of adjectives, no hype words. README in first person singular.
- Write about the code and the results as they are now, not about how they got there.
- Git: follow [.claude/reference/git-workflow.md](.claude/reference/git-workflow.md). Squash merge.

## Layout

```text
src/subfinder/
|-- cli.py                the entry point: reads the command line and hands over
|-- lib/
|   |-- statement/        the domain: swap this folder to use the template for something else
|   |   |-- transactions.py   the statement and the Money type
|   |   |-- recurring.py      finding subscriptions: arithmetic, no model
|   |   |-- workbook.py       a run's state, in a file because several processes share it
|   |   `-- tools.py          the tools, as plain functions
|   |-- hooks/
|   |   |-- checks.py     what may be written: pure functions
|   |   `-- events.py     what runs on each hook event
|   |-- mcp_server/       every tool, over stdio
|   |-- connector/
|   |   |-- server.py     the read tools over HTTP, with a token and a Host check
|   |   |-- request.py    the Messages API request that reaches them
|   |   `-- commands.py   the connector commands
|   |-- api/
|   |   |-- clean_merchants.py   the one Messages API call
|   |   |-- scripted.py   the correct answer by hand, in place of the model
|   |   |-- run.py        the whole job with no Claude Code
|   |   `-- commands.py   the run command
|   |-- demo/             the free walkthrough, and reading rule and skill files
|   `-- shared/           reading config files: imports nothing else here
`-- config/               the same subfolders as lib/
tests/                    the same subfolders again
workspace/                what a run writes: git-ignored
```

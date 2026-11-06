# CLAUDE.md

A template for agentic development with Claude. It holds one working example of each type (skill, hooks, rules, MCP, API, connector), all used by one small idea: finding subscriptions in a made-up bank statement. Write for a reader who has never seen it.

## Run things

```bash
uv sync                      # install
uv run pre-commit install    # once: ruff, mypy, line endings and gitleaks on every commit
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest   # what CI checks
```

## Index of `.claude/` and related files

| File | Read it when | What it covers |
|---|---|---|
| [.claude/reference/python-style.md](.claude/reference/python-style.md) | **Before writing or editing any `.py` file** | The single source of truth for Python here: PEP 8 via ruff, typing checked by mypy, Google-style docstrings, Pydantic models at boundaries, module structure, KISS/DRY/LEAN, comments, testing. |
| [.claude/reference/git-workflow.md](.claude/reference/git-workflow.md) | **Before creating a branch, a commit or a pull request** | Branch names, commit messages (`tag(scope): Header`, a body that says why), rebasing, pull request bodies, attribution. |
| [.claude/commands/commit-push-pr.md](.claude/commands/commit-push-pr.md) | Committing and opening a pull request | Command that runs the checks, commits, pushes and opens the pull request. |
| [.claude/hooks/check_python_style_read.py](.claude/hooks/check_python_style_read.py) | Debugging why a Python edit was blocked | `PreToolUse` hook that blocks editing `.py` files until the style guide has been read in the session. |
| [.claude/settings.json](.claude/settings.json) | Changing permissions or hooks | Allowed, asked and denied commands, and every hook. |
| [.pre-commit-config.yaml](.pre-commit-config.yaml), [.github/workflows/ci.yml](.github/workflows/ci.yml) and [.gitleaks.toml](.gitleaks.toml) | Changing what runs on commit or in CI | The automatic half of the style guide and the secret scan. |

## Rules

- Synthetic data only. Names, merchants and amounts are made up. Nothing from Anders's current or past employers goes in this repo: no code, prompts, documents, internal names or data.
- Never commit keys or what a run writes: `.env` and `workspace/` are git-ignored. Never read `.env`.
- Tests and the demo never call the paid API. Say the number of calls, the model and the cost before any command that does.
- Prompts, tool descriptions, prices, limits and data go in `config/`, not in code. A Python file that needs config has one YAML file at the same path under `config/`, read with `config_for(__name__, ...)` and checked by a Pydantic model.

## Attribution: the agent never credits itself

Anders is the only author of everything here: commits, pull request bodies, comments and docs. No `Co-Authored-By:` trailer naming a tool, agent or model, no "Generated with" line, and no text that says an AI tool built or helped with the work. Claude is what this repo teaches, so naming it as the subject is fine. Never override `user.name`, `user.email` or `--author`.

## Writing style (everything that is not Python)

- Never use em dashes anywhere: README, docs, comments, commit messages. Use commas, colons, full stops or parentheses.
- Plain English, short sentences, numbers instead of adjectives, no hype words. README in first person singular.
- Write about the code and the results as they are now, not about how they got there.
- Git: follow [.claude/reference/git-workflow.md](.claude/reference/git-workflow.md). Squash merge.

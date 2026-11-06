# The six types

Agentic development with Claude uses six kinds of building block. They overlap, so the hard part is knowing which one a job belongs to. This page says what each one is, when to pick it over the others, and how this repo's example uses it. Checked against the Claude docs on 2026-11-06.

## Choosing in one minute

Ask these in order. Stop at the first yes.

1. **Must this happen every time, whatever the model decides?** Use a **hook**.
2. **Is it a fact or a habit Claude should keep in mind while working?** Use a **rule**.
3. **Is it a procedure Claude should follow for one kind of task?** Use a **skill**.
4. **Does Claude need to reach data or actions outside itself?** Use **MCP**.
5. **Will those tools be used from somewhere other than this machine, such as claude.ai or a server?** Use a **connector**.
6. **Is there no person and no Claude Code around, or does your own program decide what happens next?** Use the **API**.

| Type | Lives in | Who decides it runs | Can it stop the model? | Context it costs |
|---|---|---|---|---|
| Rule | `.claude/rules/*.md`, `CLAUDE.md` | Claude Code loads it; the model chooses whether to follow it | No | All of it, once loaded |
| Skill | `.claude/skills/<name>/SKILL.md` | You or the model | No | The description always, the body when used |
| Hook | `.claude/settings.json` | Claude Code, at a fixed event | Yes | None, unless it speaks |
| MCP | `.mcp.json` and a server program | The model picks a tool | The server can refuse | The tool list |
| Connector | A public HTTP server, and a request or a claude.ai setting | The model picks a tool | The server can refuse | The tool list |
| API | Your own program | Your code | Your code decides everything | Only what you send |

The line that matters most runs between the first two rows and the third. The memory docs say Claude treats these files "as context, not enforced configuration". A rule asks. A hook enforces.

## Rule

**What it is.** Markdown that Claude Code loads into context. A file in `.claude/rules/` with no frontmatter loads at launch, like `CLAUDE.md`. One with a `paths` field loads when Claude reads or edits a matching file.

**Pick it over the others when** the content is a fact or a standard Claude should keep in mind while it does other things. Not a skill, because it has no steps and no moment when it starts. Not a hook, because a wrong outcome is cheap or a program cannot judge it.

**In the example.** [money.md](../.claude/rules/money.md) loads only for statement code: use `Decimal`, a negative amount is money out, keep the data made up. [no-advice.md](../.claude/rules/no-advice.md) loads in every session, because no code can judge whether a sentence gives financial advice. The part of the money rule a machine can check also has a test, in [test_project_files.py](../tests/demo/test_project_files.py).

## Skill

**What it is.** A folder with a `SKILL.md`: frontmatter with a `name` and `description`, then instructions. The description is always in context and the body loads when the skill is used. Supporting files cost nothing until they are read.

**Pick it over the others when** you keep pasting the same procedure, or a section of `CLAUDE.md` has turned into steps. Not a rule, because a rule's whole text is in context whether or not today's task needs it. Not a hook, because a skill can only guide the model.

**In the example.** [find-subscriptions](../.claude/skills/find-subscriptions/SKILL.md) is the procedure for one run. Its `allowed-tools` pre-approves the five tools for that turn. It does not limit them: that takes `disallowed-tools`.

**Worth knowing.** Custom skills do not sync across surfaces. A skill in `.claude/skills/` is not available on claude.ai or through the API until you upload it there.

## Hook

**What it is.** A command, HTTP call, prompt or subagent that Claude Code runs at a fixed event, such as `PreToolUse`, `PostToolUse` or `Stop`. A command hook gets the event as JSON on stdin and answers on stdout or through its exit code. The model has no say.

Some people call a blocking hook a **guard** or a guardrail. The Claude docs do not use that word for it. Here the *check* is a plain Python function, and the *hook* is what runs it at the right moment.

**Pick it over the others when** the thing must happen every time. Anything you would be upset to see skipped belongs here: blocking a write, keeping an audit log, refusing to stop before the work is done.

**In the example.** [settings.json](../.claude/settings.json) wires three events to [events.py](../src/subfinder/lib/hooks/events.py):

- `PreToolUse` runs the [checks](../src/subfinder/lib/hooks/checks.py). It denies a tag of a charge that is not on the statement, and a summary that claims more than the latest charge. It fails closed.
- `PostToolUse` writes the audit log.
- `Stop` sends the model back if a run has tags but no summary.

**Worth knowing.** A hook that returns `allow` does not skip your deny and ask rules. A hook that returns `deny` holds even in `bypassPermissions` mode. Hooks run only inside Claude Code and the Agent SDK.

## MCP

**What it is.** The Model Context Protocol: a standard way to offer tools to any client. A server program lists its tools and runs them. `.mcp.json` tells Claude Code how to start one, and each tool appears as `mcp__<server>__<tool>`.

**Pick it over the others when** Claude needs real data or real actions, and you want more than one client to use them. Not a skill, because a skill can only tell Claude what to do with tools it already has. Not a connector, while the client runs on the same machine as the data.

**In the example.** [server.py](../src/subfinder/lib/mcp_server/server.py) serves five tools over stdio: three that read and two that write. The tools themselves are plain functions in [tools.py](../src/subfinder/lib/statement/tools.py).

## Connector

**What it is.** The word means one thing in two products: **a remote MCP server reached over public HTTP from Anthropic's cloud**.

- In the Messages API, the **MCP connector** is the beta `mcp_servers` parameter with a matching `mcp_toolset` in `tools`.
- In claude.ai, a **connector** is a remote MCP server added under Settings > Connectors. It then also works in the desktop and mobile apps.

The server speaks ordinary MCP. What changes is who calls it and from where: a local stdio server cannot be reached this way.

**Pick it over MCP over stdio when** the client is not on your machine: someone asking from claude.ai, or a program that wants the API to call the tools for it.

**In the example.** [connector/server.py](../src/subfinder/lib/connector/server.py) serves only the three read tools. This is the design point of the whole type: **a connector call goes from Anthropic's cloud straight to your server, so your hooks and your own code never see it.** A check you want on a connector must live inside the server. Here the simpler answer is that nothing written goes through it. [request.py](../src/subfinder/lib/connector/request.py) also allows only those three tools by name, so one mistake is not enough to expose a write.

## API

**What it is.** Your own program calling `POST /v1/messages` through the Anthropic SDK. You choose the model, the prompt and the output shape, and nothing else is loaded: no rules, no skills, no hooks.

**Pick it over the others when** no person and no Claude Code are there, such as a nightly job, or when your code should decide what happens next. Start with one call. The docs' advice is to use the simplest tier that works, and an agent loop is only worth it when the steps cannot be known in advance.

**In the example.** [clean_merchants.py](../src/subfinder/lib/api/clean_merchants.py) makes one structured-output call that turns messy descriptions such as `TNBX*PREMIUM` into a clean merchant and a category. [run.py](../src/subfinder/lib/api/run.py) does the rest as arithmetic. No hook runs here, so that code calls the same checks itself.

## How they fit in one run

```text
             always in context               loaded when used
             ----------------                ----------------
             rules, CLAUDE.md                SKILL.md
                     \                         /
                      v                       v
                     [ the model in Claude Code ]
                                  |
                       wants to call a tool
                                  |
                       PreToolUse hook -----> denied: the model reads why
                                  | allowed
                                  v
                    MCP server over stdio  <-- all five tools
                                  |
                       PostToolUse hook -----> audit log
                                  |
                       wants to finish
                                  |
                       Stop hook ---------> no summary yet: back to work


[ your program ] --- Messages API ---> [ the model ]      no Claude Code, so your code
       |                                                  calls the same checks itself
       `-- the same checks, the same tools

[ claude.ai or the API ] --- Anthropic's cloud ---> connector over HTTP    three read
                                                                           tools, no hooks
```

## What is not here

- **Agent SDK.** Claude Code as a library. It loads the same `.claude/` folder, so these rules, skills, hooks and MCP servers work unchanged. Use it when you want Claude Code's built-in tools and loop inside your own program.
- **Managed Agents.** Anthropic runs the loop and a sandbox for you. Skills and connectors carry over. Hooks do not, because they run inside Claude Code.
- **Subagents and plugins.** A subagent is a helper with its own context, and a plugin packages the types above for sharing. Neither is a new kind of capability.

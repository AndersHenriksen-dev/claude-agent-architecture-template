# Claude agent architecture template

[![CI](https://github.com/AndersHenriksen-dev/claude-agent-architecture-template/actions/workflows/ci.yml/badge.svg)](https://github.com/AndersHenriksen-dev/claude-agent-architecture-template/actions/workflows/ci.yml)

Claude gives you six ways to build an agent: skills, hooks, rules, MCP, the API and connectors. They overlap, and the docs explain each one on its own page. I wanted to see them work together, so I built one small example that needs all six, and kept it as a template to start new projects from.

The example finds the subscriptions in a made-up bank statement. It is a good fit because the job splits cleanly: the bank writes one merchant as `TUNEBOX P2F3A1`, `TNBX*PREMIUM` and `TUNEBOX AB STHLM`, which needs a model to read. The money needs code, because a model should not be trusted to add up or to state a saving nobody checked.

## The six types

| Type | What it is | How the example uses it |
|---|---|---|
| **Rule** | Text Claude Code loads and asks the model to follow | [Decimal for money, loaded only for statement code](.claude/rules/money.md). [No financial advice, in every session](.claude/rules/no-advice.md) |
| **Skill** | A procedure that loads only when used | [`/find-subscriptions`](.claude/skills/find-subscriptions/SKILL.md): the steps and the format of the summary |
| **Hook** | Code Claude Code runs at a fixed moment, whatever the model wants | [Deny a saving above the latest charge, log every call, refuse to stop with no summary](src/subfinder/lib/hooks/events.py) |
| **MCP** | A standard way to offer tools to any client | [Five tools over stdio](src/subfinder/lib/mcp_server/server.py): three that read and two that write |
| **API** | Your program calling the model directly | [One structured call cleans the merchant names](src/subfinder/lib/api/clean_merchants.py), with no Claude Code around it |
| **Connector** | A remote MCP server, called from Anthropic's cloud | [The three read tools over HTTP](src/subfinder/lib/connector/server.py), so it can be asked from claude.ai or the API |

[docs/types.md](docs/types.md) says when to pick each one over the others. If you only read one page, read that one.

A "guard" is not a seventh type. The Claude docs do not have that term: it usually means a check that can block something, and in Claude Code a hook is what runs it. Here the [check](src/subfinder/lib/hooks/checks.py) is a plain function, so the API path can call the same one where no hook exists.

## What I learned

**A rule asks and a hook enforces, and only one of them can make a promise.** "Never overstate a saving" appears in the skill, in the tool's description and in a hook. Only the hook holds if the model gets it wrong.

**A connector goes around your hooks.** Its calls go from Anthropic's cloud straight to the server, so neither your hooks nor your own code see them. So the connector here has no tool that writes, and that is the design decision the whole type comes down to.

**Most of the job did not need an agent.** The API path is one model call followed by arithmetic. Keeping the model away from the amounts means a wrong answer can put a merchant in the wrong category, but it cannot invent a charge.

## Try it

You need [uv](https://docs.astral.sh/uv/). Tests and the demo need no API key and cost nothing.

```bash
git clone https://github.com/AndersHenriksen-dev/claude-agent-architecture-template.git
```

```bash
cd claude-agent-architecture-template
```

```bash
uv sync
```

```bash
uv run pytest
```

```bash
uv run subfinder demo
```

The demo runs every type for real, with only the model scripted: the MCP server as a subprocess, each hook as a process fed the JSON Claude Code sends, and the connector's server over HTTP on your machine. It stops at the first wrong result. CI runs it on every pull request. The end of its output:

```text
=== HOOKS: code that runs at fixed points, whatever the model decides
  Stop, tags but no summary: block
  ok: a half-done run is sent back to finish
  PreToolUse, saving overstated by 500.00: deny
    Reason the model reads: CloudVault: a saving of 529.00 is more than its latest charge of 29.00.
  ok: a saving above the latest charge never reaches the tool
  ...

=== RESULT
  CloudVault      29.00 a month
  FitZone        249.00 a month
  Tunebox        109.00 a month
  Viewly         119.00 a month
  Total          506.00 DKK a month if all were cancelled
```

## Use it with Claude

### In Claude Code

Open Claude Code in this folder, approve the `subfinder` MCP server when asked, and type:

```text
/find-subscriptions
```

The rules, the skill, the hooks and the server all load from the repo, as long as the session starts in this folder and not a parent of it. In a real session, the skill reached the right answer, `PostToolUse` logged every call, `PreToolUse` denied a saving of 999.00 on Viewly, and `Stop` sent back a run with no summary. To start again:

```bash
uv run subfinder reset
```

### Through the API (costs money)

Copy `.env.example` to `.env` and add your key. This makes one call on Claude Sonnet 5.5. Without `--yes` it only prints the plan.

```bash
uv run subfinder run --yes
```

It prints what it found and how many descriptions agree with the [hand-written answer](src/subfinder/config/api/scripted.yaml). When I ran it once, it used 1,118 input and 865 output tokens, which cost USD 0.0109. It found the same four subscriptions and the same 506.00 total, saw that NewsDaily had ended, and agreed on 20 of the 22 descriptions. To use another model, set `SUBFINDER_MODEL`.

### Through a connector (costs money)

Anthropic's cloud has to reach the server, so it needs a public URL. A tunnel gives you one. With [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/):

```bash
cloudflared tunnel --url http://127.0.0.1:8765
```

Set `SUBFINDER_CONNECTOR_TOKEN` in `.env`, then serve, using the host name the tunnel printed:

```bash
uv run subfinder connector-serve --public-host your-name.trycloudflare.com
```

Then ask, from another terminal:

```bash
uv run subfinder connector-ask https://your-name.trycloudflare.com/mcp --yes
```

To add it to claude.ai instead, serve with `--no-auth` and add the URL under Settings > Connectors. A custom connector there takes no authentication or OAuth, not a fixed token. Only do that with made-up data, and stop the tunnel when you are done.

## Start your own project from it

Click **Use this template**, then follow [docs/adapt.md](docs/adapt.md). Most of the change is in one folder. The tests check that the wiring still lines up, so they tell you what you missed.

## Learn more

- [docs/types.md](docs/types.md): what each type is and when to use it.
- [docs/learn/](docs/learn/README.md): a study guide with one chapter per type, one run traced from start to finish, self-test questions and exercises.
- [docs/decisions.md](docs/decisions.md): why it is built this way.

## Layout

```text
.mcp.json                      MCP: how Claude Code starts the server
.claude/
|-- rules/                     RULES
|-- skills/find-subscriptions/ SKILL
|-- settings.json              HOOKS: which event runs what
`-- reference/                 the style and git guides
src/subfinder/
|-- cli.py                     the entry point
|-- lib/
|   |-- statement/             the made-up data, tools and arithmetic (swap this)
|   |-- hooks/                 HOOKS: checks.py decides, events.py runs them
|   |-- mcp_server/            MCP: every tool over stdio
|   |-- connector/             CONNECTOR: read tools over HTTP, and the request
|   |-- api/                   API: the call, and the run with no Claude Code
|   |-- demo/                  the free walkthrough
|   `-- shared/                reading config files
`-- config/                    the same folders as lib/: prompts, prices, data
tests/                         the same folders again
docs/                          types.md, decisions.md, adapt.md, learn/
```

All data is made up: the person, the merchants and the amounts. MIT licence.

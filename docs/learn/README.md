# Learning guide

A study guide to the six building blocks of agentic development with Claude, and to what the code here actually does. Read the files in order once; afterwards each one works as a reference. Every file ends with where to find its ideas in the code.

| # | File | What it covers |
|---|---|---|
| 1 | [The six types](01-the-six-types.md) | The map: who decides what runs, what enforces and what only asks, and what each type costs in context |
| 2 | [Rules and skills](02-rules-and-skills.md) | How Claude Code loads instructions, and how to tell a fact from a procedure |
| 3 | [Hooks](03-hooks.md) | Events, the JSON on stdin and stdout, the three hooks here, and why a guard is a hook |
| 4 | [MCP](04-mcp.md) | What the protocol does, tools and their schemas, stdio, and how Claude Code names a tool |
| 5 | [The API](05-the-api.md) | One structured call instead of an agent, what the current models reject, and how to read an answer |
| 6 | [Connectors](06-connectors.md) | What the word means, the two halves of the request, and why your hooks never see the call |
| 7 | [One run, traced](07-one-run.md) | The whole example, step by step, in Claude Code and with no Claude Code |
| 8 | [Questions to test yourself](08-questions.md) | Short questions with answers, and exercises that change the code |
| 9 | [Further reading](09-further-reading.md) | The docs behind each idea |

The one idea to take away: **an instruction can be ignored, and a hook cannot, but a hook only runs where Claude Code runs.** So decide first what must always hold. Put that in code. Then ask of each path to your tools, including the API and connectors, what is still checking it.

To see all of it working, run this. It is free and needs no key.

```bash
uv run subfinder demo
```

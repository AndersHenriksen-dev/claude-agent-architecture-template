# 1. The six types

## The map

Everything an agent does comes down to two loops: the model decides, and something runs what it decided. The six types differ in where they sit relative to that.

| Type | One line |
|---|---|
| **Rule** | Text the model reads and is asked to follow |
| **Skill** | A procedure the model reads when the task calls for it |
| **Hook** | Code the harness runs at a fixed moment, whatever the model wants |
| **MCP** | A standard way to give the model tools |
| **Connector** | Those tools on a public server, called from Anthropic's cloud |
| **API** | Your program calling the model directly |

The **harness** is the program around the model. Here that is Claude Code: it loads files, offers tools, runs what the model asks for, and starts the next turn. The API has no harness unless you write one.

## Three questions that sort them

**1. Who decides that it runs?**

- The model: skills (usually), tools from MCP and connectors.
- The harness: rules (it loads them), hooks.
- Your code: the API.

**2. Does it enforce or only ask?**

Rules and skills are text. A model usually follows them, and on any given run it may not. A hook is a program outside the model. A server that refuses a call is also outside the model. Only things outside the model can promise anything.

**3. What does it cost in context?**

Every token in context is paid for on every turn, and long instructions get followed less well. So the types load differently:

- A rule with no `paths` costs its full length in every session.
- A rule with `paths` costs nothing until Claude touches a matching file.
- A skill costs its description until it is used.
- A hook costs nothing unless it says something back.
- A tool costs its name, description and schema once offered.

## How to choose

Ask in this order, and stop at the first yes:

1. Must it happen every time? **Hook.**
2. Is it a standing fact or habit? **Rule.**
3. Is it a procedure for one kind of task? **Skill.**
4. Does Claude need outside data or actions? **MCP.**
5. Are those used from off this machine? **Connector.**
6. Is there no Claude Code here, or does your code steer? **API.**

Most real features use several. In this repo, "never overstate a saving" is one idea spread over three types: the skill's format file explains it, the tool's description states it, and a hook enforces it. Only the last one holds if the model gets it wrong.

## Where each one works

| | Claude Code | Agent SDK | Messages API | claude.ai |
|---|---|---|---|---|
| Rules | Yes | Yes | No | No |
| Skills | Yes, from `.claude/skills/` | Yes, from `.claude/skills/` | Yes, uploaded, in a sandbox | Yes, uploaded |
| Hooks | Yes | Yes | No | No |
| MCP over stdio | Yes | Yes | No | No |
| Connector | Yes | Yes | Yes | Yes |

The empty cells are the reason [the API path](05-the-api.md) calls its checks itself and [the connector](06-connectors.md) cannot write.

## Where to find this in the code

- The one-page version of this file: [docs/types.md](../types.md).
- All six running in order: `run_walkthrough()` in [walkthrough.py](../../src/subfinder/lib/demo/walkthrough.py).

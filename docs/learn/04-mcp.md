# 4. MCP

## What it solves

Without a standard, every tool needs writing again for every client. The Model Context Protocol fixes that: a **server** lists what it can do, and any **client** can ask. Claude Code, the desktop app and other people's tools are all clients. The same server works for all of them.

A server can offer tools, resources and prompts. This repo uses tools, which is also the only part the Messages API's connector supports.

## A tool

A tool has a name, a description and a JSON schema for its arguments. The model picks one by reading those, so the description is a prompt: write it for the model, including how to call the tool correctly. The descriptions here live in [server.yaml](../../src/subfinder/config/mcp_server/server.yaml).

With the Python SDK, the schema comes from the function's types:

```python
def get_merchant(name: str) -> list[Transaction]:
    """The lines whose raw description contains a name, ignoring case, spaces and punctuation."""
```

**Read tools carry a hint.** `read_only_hint=True` tells clients the tool changes nothing, and Claude Code's plan mode treats those differently. It is a hint from the server, not a guarantee to anyone.

## Transports

| Transport | How it runs | Who can reach it |
|---|---|---|
| **stdio** | The client starts the server as a child process and talks over stdin and stdout | Only that client, on that machine |
| **Streamable HTTP** | The server runs on its own and takes requests | Anyone who can reach the URL |

stdio is the simple default for local tools: no ports, no login, and the server stops with the client. HTTP is for sharing, which is what makes a [connector](06-connectors.md) possible.

A stdio server must keep stdout for the protocol alone, so anything it logs goes to stderr. A stray `print` breaks the connection.

## In Claude Code

`.mcp.json` at the project root declares a server for everyone who clones the repo:

```json
{
  "mcpServers": {
    "subfinder": {
      "command": "uv",
      "args": ["run", "--quiet", "python", "-m", "subfinder.lib.mcp_server"]
    }
  }
}
```

Project servers need approval the first time, because a cloned repo should not start programs on its own. Each tool then appears to the model as `mcp__<server>__<tool>`:

```text
mcp__subfinder__get_merchant
```

The server key in `.mcp.json` is part of that name, and the name is what `settings.json` matches on. Rename the server and your hooks and permissions silently stop matching, which is why a test here checks that the matchers name real tools.

## Keep the tools plain

The tools in this repo are ordinary Python functions in [tools.py](../../src/subfinder/lib/statement/tools.py). The server only decides who may reach them. So the logic can be tested with no protocol at all, and [the connector](06-connectors.md) can serve a subset of them by adding only those.

## Money over JSON

JSON has one number type, and it arrives in Python as a `float`. So `Money` crosses the wire as a string such as `"99.00"`. Its schema tells the client to send a string, and it refuses a float if one arrives anyway. Validating at the boundary means the rest of the code can trust what it has.

## Where to find this in the code

- The server: `build_server()` and `add_read_tools()` in [server.py](../../src/subfinder/lib/mcp_server/server.py).
- The launch: [`__main__.py`](../../src/subfinder/lib/mcp_server/__main__.py), kept separate because under `python -m` a module's `__name__` is `__main__`, and `config_for` depends on the real one.
- The money type: `Money` in [transactions.py](../../src/subfinder/lib/statement/transactions.py).
- The tests, which run the real server as a subprocess: [test_server.py](../../tests/mcp_server/test_server.py).

# 6. Connectors

## What the word means

A connector is **a remote MCP server, reached over public HTTP from Anthropic's cloud**. You will meet the word in two products, and it means the same in both:

| Where | How you set it up |
|---|---|
| **Messages API** | The beta "MCP connector": `mcp_servers` plus a matching `mcp_toolset` in `tools` |
| **claude.ai** | Settings > Connectors > add a custom connector, or pick one from the directory. It then also works in the desktop and mobile apps |

Claude Code can use connectors too. They are the same infrastructure as any other MCP server.

The server itself is ordinary MCP. It is the difference in who calls it that changes everything.

## The difference from local MCP

```text
Local MCP
  [ Claude Code on your machine ] -- hooks run here --> [ server, as a child process ]

Connector
  [ your program or claude.ai ] --> [ Anthropic's cloud ] --> [ your server, over the internet ]
                                                         no hook, none of your code
```

This has three results that shape the design:

1. **The server must be public.** A local stdio server cannot be connected. The API needs a URL it can reach, over Streamable HTTP or SSE.
2. **Your hooks do not run.** Neither does your own loop. In the API response, the calls show up as `mcp_tool_use` and `mcp_tool_result` blocks, after they have already happened. You find out what happened. You do not get asked.
3. **Authentication is your job.** Anyone with the URL can try it.

## So where do the checks go?

If a check must hold on a connector, it has to live **inside the server**, because that is the only code in the path. You have two honest choices:

- **Serve only what is safe.** This repo's choice: three read tools, no writes.
- **Check inside the server.** The right choice when a connector really must write.

The write tools here stay on the stdio server, where the hooks are.

## The two halves of the request

The API requires both, and rejects one alone:

```python
client.beta.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=16000,
    messages=[{"role": "user", "content": "Which subscriptions are on the statement?"}],
    mcp_servers=[
        {
            "type": "url",
            "url": "https://your-host.example/mcp",
            "name": "subfinder",
            "authorization_token": "...",
        }
    ],
    tools=[
        {
            "type": "mcp_toolset",
            "mcp_server_name": "subfinder",
            "default_config": {"enabled": False},
            "configs": {"list_transactions": {"enabled": True}, "get_merchant": {"enabled": True}},
        }
    ],
    betas=["mcp-client-2025-11-20"],
)
```

`default_config` with `enabled: False`, plus named tools in `configs`, is an allowlist. Tools the server adds later stay off.

**Defence in two places.** The server offers only read tools, and the request allows only those by name. Either would do. With both, one mistake does not expose a write.

**A paused turn.** With server-side tools, the response can stop with `stop_reason: "pause_turn"`. You send its content back unchanged and it carries on. `ask()` does this up to a limit.

## Securing the server

`build_app()` adds two protections:

- **A bearer token**, required unless you pass `--no-auth`. A wrong or missing token gets a 401 before anything else runs. The API sends it from `authorization_token`.
- **A Host check**, from the MCP library, against DNS rebinding: a trick that makes a browser send requests to a server on your own machine. The server only answers to the host names it was told about, so a tunnel's name must be passed with `--public-host`.

**claude.ai is different.** Custom connectors there accept either no authentication or OAuth, not a fixed token. So `--no-auth` exists for that demo, and it is fine only because the data is made up.

## Trying it for real

Testing this needs a public URL, so the tests stop at localhost. To go further you need a tunnel, such as `cloudflared`. The README has the steps, and the API call costs money.

## Where to find this in the code

- The server: `build_read_only_server()` and `build_app()` in [server.py](../../src/subfinder/lib/connector/server.py).
- The request: `build_request()` and `ask()` in [request.py](../../src/subfinder/lib/connector/request.py).
- The tests over real HTTP: [test_server.py](../../tests/connector/test_server.py) and the request's shape in [test_request.py](../../tests/connector/test_request.py).

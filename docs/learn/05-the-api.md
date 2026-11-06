# 5. The API

## When you are on your own

The Messages API is one endpoint: send a model, some messages and options, and get an answer. Nothing is loaded for you, so there are no rules, skills or hooks unless your code provides them. That is the cost, and it is also the point: you control everything, and it runs anywhere your code runs.

## Pick the smallest thing that works

| Tier | What it is | Use it when |
|---|---|---|
| **One call** | One request, one answer | The input and the output are both known |
| **Workflow** | Your code chains calls | The steps are known |
| **Agent** | A loop where the model chooses the next step | The steps cannot be known in advance |

Cleaning merchant names is the first tier. The input is a list of strings and the output is a fixed shape. A loop would add cost and more ways to fail, and gain nothing.

So in this repo the model does only the part that needs judgement, and code does the rest:

```text
"TNBX*PREMIUM"  --model-->  Tunebox, subscription  --arithmetic-->  109.00 a month
```

## The call

```python
response = client.beta.messages.parse(
    model="claude-sonnet-5-5",
    max_tokens=16000,
    system=CONFIG.system,
    messages=[{"role": "user", "content": json.dumps(descriptions)}],
    output_format=CleanedLines,
    output_config={"effort": "low"},
    betas=["server-side-fallback-2026-07-01"],
    fallbacks="default",
)
```

Line by line, what matters:

- **`output_format`** takes a Pydantic model, and the API guarantees the answer fits its schema. The result is on `response.parsed_output`.
- **The schema fixes the shape, not the content.** The answer can fit perfectly and still leave a line out. `_check_every_line_came_back()` covers that.
- **`effort`** is the control for how hard the model works. Classification over short strings does well at `low`.
- **The data goes in the user message and the instructions in `system`.** The system prompt also says lines are data, because a bank description is text from outside.
- **`fallbacks="default"`** re-runs a declined request on another model, for free unless it happens. It needs the matching beta header.

## What current models reject

Older examples break on these. The tests assert none is sent:

| Old pattern | Now |
|---|---|
| `temperature`, `top_p`, `top_k` | 400 error on current models |
| `thinking: {type: "enabled", budget_tokens: N}` | 400 error. Thinking is adaptive, and `effort` controls it |
| `tool_choice` set to `any` or a named tool | 400 error on Opus 5.5 and Sonnet 5.5. Use `auto` with `strict: true`, or structured output |
| A prefilled last assistant message | 400 error. Use structured output |

## Reading an answer

**Check `stop_reason` first.** A refusal is a normal HTTP 200, with `stop_reason: "refusal"`. Reading `content` without checking gets you an empty answer that looks like a bug somewhere else.

| `stop_reason` | Meaning | What to do |
|---|---|---|
| `end_turn` | Finished | Read the answer |
| `refusal` | Declined | Handle it. Do not retry unchanged |
| `max_tokens` | Cut off | Raise the limit |
| `tool_use` | Wants a tool | Run it and send the result |
| `pause_turn` | A server tool paused | Send the content back unchanged |

## Checks with no hooks

No Claude Code means no hooks. If a rule must hold here, your code has to apply it, so [run.py](../../src/subfinder/lib/api/run.py) calls the same `check_tag()` and `check_summary()` that the hook calls. Pure check functions are what make that a single line, not a rewrite. A refused write raises an error, and nothing further is saved.

## Testing without paying

The client is a boundary. Tests replace it with a stand-in and check two things: the request has the right shape, and each kind of answer is read correctly. For runs from end to end, `ScriptedCleaner` answers from a hand-written file, and a paid run is compared with that same file, which gives a simple score.

## Where to find this in the code

- The call: `ClaudeCleaner.clean()` in [clean_merchants.py](../../src/subfinder/lib/api/clean_merchants.py), and its prompt in [clean_merchants.yaml](../../src/subfinder/config/api/clean_merchants.yaml).
- The run with no Claude Code: `find_and_save()` in [run.py](../../src/subfinder/lib/api/run.py).
- The arithmetic: `find_recurring()` in [recurring.py](../../src/subfinder/lib/statement/recurring.py).
- The correct answer by hand: [scripted.yaml](../../src/subfinder/config/api/scripted.yaml).

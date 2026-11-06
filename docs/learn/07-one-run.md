# 7. One run, traced

## The statement

35 lines over three months for a made-up person, in DKK. It is built to contain the hard cases:

| What | Why it is there |
|---|---|
| `TUNEBOX P2F3A1`, `TNBX*PREMIUM`, `TUNEBOX AB STHLM` | One merchant, written three ways. Exact matching fails |
| Viewly goes 99.00, 99.00, 119.00 | A price rise, and the saving is the latest charge |
| NewsDaily stops after September | A subscription that has already ended, so it saves nothing |
| Rent and the phone bill | They recur, but they are not subscriptions |
| Groceries | They repeat, with amounts that vary |
| The salary | It recurs, and it is money in |

The right answer is four active subscriptions, worth 506.00 a month: CloudVault 29.00, FitZone 249.00, Tunebox 109.00 and Viewly 119.00.

## In Claude Code

You type `/find-subscriptions`, or ask "what subscriptions do I have?".

1. **At launch.** Claude Code reads `CLAUDE.md` and `no-advice.md`. It lists the skill's description. It starts the MCP server, after you have approved it, and offers its tools.
2. **The skill loads.** The body of `SKILL.md` enters context, and its `allowed-tools` pre-approves the five tools for that turn.
3. **Read.** The model calls `mcp__subfinder__list_transactions`. No `PreToolUse` check applies. `PostToolUse` logs it.
4. **Think.** The model groups the lines by what they mean. This is the part that needs a model.
5. **Tag.** It calls `tag_subscription` for each active merchant. `PreToolUse` runs `check_tag()`: every id must be real and outgoing. Each tag goes in `workspace/workbook.json`, and `PostToolUse` logs it.
6. **Try to stop early (if it does).** The `Stop` hook sees tags and no summary, answers `block`, and the model goes back to work.
7. **Save.** It reads `summary-format.md` if it needs to, and calls `save_summary`. `PreToolUse` runs `check_summary()`.
8. **If it overclaims,** the call never runs. The model reads the reason:

   ```text
   Viewly: a saving of 500.00 is more than its latest charge of 119.00.
   ```

   It fixes the call and tries again. The audit log keeps the refused attempt.

9. **Finish.** `Stop` sees a saved summary and says nothing. The model reports to you, following `no-advice.md`, which asks it not to tell you what to cancel.

Every type did something a different type could not:

| Type | What only it could do here |
|---|---|
| Rule | Set a standard no code can judge (no advice) |
| Skill | Bring in the procedure only when asked |
| Hook | Refuse the overclaim, whatever the model believed |
| MCP | Give the model the statement and a way to write |

## With no Claude Code

`uv run subfinder run --yes` does the same job from a plain program.

1. **Collect.** `find_and_save()` takes the 22 different descriptions.
2. **One API call.** `ClaudeCleaner` sends them and gets back a merchant and a category for each.
3. **Arithmetic.** `find_recurring()` keeps outgoing charges in the `subscription` category, in at least 2 different months. It takes the latest charge as the cost, measures any rise, and marks a merchant active if it charged in the last month.
4. **Check and save.** `tag_checked()` and `save_checked()` call the same checks as the hook. A refusal raises an error.

The model never touches an amount. A wrong category can make the result wrong, but it cannot invent a charge.

## From outside

Later, someone asks "what did the run find?" through a connector. Anthropic's cloud calls `get_summary` on the HTTP server, which reads the same workbook. There is no `tag_subscription` or `save_summary` to call, so there is nothing for the missing hooks to have stopped.

## Where to find this in the code

- The demo, which runs these steps for real with only the model scripted: [walkthrough.py](../../src/subfinder/lib/demo/walkthrough.py).
- The statement: [transactions.yaml](../../src/subfinder/config/statement/transactions.yaml).
- The state shared between processes: [workbook.py](../../src/subfinder/lib/statement/workbook.py).

---
name: find-subscriptions
description: Find the subscriptions on the bank statement, spot price rises and ended subscriptions, and save a summary of what cancelling each would save. Use when asked about subscriptions, recurring charges or monthly costs on the statement.
allowed-tools: mcp__subfinder__list_transactions mcp__subfinder__get_merchant mcp__subfinder__get_summary mcp__subfinder__tag_subscription mcp__subfinder__save_summary
---

# Find subscriptions

The statement comes from the `subfinder` MCP server. It writes the same merchant differently from month to month, so judge by what a line means and not by its exact text.

1. Call `list_transactions` and read every line.
2. Group the lines by real merchant. Where you are unsure two spellings are the same merchant, call `get_merchant` and compare dates and amounts.
3. Decide which merchants are subscriptions: a service charged about monthly, in at least two different months, that the account holder could cancel. Rent, utilities, phone bills, groceries, travel and income are not subscriptions.
4. Call `tag_subscription` once for each subscription that is still active: it charged in the statement's last month. Give it one clean merchant name and the ids of all its charges.
5. Call `save_summary` once, in the format in [summary-format.md](summary-format.md).
6. Tell the user what you found: each subscription, its monthly cost, any price rise, any subscription that has already ended, and the total. Add a one-line reminder that the choice to cancel is theirs.

A hook checks each write against the statement. If a call is denied, read the reason, fix the call and try again. Do not work around it.

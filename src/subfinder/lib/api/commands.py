"""The `run` command: the whole job with a real model. It prints its plan and stops unless told to spend money."""

from __future__ import annotations

import anthropic
from dotenv import load_dotenv

from subfinder.lib.api.clean_merchants import ClaudeCleaner
from subfinder.lib.api.run import RunResult, find_and_save
from subfinder.lib.api.scripted import CONFIG as REFERENCE
from subfinder.lib.api.scripted import count_agreeing
from subfinder.lib.shared.settings import SETTINGS, model_from_env


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """What a call cost, or None for a model with no price in the config."""
    price = SETTINGS.prices.get(model)
    if price is None:
        return None
    return (input_tokens * price.input + output_tokens * price.output) / 1_000_000


def _print_result(result: RunResult) -> None:
    for item in result.recurring:
        state = f"{item.monthly_cost} a month" if item.active else "ended"
        rise = f", up {item.price_rise}" if item.price_rise else ""
        print(f"  {item.merchant}: {state}{rise}")
    print(f"Total if all active ones were cancelled: {result.summary.total_monthly_saving} DKK a month")
    agreeing = count_agreeing(result.cleaning.lines)
    print(f"Agreement with the hand-written answer: {agreeing} of {len(REFERENCE.lines)} descriptions")


def cmd_run(yes: bool) -> int:
    """Clean the names with Claude, then find and save the subscriptions.

    Args:
        yes: Whether to make the paid call. Without it, this only prints the plan.

    Returns:
        The exit code.
    """
    model = model_from_env()
    print(f"Plan: 1 Messages API call on {model}, roughly 1,000 input and 1,500 output tokens.")
    if not yes:
        print("That costs money, so nothing was sent. Add --yes to run it. `subfinder demo` is free.")
        return 0
    load_dotenv()
    result = find_and_save(ClaudeCleaner(anthropic.Anthropic()))
    _print_result(result)
    tokens = result.cleaning
    cost = cost_usd(model, tokens.input_tokens, tokens.output_tokens)
    spent = f"USD {cost:.4f}" if cost is not None else "cost unknown"
    print(f"Tokens: {tokens.input_tokens} in, {tokens.output_tokens} out ({spent}).")
    return 0

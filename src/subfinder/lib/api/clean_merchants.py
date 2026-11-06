"""The one call to the Messages API: turn messy statement descriptions into clean merchants and categories.

This is the part of the job a model is good at and code is not. It is one request with a fixed output shape, not an
agent: nothing here chooses what to do next. Everything after it is arithmetic.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import anthropic

from subfinder.lib.shared.settings import Strict, config_for, model_from_env
from subfinder.lib.statement.recurring import CleanedLine


class _Config(Strict):
    effort: Literal["low", "medium", "high", "xhigh", "max"]
    max_tokens: int
    betas: list[str]
    fallbacks: Literal["default"]
    system: str


CONFIG = config_for(__name__, _Config)


class CleanedLines(Strict):
    """The shape the model must answer in. Structured output makes the API enforce it."""

    lines: list[CleanedLine]


@dataclass(frozen=True)
class Cleaning:
    """What a cleaner produced, and the tokens it spent. The hand-written answer spends none."""

    lines: list[CleanedLine]
    input_tokens: int = 0
    output_tokens: int = 0


MerchantCleaner = Callable[[list[str]], Cleaning]
"""Anything that can clean descriptions: Claude, or the hand-written answer in the demo and the tests."""


def _check_every_line_came_back(descriptions: list[str], lines: list[CleanedLine]) -> None:
    """The schema fixes the shape of the answer, not its content, so this checks that the content is complete."""
    answered = {line.description for line in lines}
    missing = sorted(set(descriptions) - answered)
    if missing:
        raise ValueError(f"The model did not clean these lines: {missing}")


def clean_with_claude(client: anthropic.Anthropic, descriptions: list[str]) -> Cleaning:
    """Send every description in one request. This costs money.

    Args:
        client: The API client. Tests pass a stand-in, because the model is a boundary they must not cross.
        descriptions: The raw statement descriptions.

    Returns:
        A clean merchant and category for each description, and the tokens spent.

    Raises:
        ValueError: If the model refused, or left out a line.
    """
    response = client.beta.messages.parse(
        model=model_from_env(),
        max_tokens=CONFIG.max_tokens,
        system=CONFIG.system,
        messages=[{"role": "user", "content": json.dumps(descriptions, indent=0)}],
        output_format=CleanedLines,
        output_config={"effort": CONFIG.effort},
        betas=CONFIG.betas,
        fallbacks=CONFIG.fallbacks,
    )
    # A refusal is a normal HTTP 200, so it has to be checked for before reading the answer.
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise ValueError(f"The model gave no usable answer (stop_reason: {response.stop_reason}).")
    lines = response.parsed_output.lines
    _check_every_line_came_back(descriptions, lines)
    return Cleaning(
        lines=lines,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )

"""A whole run with no Claude Code: clean the names, do the arithmetic, check, save.

Hooks only exist inside Claude Code. Here nothing would run them, so this code calls the same checks itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from subfinder.lib.api.clean_merchants import Cleaning, MerchantCleaner
from subfinder.lib.hooks.checks import Decision, check_summary, check_tag
from subfinder.lib.statement.recurring import RULES, Recurring, find_recurring
from subfinder.lib.statement.tools import save_summary, tag_subscription
from subfinder.lib.statement.transactions import STATEMENT
from subfinder.lib.statement.workbook import Summary, SummaryLine, Tag, load_workbook, reset_workbook


@dataclass(frozen=True)
class RunResult:
    """What a run found."""

    cleaning: Cleaning
    recurring: list[Recurring]
    summary: Summary


def _require(decision: Decision) -> None:
    if not decision.allowed:
        raise ValueError(f"A check refused this write: {decision.reason}")


def tag_checked(tag: Tag) -> None:
    """Save a tag if its check passes."""
    _require(check_tag(tag, load_workbook().tags, STATEMENT))
    tag_subscription(tag.merchant, tag.transaction_ids)


def save_checked(summary: Summary) -> None:
    """Save a summary if its check passes."""
    _require(check_summary(summary, load_workbook().tags, STATEMENT))
    save_summary(summary.lines, summary.total_monthly_saving)


def build_summary(active: list[Recurring]) -> Summary:
    """One line per active subscription, saving its latest charge."""
    lines = [
        SummaryLine(
            merchant=item.merchant,
            monthly_saving=item.monthly_cost,
            note=f"Rose by {item.price_rise:.2f} during the statement." if item.price_rise else "Price unchanged.",
        )
        for item in active
    ]
    total = sum((line.monthly_saving for line in lines), Decimal("0.00"))
    return Summary(lines=lines, total_monthly_saving=total)


def find_and_save(clean: MerchantCleaner) -> RunResult:
    """Run the whole job once, starting from an empty workbook.

    Args:
        clean: Claude for a paid run, or the hand-written answer for a free one.

    Returns:
        The cleaning, every subscription found, and the summary that was saved.

    Raises:
        ValueError: If a check refuses a write. Nothing further is written.
    """
    reset_workbook()
    descriptions = sorted({line.description for line in STATEMENT.transactions})
    cleaning = clean(descriptions)
    recurring = find_recurring(STATEMENT.transactions, cleaning.lines, RULES)
    active = [item for item in recurring if item.active]
    for item in active:
        tag_checked(Tag(merchant=item.merchant, transaction_ids=item.transaction_ids))
    summary = build_summary(active)
    save_checked(summary)
    return RunResult(cleaning=cleaning, recurring=recurring, summary=summary)

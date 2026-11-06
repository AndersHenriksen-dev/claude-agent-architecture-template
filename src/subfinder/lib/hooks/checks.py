"""The checks that decide, in code, whether a write may run. Some people call a check like this a guard.

They are pure functions that know nothing about Claude Code: the hook runner in `events.py` calls them when the model
works through Claude Code, and the run in `lib/api/run.py` calls the same ones when no Claude Code is there.
"""

from __future__ import annotations

from decimal import Decimal

from subfinder.lib.shared.settings import Strict
from subfinder.lib.statement.transactions import Statement, Transaction
from subfinder.lib.statement.workbook import Summary, SummaryLine, Tag


class Decision(Strict):
    """Whether a call may run. A refusal carries the reason the model is shown, so it can fix the call."""

    allowed: bool
    reason: str = ""


def _decide(problems: list[str]) -> Decision:
    return Decision(allowed=not problems, reason=" ".join(problems))


def check_tag(tag: Tag, statement: Statement) -> Decision:
    """Refuse a tag whose charges are not real outgoing lines on the statement.

    Args:
        tag: The tag the model asked to save.
        statement: The bank statement the charges must come from.

    Returns:
        An allowed decision, or a denied one that names each bad id.
    """
    lines = {line.id: line for line in statement.transactions}
    problems = [f"{id_} is not on the statement." for id_ in tag.transaction_ids if id_ not in lines]
    problems += [
        f"{id_} is money in, not a charge." for id_ in tag.transaction_ids if id_ in lines and lines[id_].amount >= 0
    ]
    if not tag.transaction_ids:
        problems.append(f"{tag.merchant} has no charges.")
    return _decide(problems)


def _latest_charge(tag: Tag, lines: dict[str, Transaction]) -> Decimal:
    """The most recent charge behind a tag, as a positive amount: the most that cancelling can save per month."""
    charges = [lines[id_] for id_ in tag.transaction_ids if id_ in lines]
    return -max(charges, key=lambda charge: charge.date).amount if charges else Decimal("0.00")


def _check_line(line: SummaryLine, tags: dict[str, Tag], lines: dict[str, Transaction]) -> list[str]:
    if line.merchant not in tags:
        return [f"{line.merchant} is not tagged as a subscription."]
    latest = _latest_charge(tags[line.merchant], lines)
    if line.monthly_saving > latest:
        return [f"{line.merchant}: a saving of {line.monthly_saving} is more than its latest charge of {latest}."]
    return []


def check_summary(summary: Summary, tags: list[Tag], statement: Statement) -> Decision:
    """Refuse a summary that claims more than the statement can back up.

    Args:
        summary: The summary the model asked to save.
        tags: The subscriptions tagged so far.
        statement: The bank statement the claims are checked against.

    Returns:
        An allowed decision, or a denied one that names every problem at once.
    """
    by_merchant = {tag.merchant: tag for tag in tags}
    lines = {line.id: line for line in statement.transactions}
    problems = [problem for line in summary.lines for problem in _check_line(line, by_merchant, lines)]

    merchants = [line.merchant for line in summary.lines]
    if len(merchants) != len(set(merchants)):
        problems.append("A merchant appears more than once, which counts its saving twice.")

    total = sum((line.monthly_saving for line in summary.lines), Decimal("0.00"))
    if summary.total_monthly_saving != total:
        problems.append(f"The total is {summary.total_monthly_saving}, but the lines add up to {total}.")
    return _decide(problems)

"""The checks that decide, in code, whether a write may run. Some people call a check like this a guard.

They are pure functions that know nothing about Claude Code: the hook runner in `events.py` calls them when the model
works through Claude Code, and the run in `lib/api/run.py` calls the same ones when no Claude Code is there.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from subfinder.lib.statement.transactions import Statement, Transaction
from subfinder.lib.statement.workbook import Summary, SummaryLine, Tag


@dataclass(frozen=True)
class Decision:
    """Whether a call may run. A refusal carries the reason the model is shown, so it can fix the call."""

    allowed: bool
    reason: str = ""


def _decide(problems: list[str]) -> Decision:
    return Decision(allowed=not problems, reason=" ".join(problems))


def _month(charge: Transaction) -> tuple[int, int]:
    return charge.date.year, charge.date.month


def _find_tagged_elsewhere(tag: Tag, tags: list[Tag]) -> list[str]:
    """Charges that already belong to another merchant. Counting one twice would double the saving."""
    others = {id_ for other in tags if other.merchant != tag.merchant for id_ in other.transaction_ids}
    return [f"{id_} is already tagged under another merchant." for id_ in tag.transaction_ids if id_ in others]


def check_tag(tag: Tag, tags: list[Tag], statement: Statement) -> Decision:
    """Refuse a tag whose charges are not real, outgoing and its own.

    Args:
        tag: The tag the model asked to save.
        tags: The subscriptions tagged so far.
        statement: The bank statement the charges must come from.

    Returns:
        An allowed decision, or a denied one that names each bad id.
    """
    lines = {line.id: line for line in statement.transactions}
    problems = [f"{id_} is not on the statement." for id_ in tag.transaction_ids if id_ not in lines]
    problems += [
        f"{id_} is money in, not a charge." for id_ in tag.transaction_ids if id_ in lines and lines[id_].amount >= 0
    ]
    problems += _find_tagged_elsewhere(tag, tags)
    if len(tag.transaction_ids) != len(set(tag.transaction_ids)):
        problems.append(f"{tag.merchant} lists the same charge twice.")
    if not tag.transaction_ids:
        problems.append(f"{tag.merchant} has no charges.")
    return _decide(problems)


def _check_line(
    line: SummaryLine,
    tags: dict[str, Tag],
    lines: dict[str, Transaction],
    last_month: tuple[int, int],
) -> list[str]:
    """Check one saving against the charges behind it: it can be neither negative nor more than cancelling saves."""
    if line.merchant not in tags:
        return [f"{line.merchant} is not tagged as a subscription."]
    if line.monthly_saving < 0:
        return [f"{line.merchant}: a saving cannot be negative."]
    charges = [lines[id_] for id_ in tags[line.merchant].transaction_ids if id_ in lines]
    latest = max(charges, key=lambda charge: charge.date, default=None)
    if latest is None:
        return [f"{line.merchant} has no charges on the statement."]
    if _month(latest) != last_month and line.monthly_saving > 0:
        return [f"{line.merchant} has already ended, so cancelling it saves nothing."]
    charge = -latest.amount
    if line.monthly_saving > charge:
        return [f"{line.merchant}: a saving of {line.monthly_saving} is more than its latest charge of {charge}."]
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
    last_month = max(_month(line) for line in statement.transactions)
    problems = [problem for line in summary.lines for problem in _check_line(line, by_merchant, lines, last_month)]

    merchants = [line.merchant for line in summary.lines]
    if len(merchants) != len(set(merchants)):
        problems.append("A merchant appears more than once, which counts its saving twice.")

    total = sum((line.monthly_saving for line in summary.lines), Decimal("0.00"))
    if summary.total_monthly_saving != total:
        problems.append(f"The total is {summary.total_monthly_saving}, but the lines add up to {total}.")
    return _decide(problems)

"""Working out which merchants charge every month. No model here: once names are clean, this is arithmetic."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Literal

from subfinder.lib.shared.settings import Strict, config_for
from subfinder.lib.statement.transactions import Money, Transaction

Category = Literal["subscription", "housing", "bill", "groceries", "income", "other"]


class CleanedLine(Strict):
    """What one raw statement description means."""

    description: str
    merchant: str
    category: Category


class Recurring(Strict):
    """A subscription found on the statement."""

    merchant: str
    transaction_ids: list[str]
    monthly_cost: Money
    price_rise: Money
    active: bool


class _Config(Strict):
    min_months: int


CONFIG = config_for(__name__, _Config)


def _month(transaction: Transaction) -> tuple[int, int]:
    return transaction.date.year, transaction.date.month


def _summarize(merchant: str, charges: list[Transaction], last_month: tuple[int, int]) -> Recurring:
    """Describe one merchant's charges: what it costs now, how much that rose, and whether it still runs."""
    in_order = sorted(charges, key=lambda charge: charge.date)
    first, latest = -in_order[0].amount, -in_order[-1].amount
    return Recurring(
        merchant=merchant,
        transaction_ids=[charge.id for charge in in_order],
        monthly_cost=latest,
        price_rise=max(latest - first, Decimal("0.00")),
        active=_month(in_order[-1]) == last_month,
    )


def find_recurring(transactions: list[Transaction], cleaned: list[CleanedLine]) -> list[Recurring]:
    """Find the subscriptions: outgoing charges in the subscription category, in enough different months.

    Rent also recurs, and groceries also repeat. Their category keeps them out, which is why the names and categories
    have to be cleaned first.

    Args:
        transactions: The statement's lines.
        cleaned: What each raw description means. Every description on the statement must be here.

    Returns:
        One entry per subscription, sorted by merchant name.
    """
    by_description = {line.description: line for line in cleaned}
    charges_by_merchant: dict[str, list[Transaction]] = defaultdict(list)
    for transaction in transactions:
        line = by_description[transaction.description]
        if transaction.amount < 0 and line.category == "subscription":
            charges_by_merchant[line.merchant].append(transaction)

    last_month = max(_month(transaction) for transaction in transactions)
    return [
        _summarize(merchant, charges, last_month)
        for merchant, charges in sorted(charges_by_merchant.items())
        if len({_month(charge) for charge in charges}) >= CONFIG.min_months
    ]

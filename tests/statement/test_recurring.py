"""Finding subscriptions once names are clean."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from subfinder.lib.statement.recurring import CleanedLine, find_recurring
from subfinder.lib.statement.transactions import Transaction


def _charge(id_: str, month: int, description: str, amount: str) -> Transaction:
    return Transaction(id=id_, date=date(2026, month, 5), description=description, amount=Decimal(amount))


TRANSACTIONS = [
    _charge("A1", 8, "VIEWLY.COM", "-99.00"),
    _charge("A2", 9, "VIEWLY *M", "-99.00"),
    _charge("A3", 10, "VIEWLY.COM", "-119.00"),
    _charge("B1", 8, "NEWS", "-79.00"),
    _charge("B2", 9, "NEWS", "-79.00"),
    _charge("C1", 8, "ONCE", "-10.00"),
    _charge("D1", 8, "RENT", "-7800.00"),
    _charge("D2", 9, "RENT", "-7800.00"),
    _charge("E1", 8, "REFUND", "20.00"),
    _charge("E2", 9, "REFUND", "20.00"),
]
CLEANED = [
    CleanedLine(description="VIEWLY.COM", merchant="Viewly", category="subscription"),
    CleanedLine(description="VIEWLY *M", merchant="Viewly", category="subscription"),
    CleanedLine(description="NEWS", merchant="NewsDaily", category="subscription"),
    CleanedLine(description="ONCE", merchant="Once", category="subscription"),
    CleanedLine(description="RENT", merchant="Rent", category="housing"),
    CleanedLine(description="REFUND", merchant="Refund", category="subscription"),
]


def test_different_descriptions_join_under_one_merchant() -> None:
    found = {item.merchant: item for item in find_recurring(TRANSACTIONS, CLEANED)}
    assert found["Viewly"].transaction_ids == ["A1", "A2", "A3"]


def test_cost_is_the_latest_charge_and_the_rise_is_measured() -> None:
    viewly = next(item for item in find_recurring(TRANSACTIONS, CLEANED) if item.merchant == "Viewly")
    assert viewly.monthly_cost == Decimal("119.00")
    assert viewly.price_rise == Decimal("20.00")


def test_a_subscription_that_stopped_is_not_active() -> None:
    news = next(item for item in find_recurring(TRANSACTIONS, CLEANED) if item.merchant == "NewsDaily")
    assert news.active is False


def test_leaves_out_one_offs_other_categories_and_money_in() -> None:
    assert {item.merchant for item in find_recurring(TRANSACTIONS, CLEANED)} == {"NewsDaily", "Viewly"}

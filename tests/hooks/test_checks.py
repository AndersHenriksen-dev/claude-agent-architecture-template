"""The checks: what may be written, whatever the model believes."""

from __future__ import annotations

from decimal import Decimal

from subfinder.lib.hooks.checks import check_summary, check_tag
from subfinder.lib.statement.transactions import STATEMENT
from subfinder.lib.statement.workbook import Summary, SummaryLine, Tag

VIEWLY = Tag(merchant="Viewly", transaction_ids=["T03", "T16", "T28"])
TUNEBOX = Tag(merchant="Tunebox", transaction_ids=["T05", "T18", "T30"])


def _summary(*lines: tuple[str, str], total: str) -> Summary:
    return Summary(
        lines=[
            SummaryLine(merchant=merchant, monthly_saving=Decimal(saving), note="Note.") for merchant, saving in lines
        ],
        total_monthly_saving=Decimal(total),
    )


class TestCheckTag:
    def test_allows_real_charges(self) -> None:
        assert check_tag(VIEWLY, STATEMENT).allowed

    def test_denies_an_id_that_is_not_on_the_statement(self) -> None:
        decision = check_tag(Tag(merchant="Ghost", transaction_ids=["T99"]), STATEMENT)
        assert not decision.allowed
        assert "T99" in decision.reason

    def test_denies_money_in(self) -> None:
        decision = check_tag(Tag(merchant="Salary", transaction_ids=["T13"]), STATEMENT)
        assert not decision.allowed
        assert "money in" in decision.reason

    def test_denies_a_tag_with_no_charges(self) -> None:
        assert not check_tag(Tag(merchant="Empty", transaction_ids=[]), STATEMENT).allowed


class TestCheckSummary:
    def test_allows_a_saving_equal_to_the_latest_charge(self) -> None:
        summary = _summary(("Viewly", "119.00"), ("Tunebox", "109.00"), total="228.00")
        assert check_summary(summary, [VIEWLY, TUNEBOX], STATEMENT).allowed

    def test_uses_the_latest_charge_after_a_price_rise(self) -> None:
        assert check_summary(_summary(("Viewly", "119.00"), total="119.00"), [VIEWLY], STATEMENT).allowed

    def test_denies_a_saving_above_the_latest_charge(self) -> None:
        decision = check_summary(_summary(("Viewly", "120.00"), total="120.00"), [VIEWLY], STATEMENT)
        assert not decision.allowed
        assert "more than its latest charge of 119.00" in decision.reason

    def test_denies_a_merchant_that_was_not_tagged(self) -> None:
        decision = check_summary(_summary(("Rent", "1.00"), total="1.00"), [VIEWLY], STATEMENT)
        assert not decision.allowed
        assert "not tagged" in decision.reason

    def test_denies_a_wrong_total(self) -> None:
        decision = check_summary(_summary(("Viewly", "119.00"), total="500.00"), [VIEWLY], STATEMENT)
        assert not decision.allowed
        assert "add up to 119.00" in decision.reason

    def test_denies_a_merchant_counted_twice(self) -> None:
        summary = _summary(("Viewly", "119.00"), ("Viewly", "119.00"), total="238.00")
        assert not check_summary(summary, [VIEWLY], STATEMENT).allowed

    def test_names_every_problem_at_once(self) -> None:
        decision = check_summary(_summary(("Viewly", "999.00"), total="1.00"), [VIEWLY], STATEMENT)
        assert "latest charge" in decision.reason
        assert "add up to" in decision.reason

"""The tools and the workbook behind them."""

from __future__ import annotations

from subfinder.lib.statement.tools import get_merchant, list_transactions, tag_subscription
from subfinder.lib.statement.workbook import load_workbook


def test_lists_the_whole_statement() -> None:
    assert len(list_transactions()) == 35


def test_merchant_search_ignores_case_and_punctuation() -> None:
    assert [line.id for line in get_merchant("viewly com")] == ["T03", "T28"]


def test_tagging_twice_replaces_the_first_tag() -> None:
    tag_subscription("Viewly", ["T03"])
    tag_subscription("Viewly", ["T03", "T16"])
    assert [tag.transaction_ids for tag in load_workbook().tags] == [["T03", "T16"]]

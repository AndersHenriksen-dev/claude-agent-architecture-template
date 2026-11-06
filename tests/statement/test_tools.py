"""The tools and the workbook behind them."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from subfinder.lib.statement.tools import get_merchant, get_summary, list_transactions, save_summary, tag_subscription
from subfinder.lib.statement.workbook import SummaryLine, load_workbook, reset_workbook


def test_lists_the_whole_statement() -> None:
    assert len(list_transactions()) == 35


def test_merchant_search_ignores_case_and_punctuation() -> None:
    assert [line.id for line in get_merchant("viewly com")] == ["T03", "T28"]


def test_tagging_twice_replaces_the_first_tag() -> None:
    tag_subscription("Viewly", ["T03"])
    tag_subscription("Viewly", ["T03", "T16"])
    assert [tag.transaction_ids for tag in load_workbook().tags] == [["T03", "T16"]]


def test_summary_round_trips_through_the_file_as_decimal() -> None:
    line = SummaryLine(merchant="Viewly", monthly_saving=Decimal("119.00"), note="Price rose in October.")
    save_summary([line], Decimal("119.00"))
    summary = get_summary()
    assert summary is not None
    assert summary.total_monthly_saving == Decimal("119.00")
    assert summary.lines == [line]


def test_reset_forgets_the_run() -> None:
    tag_subscription("Viewly", ["T03"])
    reset_workbook()
    assert load_workbook().tags == []


def test_a_damaged_file_fails_loudly(workspace: Path) -> None:
    workspace.mkdir()
    (workspace / "workbook.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="damaged"):
        load_workbook()

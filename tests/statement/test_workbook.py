"""The file that holds a run's state: what goes in comes back, and damage is loud."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from subfinder.lib.statement.tools import get_summary, save_summary, tag_subscription
from subfinder.lib.statement.workbook import SummaryLine, load_workbook, reset_workbook


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

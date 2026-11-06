"""A whole run with no Claude Code, using the free scripted cleaner."""

from __future__ import annotations

from decimal import Decimal

import pytest

from subfinder.lib.api.run import find_and_save, save_checked, tag_checked
from subfinder.lib.api.scripted import clean_from_reference
from subfinder.lib.statement.workbook import Summary, SummaryLine, Tag, load_workbook


def test_finds_the_four_active_subscriptions() -> None:
    result = find_and_save(clean_from_reference)
    savings = {line.merchant: line.monthly_saving for line in result.summary.lines}
    assert savings == {
        "CloudVault": Decimal("29.00"),
        "FitZone": Decimal("249.00"),
        "Tunebox": Decimal("109.00"),
        "Viewly": Decimal("119.00"),
    }
    assert result.summary.total_monthly_saving == Decimal("506.00")


def test_notes_the_price_rise() -> None:
    lines = {line.merchant: line for line in find_and_save(clean_from_reference).summary.lines}
    assert "20.00" in lines["Viewly"].note
    assert lines["Tunebox"].note == "Price unchanged."


def test_reports_the_ended_subscription_without_counting_it() -> None:
    result = find_and_save(clean_from_reference)
    ended = [item.merchant for item in result.recurring if not item.active]
    assert ended == ["NewsDaily"]
    assert "NewsDaily" not in {line.merchant for line in result.summary.lines}


def test_saves_tags_and_summary_to_the_workbook() -> None:
    find_and_save(clean_from_reference)
    workbook = load_workbook()
    assert len(workbook.tags) == 4
    assert workbook.summary is not None


def test_a_second_run_starts_clean() -> None:
    tag_checked(Tag(merchant="Old", transaction_ids=["T01"]))
    find_and_save(clean_from_reference)
    assert "Old" not in {tag.merchant for tag in load_workbook().tags}


def test_the_check_stops_a_bad_tag_with_no_hook_around() -> None:
    with pytest.raises(ValueError, match="T99"):
        tag_checked(Tag(merchant="Ghost", transaction_ids=["T99"]))
    assert load_workbook().tags == []


def test_the_check_stops_an_overclaim_with_no_hook_around() -> None:
    tag_checked(Tag(merchant="Viewly", transaction_ids=["T03", "T16", "T28"]))
    line = SummaryLine(merchant="Viewly", monthly_saving=Decimal("999.00"), note="Note.")
    with pytest.raises(ValueError, match="latest charge"):
        save_checked(Summary(lines=[line], total_monthly_saving=Decimal("999.00")))
    assert load_workbook().summary is None

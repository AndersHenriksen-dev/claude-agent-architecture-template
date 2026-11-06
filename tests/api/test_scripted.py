"""The hand-written answer: it covers the whole statement, and it can score a real one."""

from __future__ import annotations

from subfinder.lib.api.scripted import clean_from_reference, count_agreeing
from subfinder.lib.statement.recurring import CleanedLine
from subfinder.lib.statement.transactions import STATEMENT


def test_covers_every_description_on_the_statement() -> None:
    descriptions = sorted({line.description for line in STATEMENT.transactions})
    assert {line.description for line in clean_from_reference(descriptions).lines} == set(descriptions)


def test_spends_no_tokens() -> None:
    assert clean_from_reference(["VIEWLY *MONTHLY"]).input_tokens == 0


def test_agreement_ignores_case_and_spaces_in_the_merchant() -> None:
    same = CleanedLine(description="HARBOUR LANE COFFEE", merchant="harbourlane COFFEE", category="other")
    assert count_agreeing([same]) == 1


def test_agreement_counts_a_wrong_category_as_wrong() -> None:
    wrong = CleanedLine(description="VIEWLY *MONTHLY", merchant="Viewly", category="other")
    assert count_agreeing([wrong]) == 0

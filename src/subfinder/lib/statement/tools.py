"""The tools themselves, as plain functions. The MCP server and the connector only decide who may reach them."""

from __future__ import annotations

from subfinder.lib.statement.transactions import STATEMENT, Money, Transaction
from subfinder.lib.statement.workbook import Summary, SummaryLine, Tag, load_workbook, save_workbook


def _normalize(text: str) -> str:
    return "".join(character for character in text.lower() if character.isalnum())


def list_transactions() -> list[Transaction]:
    """Every line on the statement."""
    return STATEMENT.transactions


def get_merchant(name: str) -> list[Transaction]:
    """The lines whose raw description contains a name, ignoring case, spaces and punctuation."""
    wanted = _normalize(name)
    return [line for line in STATEMENT.transactions if wanted in _normalize(line.description)]


def get_summary() -> Summary | None:
    """The saved summary, if a run has finished."""
    return load_workbook().summary


def tag_subscription(merchant: str, transaction_ids: list[str]) -> Tag:
    """Mark a merchant as a subscription. Tagging the same merchant again replaces its charges."""
    workbook = load_workbook()
    tag = Tag(merchant=merchant, transaction_ids=transaction_ids)
    workbook.tags = [existing for existing in workbook.tags if existing.merchant != merchant] + [tag]
    save_workbook(workbook)
    return tag


def save_summary(lines: list[SummaryLine], total_monthly_saving: Money) -> Summary:
    """Save the finished summary."""
    workbook = load_workbook()
    summary = Summary(lines=lines, total_monthly_saving=total_monthly_saving)
    workbook.summary = summary
    save_workbook(workbook)
    return summary

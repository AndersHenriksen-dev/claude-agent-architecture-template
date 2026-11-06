"""What a run has decided so far, kept in a file.

It has to be a file: the MCP server, each hook and the demo are separate processes, and they all need the same answer
to "what has been tagged, and has a summary been saved?".
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import Field, ValidationError

from subfinder.lib.shared.settings import Strict, workspace_dir
from subfinder.lib.statement.transactions import Money


class Tag(Strict):
    """A merchant marked as a subscription, with the charges that show it."""

    merchant: str
    transaction_ids: list[str]


class SummaryLine(Strict):
    """One subscription in the summary, and what cancelling it would save each month."""

    merchant: str
    monthly_saving: Money
    note: str


class Summary(Strict):
    """The finished result of a run."""

    lines: list[SummaryLine]
    total_monthly_saving: Money


class Workbook(Strict):
    """Everything a run has written."""

    tags: list[Tag] = Field(default_factory=list)
    summary: Summary | None = None


def _path() -> Path:
    return workspace_dir() / "workbook.json"


def load_workbook() -> Workbook:
    """Read the workbook, or start an empty one. A damaged file fails loudly instead of silently losing a run."""
    path = _path()
    if not path.exists():
        return Workbook()
    try:
        return Workbook.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as error:
        raise ValueError(f"{path} is damaged. Run `uv run subfinder reset` to start again.") from error


def save_workbook(workbook: Workbook) -> None:
    """Write the workbook to disk."""
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(workbook.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")


def reset_workbook() -> None:
    """Forget the current run."""
    _path().unlink(missing_ok=True)

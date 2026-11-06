"""The hand-written correct answer, used in place of the model where no paid call may happen."""

from __future__ import annotations

from subfinder.lib.api.clean_merchants import Cleaning
from subfinder.lib.shared.settings import Strict, config_for
from subfinder.lib.statement.recurring import CleanedLine


class _Config(Strict):
    lines: list[CleanedLine]


CONFIG = config_for(__name__, _Config)


class ScriptedCleaner:
    """Answers from the hand-written file, free. It behaves like a model that gets every line right."""

    def clean(self, descriptions: list[str]) -> Cleaning:
        """Look up each description."""
        wanted = set(descriptions)
        return Cleaning(lines=[line for line in CONFIG.lines if line.description in wanted])


def count_agreeing(lines: list[CleanedLine]) -> int:
    """How many cleaned lines have the right category and merchant name, ignoring the merchant's case and spacing."""

    def key(line: CleanedLine) -> tuple[str, str, str]:
        return line.description, "".join(line.merchant.lower().split()), line.category

    reference = {key(line) for line in CONFIG.lines}
    return sum(key(line) in reference for line in lines)

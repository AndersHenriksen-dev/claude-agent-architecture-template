"""Reading the rule and skill files the way Claude Code does: YAML frontmatter on top, Markdown under it.

Rules and skills are not Python, so nothing imports them. This is what lets the demo and the tests see them at all.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

from subfinder.lib.shared.settings import REPO_ROOT


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    """Split a Markdown file into its frontmatter and its body.

    Args:
        path: A rule or skill file. Frontmatter must start on the first line, as Claude Code requires.

    Returns:
        The frontmatter (empty if the file has none; Any because each kind of file has its own fields) and the body.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    header, body = text.removeprefix("---\n").split("\n---\n", maxsplit=1)
    return yaml.safe_load(header), body


def rule_files() -> list[Path]:
    """Every rule in the repo."""
    return sorted((REPO_ROOT / ".claude" / "rules").rglob("*.md"))


def skill_files() -> list[Path]:
    """Every skill's SKILL.md in the repo."""
    return sorted((REPO_ROOT / ".claude" / "skills").glob("*/SKILL.md"))


def rule_applies_to(rule: Path, relative_path: str) -> bool:
    """Whether a rule loads for a file. A rule with no `paths` loads in every session."""
    patterns = read_frontmatter(rule)[0].get("paths", [])
    return not patterns or any(fnmatch(relative_path, pattern) for pattern in patterns)

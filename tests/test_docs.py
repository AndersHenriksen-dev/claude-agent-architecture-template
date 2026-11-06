"""The docs: links must point at real files, and the house style holds. A broken link in a template is a broken step."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from subfinder.lib.shared.settings import REPO_ROOT

_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def _tracked_markdown() -> list[Path]:
    listing = subprocess.run(["git", "ls-files", "*.md"], capture_output=True, text=True, cwd=REPO_ROOT, check=True)
    others = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "*.md"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    )
    return [REPO_ROOT / name for name in (listing.stdout + others.stdout).split()]


MARKDOWN = _tracked_markdown()


def test_markdown_was_found() -> None:
    assert len(MARKDOWN) >= 10


@pytest.mark.parametrize("path", MARKDOWN, ids=lambda path: path.name)
def test_relative_links_point_at_real_files(path: Path) -> None:
    for target in _LINK.findall(path.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        assert (path.parent / target.split("#")[0]).exists(), f"{path.name} links to a missing file: {target}"


@pytest.mark.parametrize("path", MARKDOWN, ids=lambda path: path.name)
def test_no_em_dashes(path: Path) -> None:
    assert chr(0x2014) not in path.read_text(encoding="utf-8")

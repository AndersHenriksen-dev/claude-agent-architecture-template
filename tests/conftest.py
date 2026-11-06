"""Every test gets its own empty workspace, so no test can see another's run or touch the real one."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    folder = tmp_path / "workspace"
    monkeypatch.setenv("SUBFINDER_WORKSPACE", str(folder))
    return folder

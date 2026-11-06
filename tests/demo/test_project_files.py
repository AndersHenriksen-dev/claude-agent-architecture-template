"""The rule and skill files: Claude Code only loads them if they have the shape its docs require."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import anyio
import pytest

from subfinder.lib.demo.project_files import read_frontmatter, rule_applies_to, rule_files, skill_files
from subfinder.lib.mcp_server.server import build_server
from subfinder.lib.shared.settings import REPO_ROOT
from subfinder.lib.statement.workbook import Summary

MONEY_RULE = REPO_ROOT / ".claude" / "rules" / "money.md"
ADVICE_RULE = REPO_ROOT / ".claude" / "rules" / "no-advice.md"
SKILL = REPO_ROOT / ".claude" / "skills" / "find-subscriptions" / "SKILL.md"


class TestFrontmatter:
    def test_splits_header_and_body(self, tmp_path: Path) -> None:
        file = tmp_path / "rule.md"
        file.write_text('---\npaths:\n  - "src/**"\n---\n\n# Title\n', encoding="utf-8")
        header, body = read_frontmatter(file)
        assert header == {"paths": ["src/**"]}
        assert "# Title" in body

    def test_a_file_without_a_header_is_all_body(self, tmp_path: Path) -> None:
        file = tmp_path / "rule.md"
        file.write_text("# Title\n", encoding="utf-8")
        assert read_frontmatter(file) == ({}, "# Title\n")


class TestRules:
    def test_the_money_rule_loads_only_for_statement_files(self) -> None:
        assert rule_applies_to(MONEY_RULE, "src/subfinder/lib/statement/recurring.py")
        assert not rule_applies_to(MONEY_RULE, "src/subfinder/lib/hooks/events.py")

    def test_the_advice_rule_loads_everywhere(self) -> None:
        assert rule_applies_to(ADVICE_RULE, "README.md")

    def test_each_path_pattern_matches_a_real_file(self) -> None:
        for pattern in read_frontmatter(MONEY_RULE)[0]["paths"]:
            assert any(path.is_file() for path in REPO_ROOT.glob(pattern + "/*")), pattern

    def test_the_money_rule_holds_in_the_code_it_covers(self) -> None:
        """A rule only asks, so the part a machine can check also has a test: no float in the statement code."""
        for path in (REPO_ROOT / "src" / "subfinder" / "lib" / "statement").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
            # transactions.py names float once: the validator that refuses it.
            assert "float" not in names or path.name == "transactions.py", path


class TestSkill:
    def _header(self) -> dict[str, str]:
        return read_frontmatter(SKILL)[0]

    def test_there_is_one_skill(self) -> None:
        assert skill_files() == [SKILL]

    def test_the_name_meets_the_documented_limits(self) -> None:
        name = self._header()["name"]
        assert name == SKILL.parent.name
        assert re.fullmatch(r"[a-z0-9-]{1,64}", name)
        assert "claude" not in name
        assert "anthropic" not in name

    def test_the_description_says_what_and_when(self) -> None:
        description = self._header()["description"]
        assert 0 < len(description) <= 1024
        assert "Use when" in description

    def test_it_only_names_tools_the_server_has(self) -> None:
        tools = {tool.name for tool in anyio.run(build_server().list_tools)}
        allowed = self._header()["allowed-tools"].split()
        assert {name.removeprefix("mcp__subfinder__") for name in allowed} == tools

    def test_every_linked_file_exists(self) -> None:
        for link in re.findall(r"\]\(([^)]+\.md)\)", read_frontmatter(SKILL)[1]):
            assert (SKILL.parent / link).exists(), link

    def test_the_format_example_is_a_valid_summary(self) -> None:
        text = (SKILL.parent / "summary-format.md").read_text(encoding="utf-8")
        example = re.search(r"```json\n(.*?)```", text, re.DOTALL)
        assert example is not None
        summary = Summary.model_validate_json(example.group(1))
        assert summary.total_monthly_saving == sum(line.monthly_saving for line in summary.lines)

    @pytest.mark.parametrize("path", [*rule_files(), SKILL])
    def test_keeps_to_the_documented_size(self, path: Path) -> None:
        assert len(path.read_text(encoding="utf-8").splitlines()) < 200

"""The statement data and the money type."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from subfinder.lib.statement.transactions import STATEMENT, Money


class TestMoney:
    adapter: TypeAdapter[Decimal] = TypeAdapter(Money)

    def test_reads_a_string_exactly(self) -> None:
        assert self.adapter.validate_python("99.10") == Decimal("99.10")

    def test_refuses_a_float(self) -> None:
        with pytest.raises(ValidationError):
            self.adapter.validate_python(99.10)

    @pytest.mark.parametrize("text", ["1e5", "1.999", "99", "NaN", "Infinity", ""])
    def test_refuses_a_string_that_is_not_an_amount(self, text: str) -> None:
        with pytest.raises(ValidationError):
            self.adapter.validate_python(text)

    def test_writes_two_decimals_as_a_string(self) -> None:
        assert self.adapter.dump_python(Decimal("119"), mode="json") == "119.00"

    def test_tells_clients_to_send_a_string(self) -> None:
        assert self.adapter.json_schema()["type"] == "string"


class TestStatement:
    def test_every_id_is_unique(self) -> None:
        ids = [line.id for line in STATEMENT.transactions]
        assert len(ids) == len(set(ids))

    def test_covers_three_months(self) -> None:
        assert len({(line.date.year, line.date.month) for line in STATEMENT.transactions}) == 3

    def test_money_in_and_out_are_both_present(self) -> None:
        amounts = [line.amount for line in STATEMENT.transactions]
        assert min(amounts) < 0 < max(amounts)

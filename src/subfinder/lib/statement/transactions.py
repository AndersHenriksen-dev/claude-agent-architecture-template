"""The bank statement, and the money type every amount in the package uses.

Amounts are Decimal, and cross every JSON boundary as strings: a JSON number would arrive in Python as a float, and
99.10 as a float is not 99.10.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BeforeValidator, PlainSerializer, WithJsonSchema

from subfinder.lib.shared.settings import Strict, config_for

_AMOUNT_PATTERN = r"^-?\d+\.\d{2}$"


def _reject_float(value: object) -> object:
    """Stop a float before Pydantic quietly turns it into a Decimal that carries its rounding error."""
    if isinstance(value, float):
        raise ValueError("money must be a string such as '99.00', not a float")
    return value


Money = Annotated[
    Decimal,
    BeforeValidator(_reject_float),
    PlainSerializer(lambda amount: f"{amount:.2f}", return_type=str),
    WithJsonSchema({"type": "string", "pattern": _AMOUNT_PATTERN, "description": "An amount such as '99.00'"}),
]


class Transaction(Strict):
    """One line on the statement. A negative amount is money out."""

    id: str
    date: date
    description: str
    amount: Money


class Statement(Strict):
    """Everything the bank gives us."""

    account_holder: str
    currency: str
    transactions: list[Transaction]


STATEMENT = config_for(__name__, Statement)

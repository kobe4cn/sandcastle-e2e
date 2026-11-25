"""Money is stored as integer cents; convert only at the edges."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# Commas are only accepted as well-formed thousands groups; validate before stripping them,
# otherwise inputs like "1,23.4" or ",100" would slip through.
_GROUPED = re.compile(r"^[1-9]\d{0,2}(,\d{3})+(\.\d*)?$")


def parse_amount(text: str) -> int:
    """'12.5' -> 1250, '1,234.50' -> 123450. Rejects negatives, zero and more than two decimals."""
    cleaned = text.strip()
    if "," in cleaned:
        if not _GROUPED.match(cleaned):
            raise ValueError(f"not a number: {text!r}")
        cleaned = cleaned.replace(",", "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"not a number: {text!r}") from None
    if value <= 0:
        raise ValueError("amount must be positive")
    if value.as_tuple().exponent < -2:  # type: ignore[operator]
        raise ValueError("at most two decimals")
    return int(value * 100)


def format_cents(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"

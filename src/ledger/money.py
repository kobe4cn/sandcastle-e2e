"""Parse and format money amounts; money is stored as integer cents, converted only at the edges."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# Commas are only accepted as well-formed thousands groups; validate before stripping them,
# otherwise inputs like "1,23.4" or ",100" would slip through.
_GROUPED = re.compile(r"^[1-9]\d{0,2}(,\d{3})+(\.\d*)?$")


def parse_amount(text: str) -> int:
    """'12.5' -> 1250, '$12.50' -> 1250, '1,234.50' -> 123450.

    Rejects negatives, zero and more than two decimals.
    """
    # Strip the "$" before the comma check so "$1,234.50" still matches _GROUPED.
    cleaned = text.strip().removeprefix("$")
    # Decimal ignores leading whitespace, so "$ 5" would otherwise slip through.
    if cleaned[:1].isspace():
        raise ValueError(f"not a number: {text!r}")
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
    # Format the magnitude and prepend the sign: `//` floors toward -inf, so -150 would be "-2.50".
    sign = "-" if cents < 0 else ""
    magnitude = abs(cents)
    return f"{sign}{magnitude // 100}.{magnitude % 100:02d}"


def format_signed_cents(cents: int) -> str:
    """Format cents like `format_cents`, always signed; zero is "+0.00"."""
    sign = "-" if cents < 0 else "+"
    return f"{sign}{format_cents(abs(cents))}"


def format_cents_grouped(cents: int) -> str:
    """Format cents like `format_cents`, with thousands separators (123450 -> "1,234.50")."""
    # Same sign-first approach as `format_cents`, so -99 stays "-0.99".
    sign = "-" if cents < 0 else ""
    magnitude = abs(cents)
    return f"{sign}{magnitude // 100:,}.{magnitude % 100:02d}"

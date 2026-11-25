"""Money is stored as integer cents; convert only at the edges."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def parse_amount(text: str) -> int:
    """'12.5' -> 1250. Rejects negatives, zero and more than two decimals."""
    try:
        value = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError(f"not a number: {text!r}") from None
    if value <= 0:
        raise ValueError("amount must be positive")
    if value.as_tuple().exponent < -2:  # type: ignore[operator]
        raise ValueError("at most two decimals")
    return int(value * 100)


def format_cents(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"

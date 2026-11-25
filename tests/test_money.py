from __future__ import annotations

import pytest

from ledger.money import format_cents, parse_amount


@pytest.mark.parametrize("text,cents", [("12", 1200), ("12.5", 1250), ("0.01", 1), (" 3.40 ", 340)])
def test_parse(text: str, cents: int) -> None:
    assert parse_amount(text) == cents


@pytest.mark.parametrize("text", ["abc", "0", "-1", "1.234"])
def test_parse_rejects(text: str) -> None:
    with pytest.raises(ValueError):
        parse_amount(text)


def test_format() -> None:
    assert format_cents(1250) == "12.50"
    assert format_cents(5) == "0.05"

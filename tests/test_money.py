from __future__ import annotations

import pytest

from ledger.money import format_cents, format_cents_grouped, format_signed_cents, parse_amount


@pytest.mark.parametrize(
    "text,cents",
    [
        ("12", 1200),
        ("12.5", 1250),
        ("0.01", 1),
        (" 3.40 ", 340),
        ("1,234.50", 123450),
        ("12,345", 1234500),
        ("1,234,567", 123456700),
        ("$12.50", 1250),
        ("12.50", 1250),
        ("$1,234.50", 123450),
        (" $5", 500),
    ],
)
def test_parse(text: str, cents: int) -> None:
    assert parse_amount(text) == cents


@pytest.mark.parametrize(
    "text",
    [
        "abc",
        "0",
        "-1",
        "1.234",
        "1,23.4",
        ",100",
        "1,2345",
        "1,,234",
        "100,",
        "01,234",
        "1, 234",
        "-$5",
        "$-5",
        "$0",
        "$ 5",
    ],
)
def test_parse_rejects(text: str) -> None:
    with pytest.raises(ValueError):
        parse_amount(text)


@pytest.mark.parametrize("text", ["$", "$$1", "$ 5"])
def test_parse_rejects_malformed_dollar_sign_as_not_a_number(text: str) -> None:
    with pytest.raises(ValueError, match=r"^not a number: "):
        parse_amount(text)


@pytest.mark.parametrize(
    "cents,text",
    [
        (1250, "12.50"),
        (5, "0.05"),
        (0, "0.00"),
        (-150, "-1.50"),
        (-5, "-0.05"),
        (-100, "-1.00"),
    ],
)
def test_format_puts_minus_before_negative_amounts(cents: int, text: str) -> None:
    assert format_cents(cents) == text


@pytest.mark.parametrize(
    "cents,text",
    [
        (123450, "1,234.50"),
        (99, "0.99"),
        (100000000, "1,000,000.00"),
        (-123450, "-1,234.50"),
        (0, "0.00"),
        (-99, "-0.99"),
        (99999, "999.99"),
        (100000, "1,000.00"),
    ],
)
def test_format_grouped_inserts_thousands_separators(cents: int, text: str) -> None:
    assert format_cents_grouped(cents) == text


@pytest.mark.parametrize(
    "cents,text",
    [(750, "+7.50"), (0, "+0.00"), (-250, "-2.50"), (-99, "-0.99"), (123450, "+1234.50")],
)
def test_format_signed_cents_always_has_a_sign(cents: int, text: str) -> None:
    assert format_signed_cents(cents) == text

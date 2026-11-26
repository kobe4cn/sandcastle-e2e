"""CSV export and import of expenses; quoting is left to the csv module so notes with commas survive."""

from __future__ import annotations

import csv
import io
from datetime import date

from ledger.db import Expense, _validated_category, _validated_note
from ledger.money import format_cents, parse_amount

HEADER = ["id", "date", "category", "amount", "note"]


def expenses_to_csv(expenses: list[Expense]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(HEADER)
    for e in expenses:
        writer.writerow(
            [e.id, e.spent_on.isoformat(), e.category, format_cents(e.amount_cents), e.note]
        )
    return buf.getvalue()


def parse_csv(text: str) -> list[tuple[date, str, int, str]]:
    """Validate every row like `ledger add`; errors name the line where the bad record starts."""
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != HEADER:
        raise ValueError(f"line 1: header must be {','.join(HEADER)}")
    rows: list[tuple[date, str, int, str]] = []
    while True:
        # A quoted note can span several physical lines; line_num is where the record ends.
        line = reader.line_num + 1
        try:
            row = next(reader)
        except StopIteration:
            break
        try:
            rows.append(_parse_row(row))
        except ValueError as e:
            raise ValueError(f"line {line}: {e}") from None
    return rows


def _parse_row(row: dict[str | None, str | None]) -> tuple[date, str, int, str]:
    if None in row:
        raise ValueError("too many fields")
    spent_on, category, amount, note = (row["date"], row["category"], row["amount"], row["note"])
    if spent_on is None or category is None or amount is None or note is None:
        raise ValueError("missing field")
    cents = parse_amount(amount)
    return (
        date.fromisoformat(spent_on),
        _validated_category(category, cents),
        cents,
        _validated_note(note),
    )

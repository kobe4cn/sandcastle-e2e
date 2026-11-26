"""CSV export of expenses; quoting is left to the csv module so notes with commas survive."""

from __future__ import annotations

import csv
import io

from ledger.db import Expense
from ledger.money import format_cents


def expenses_to_csv(expenses: list[Expense]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["id", "date", "category", "amount", "note"])
    for e in expenses:
        writer.writerow(
            [e.id, e.spent_on.isoformat(), e.category, format_cents(e.amount_cents), e.note]
        )
    return buf.getvalue()

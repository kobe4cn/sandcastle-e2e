from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date

from ledger import db
from ledger.export import expenses_to_csv


def test_csv_has_header_and_quotes_awkward_notes(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 2), "food", 1250, 'lunch, "big"\nwith friends')
    db.add_expense(conn, date(2026, 1, 3), "travel", 300)
    out = expenses_to_csv(db.list_expenses(conn))
    assert list(csv.reader(io.StringIO(out))) == [
        ["id", "date", "category", "amount", "note"],
        ["1", "2026-01-02", "food", "12.50", 'lunch, "big"\nwith friends'],
        ["2", "2026-01-03", "travel", "3.00", ""],
    ]


def test_csv_of_no_expenses_is_header_only() -> None:
    assert expenses_to_csv([]) == "id,date,category,amount,note\n"

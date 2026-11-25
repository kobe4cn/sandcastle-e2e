from __future__ import annotations

import sqlite3
from datetime import date

from ledger import db
from ledger.report import monthly_totals, totals_by_category


def test_totals_sorted_by_amount_desc(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 300)
    db.add_expense(conn, date(2026, 1, 2), "rent", 1000)
    db.add_expense(conn, date(2026, 2, 1), "food", 200)
    assert totals_by_category(db.list_expenses(conn)) == {"rent": 1000, "food": 500}


def test_monthly(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 300)
    db.add_expense(conn, date(2026, 2, 1), "food", 200)
    assert monthly_totals(db.list_expenses(conn)) == {"2026-01": 300, "2026-02": 200}

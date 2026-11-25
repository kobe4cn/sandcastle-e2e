from __future__ import annotations

import sqlite3
from datetime import date

import pytest

from ledger import db


def test_add_and_list(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 2), "Food ", 1250, "lunch")
    db.add_expense(conn, date(2026, 1, 1), "rent", 100000)
    rows = db.list_expenses(conn)
    assert [r.category for r in rows] == ["rent", "food"]
    assert rows[1].note == "lunch"


def test_filter_by_category(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 100)
    db.add_expense(conn, date(2026, 1, 1), "travel", 200)
    assert [r.amount_cents for r in db.list_expenses(conn, "FOOD")] == [100]


@pytest.mark.parametrize("amount,category", [(0, "food"), (-5, "food"), (100, "  ")])
def test_rejects_invalid(conn: sqlite3.Connection, amount: int, category: str) -> None:
    with pytest.raises(ValueError):
        db.add_expense(conn, date(2026, 1, 1), category, amount)


def test_delete(conn: sqlite3.Connection) -> None:
    i = db.add_expense(conn, date(2026, 1, 1), "food", 100)
    assert db.delete_expense(conn, i) is True
    assert db.delete_expense(conn, i) is False
    assert db.list_expenses(conn) == []

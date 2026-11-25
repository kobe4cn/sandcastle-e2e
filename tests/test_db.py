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


def test_set_budget_overwrites_previous_value(conn: sqlite3.Connection) -> None:
    db.set_budget(conn, "food", 30000)
    db.set_budget(conn, "food", 45000)
    assert db.list_budgets(conn) == {"food": 45000}


def test_set_budget_normalizes_category(conn: sqlite3.Connection) -> None:
    db.set_budget(conn, " Food ", 30000)
    db.set_budget(conn, "FOOD", 20000)
    assert db.list_budgets(conn) == {"food": 20000}


def test_list_budgets_sorted_by_category(conn: sqlite3.Connection) -> None:
    db.set_budget(conn, "travel", 500)
    db.set_budget(conn, "food", 300)
    db.set_budget(conn, "rent", 100000)
    assert list(db.list_budgets(conn).items()) == [
        ("food", 300),
        ("rent", 100000),
        ("travel", 500),
    ]


@pytest.mark.parametrize("amount,category", [(0, "food"), (-5, "food"), (100, "  ")])
def test_set_budget_rejects_invalid(conn: sqlite3.Connection, amount: int, category: str) -> None:
    with pytest.raises(ValueError):
        db.set_budget(conn, category, amount)
    assert db.list_budgets(conn) == {}


def test_budgets_table_leaves_expenses_untouched(conn: sqlite3.Connection) -> None:
    db.set_budget(conn, "food", 300)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(expenses)")]
    assert cols == ["id", "spent_on", "category", "amount_cents", "note"]
    assert db.list_expenses(conn) == []


def test_delete_budget(conn: sqlite3.Connection) -> None:
    db.set_budget(conn, "food", 300)
    assert db.delete_budget(conn, "food") is True
    assert db.delete_budget(conn, "food") is False
    assert db.list_budgets(conn) == {}


def test_delete_budget_normalizes_category(conn: sqlite3.Connection) -> None:
    db.set_budget(conn, "food", 300)
    assert db.delete_budget(conn, " Food ") is True
    assert db.list_budgets(conn) == {}


def test_delete_budget_blank_category_returns_false(conn: sqlite3.Connection) -> None:
    db.set_budget(conn, "food", 300)
    assert db.delete_budget(conn, "  ") is False
    assert db.list_budgets(conn) == {"food": 300}


def test_list_categories_distinct_sorted(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 2), "travel", 300)
    db.add_expense(conn, date(2026, 1, 2), "Food", 1000)
    db.add_expense(conn, date(2026, 1, 3), "food ", 2000)
    db.add_expense(conn, date(2026, 1, 3), "books", 150)
    db.set_budget(conn, "rent", 100000)
    assert db.list_categories(conn) == ["books", "food", "travel"]


def test_list_categories_empty(conn: sqlite3.Connection) -> None:
    assert db.list_categories(conn) == []

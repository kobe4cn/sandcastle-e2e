from __future__ import annotations

import sqlite3
from datetime import date

from ledger import db
from ledger.report import (
    average_by_category,
    budget_status,
    monthly_totals,
    totals_by_category,
)


def test_totals_sorted_by_amount_desc(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 300)
    db.add_expense(conn, date(2026, 1, 2), "rent", 1000)
    db.add_expense(conn, date(2026, 2, 1), "food", 200)
    assert totals_by_category(db.list_expenses(conn)) == {"rent": 1000, "food": 500}


def test_monthly(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 300)
    db.add_expense(conn, date(2026, 2, 1), "food", 200)
    assert monthly_totals(db.list_expenses(conn)) == {"2026-01": 300, "2026-02": 200}


def test_average_of_empty_list_is_empty() -> None:
    assert average_by_category([]) == {}


def test_average_rounds_half_up(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 1)
    db.add_expense(conn, date(2026, 1, 2), "food", 2)
    assert average_by_category(db.list_expenses(conn)) == {"food": 2}


def test_average_per_category_sorted_by_name(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "rent", 1000)
    db.add_expense(conn, date(2026, 1, 2), "food", 300)
    db.add_expense(conn, date(2026, 2, 1), "food", 200)
    result = average_by_category(db.list_expenses(conn))
    assert result == {"food": 250, "rent": 1000}
    assert list(result) == ["food", "rent"]


def test_budget_status_counts_only_the_given_month(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 300)
    db.add_expense(conn, date(2026, 1, 31), "food", 200)
    db.add_expense(conn, date(2026, 2, 1), "food", 9999)
    db.add_expense(conn, date(2025, 12, 31), "food", 9999)
    result = budget_status(db.list_expenses(conn), {"food": 1000}, "2026-01")
    assert result == [("food", 500, 1000, 500)]


def test_budget_status_overspent_remaining_is_negative(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 2), "food", 1250)
    assert budget_status(db.list_expenses(conn), {"food": 1000}, "2026-01") == [
        ("food", 1250, 1000, -250)
    ]


def test_budget_status_budget_without_spending_has_zero_spent(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 2), "food", 100)
    result = budget_status(db.list_expenses(conn), {"travel": 5000, "food": 300}, "2026-01")
    assert result == [("food", 100, 300, 200), ("travel", 0, 5000, 5000)]


def test_budget_status_omits_categories_without_budget(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 2), "food", 100)
    db.add_expense(conn, date(2026, 1, 3), "rent", 100000)
    assert budget_status(db.list_expenses(conn), {"food": 300}, "2026-01") == [
        ("food", 100, 300, 200)
    ]

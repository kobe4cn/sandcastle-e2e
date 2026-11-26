from __future__ import annotations

import sqlite3
from datetime import date

import pytest

from ledger import db
from ledger.report import (
    average_by_category,
    budget_status,
    category_share,
    change_percent,
    compare_months,
    largest_expense_by_category,
    monthly_totals,
    totals_by_category,
)


def test_totals_sorted_by_amount_desc(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 300)
    db.add_expense(conn, date(2026, 1, 2), "rent", 1000)
    db.add_expense(conn, date(2026, 2, 1), "food", 200)
    assert totals_by_category(db.list_expenses(conn)) == {"rent": 1000, "food": 500}


def test_share_sorted_by_share_desc(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 100)
    db.add_expense(conn, date(2026, 1, 2), "rent", 200)
    result = category_share(db.list_expenses(conn))
    assert result == {"rent": 66.7, "food": 33.3}
    assert list(result) == ["rent", "food"]


def test_share_rounds_half_up(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "a", 1)
    db.add_expense(conn, date(2026, 1, 2), "b", 15)
    result = category_share(db.list_expenses(conn))
    assert result == {"b": 93.8, "a": 6.3}
    assert list(result) == ["b", "a"]


def test_share_of_empty_list_is_empty() -> None:
    assert category_share([]) == {}


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


def test_largest_of_empty_list_is_empty() -> None:
    assert largest_expense_by_category([]) == {}


def test_largest_is_max_single_expense_sorted_by_name(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "rent", 1000)
    db.add_expense(conn, date(2026, 1, 2), "food", 300)
    db.add_expense(conn, date(2026, 1, 3), "food", 750)
    db.add_expense(conn, date(2026, 2, 1), "food", 200)
    result = largest_expense_by_category(db.list_expenses(conn))
    assert result == {"food": 750, "rent": 1000}
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


def test_compare_months_sorted_by_category_name(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 3, 1), "rent", 100000)
    db.add_expense(conn, date(2026, 3, 2), "food", 2000)
    db.add_expense(conn, date(2026, 3, 3), "food", 1750)
    db.add_expense(conn, date(2026, 2, 5), "food", 3000)
    db.add_expense(conn, date(2026, 2, 6), "rent", 100000)
    db.add_expense(conn, date(2026, 1, 6), "food", 9999)
    result = compare_months(db.list_expenses(conn), "2026-03", "2026-02")
    assert result == [("food", 3750, 3000), ("rent", 100000, 100000)]


def test_compare_months_includes_category_in_only_one_month(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 3, 1), "books", 500)
    db.add_expense(conn, date(2026, 2, 1), "travel", 1200)
    result = compare_months(db.list_expenses(conn), "2026-03", "2026-02")
    assert result == [("books", 500, 0), ("travel", 0, 1200)]


def test_compare_months_across_year_boundary(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 300)
    db.add_expense(conn, date(2025, 12, 31), "food", 200)
    db.add_expense(conn, date(2025, 1, 15), "food", 9999)
    result = compare_months(db.list_expenses(conn), "2026-01", "2025-12")
    assert result == [("food", 300, 200)]


def test_compare_months_empty_when_neither_month_has_expenses(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 1), "food", 300)
    assert compare_months(db.list_expenses(conn), "2026-03", "2026-02") == []


@pytest.mark.parametrize(
    "current,previous,expected",
    [
        (3750, 3000, 25),
        (105, 100, 5),
        (201, 200, 1),
        (199, 200, -1),
        (0, 100, -100),
        (100, 100, 0),
        (100, 0, None),
    ],
)
def test_change_percent_rounds_half_away_from_zero(
    current: int, previous: int, expected: int | None
) -> None:
    assert change_percent(current, previous) == expected

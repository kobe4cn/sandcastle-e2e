"""SQLite storage. The database path comes from LEDGER_DB (default: ./ledger.db)."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spent_on TEXT NOT NULL,
    category TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS budgets (
    category TEXT PRIMARY KEY,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0)
);
"""


@dataclass(frozen=True)
class Expense:
    id: int
    spent_on: date
    category: str
    amount_cents: int
    note: str


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or os.environ.get("LEDGER_DB", "ledger.db"))
    conn.executescript(SCHEMA)
    return conn


def _validated_category(category: str, amount_cents: int) -> str:
    """Shared by expenses and budgets so both store categories in the same normalized form."""
    if amount_cents <= 0:
        raise ValueError("amount must be positive")
    category = category.strip().lower()
    if not category:
        raise ValueError("category is required")
    return category


def add_expense(
    conn: sqlite3.Connection, spent_on: date, category: str, amount_cents: int, note: str = ""
) -> int:
    category = _validated_category(category, amount_cents)
    cur = conn.execute(
        "INSERT INTO expenses (spent_on, category, amount_cents, note) VALUES (?, ?, ?, ?)",
        (spent_on.isoformat(), category, amount_cents, note),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def _category_filter(category: str | None) -> tuple[str, tuple[str, ...]]:
    """WHERE clause for an optional category filter; empty means no filter. Normalized like writes."""
    if not category:
        return "", ()
    return " WHERE category = ?", (category.strip().lower(),)


def list_expenses(
    conn: sqlite3.Connection, category: str | None = None, *, min_cents: int | None = None
) -> list[Expense]:
    where, cat_args = _category_filter(category)
    args: tuple[str | int, ...] = cat_args
    if min_cents is not None:
        where += " AND amount_cents >= ?" if where else " WHERE amount_cents >= ?"
        args += (min_cents,)
    sql = f"SELECT id, spent_on, category, amount_cents, note FROM expenses{where}"
    sql += " ORDER BY spent_on, id"
    return [
        Expense(r[0], date.fromisoformat(r[1]), r[2], r[3], r[4]) for r in conn.execute(sql, args)
    ]


def list_categories(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT category FROM expenses ORDER BY category")
    return [r[0] for r in rows]


def count_expenses(conn: sqlite3.Connection, category: str | None = None) -> int:
    where, args = _category_filter(category)
    return int(conn.execute(f"SELECT COUNT(*) FROM expenses{where}", args).fetchone()[0])


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> bool:
    cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    return cur.rowcount > 0


def set_budget(conn: sqlite3.Connection, category: str, amount_cents: int) -> None:
    category = _validated_category(category, amount_cents)
    conn.execute(
        "INSERT INTO budgets (category, amount_cents) VALUES (?, ?)"
        " ON CONFLICT(category) DO UPDATE SET amount_cents = excluded.amount_cents",
        (category, amount_cents),
    )
    conn.commit()


def list_budgets(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT category, amount_cents FROM budgets ORDER BY category")
    return {r[0]: r[1] for r in rows}


def delete_budget(conn: sqlite3.Connection, category: str) -> bool:
    category = category.strip().lower()
    if not category:
        return False
    cur = conn.execute("DELETE FROM budgets WHERE category = ?", (category,))
    conn.commit()
    return cur.rowcount > 0

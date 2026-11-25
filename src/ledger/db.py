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


def add_expense(
    conn: sqlite3.Connection, spent_on: date, category: str, amount_cents: int, note: str = ""
) -> int:
    if amount_cents <= 0:
        raise ValueError("amount must be positive")
    category = category.strip().lower()
    if not category:
        raise ValueError("category is required")
    cur = conn.execute(
        "INSERT INTO expenses (spent_on, category, amount_cents, note) VALUES (?, ?, ?, ?)",
        (spent_on.isoformat(), category, amount_cents, note),
    )
    conn.commit()
    assert cur.lastrowid is not None
    return cur.lastrowid


def list_expenses(conn: sqlite3.Connection, category: str | None = None) -> list[Expense]:
    sql = "SELECT id, spent_on, category, amount_cents, note FROM expenses"
    args: tuple[str, ...] = ()
    if category:
        sql += " WHERE category = ?"
        args = (category.strip().lower(),)
    sql += " ORDER BY spent_on, id"
    return [
        Expense(r[0], date.fromisoformat(r[1]), r[2], r[3], r[4]) for r in conn.execute(sql, args)
    ]


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> bool:
    cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    return cur.rowcount > 0

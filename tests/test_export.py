from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date

import pytest

from ledger import db
from ledger.export import expenses_to_csv, parse_csv


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


def test_parse_csv_round_trips_export(conn: sqlite3.Connection) -> None:
    db.add_expense(conn, date(2026, 1, 2), "food", 1250, 'lunch, "big"\nwith friends')
    db.add_expense(conn, date(2026, 1, 3), "travel", 300)
    assert parse_csv(expenses_to_csv(db.list_expenses(conn))) == [
        (date(2026, 1, 2), "food", 1250, 'lunch, "big"\nwith friends'),
        (date(2026, 1, 3), "travel", 300, ""),
    ]


def test_parse_csv_ignores_id_and_normalizes_category() -> None:
    text = "id,date,category,amount,note\n99,2026-01-02, Food ,$1.5,x\n"
    assert parse_csv(text) == [(date(2026, 1, 2), "food", 150, "x")]


def test_parse_csv_of_header_only_is_empty() -> None:
    assert parse_csv("id,date,category,amount,note\n") == []


HEADER = "id,date,category,amount,note\n"
GOOD = "1,2026-01-02,food,1.00,ok\n"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (HEADER + GOOD + "2,2026-01-03,food,abc,\n", "line 3: not a number: 'abc'"),
        (HEADER + "1,2026-01-02,food,0,\n", "line 2: amount must be positive"),
        (HEADER + "1,2026-01-02, ,1.00,\n", "line 2: category is required"),
        (
            HEADER + "1,2026-01-02,food,1.00," + "x" * 201 + "\n",
            "line 2: note must be at most 200 characters",
        ),
        (HEADER + "1,2026-13-02,food,1.00,\n", "line 2: "),
        (HEADER + '1,2026-01-02,food,1.00,"two\nlines"\n2,bad,food,1.00,\n', "line 4: "),
        (HEADER + "1,2026-01-02,food\n", "line 2: missing field"),
        (HEADER + "1,2026-01-02,food,1.00,,extra\n", "line 2: too many fields"),
        ("id,date,category,amount\n", "line 1: header must be id,date,category,amount,note"),
        ("", "line 1: header must be id,date,category,amount,note"),
    ],
)
def test_parse_csv_rejects_bad_rows(text: str, message: str) -> None:
    with pytest.raises(ValueError) as exc:
        parse_csv(text)
    assert str(exc.value).startswith(message)

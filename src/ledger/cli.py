"""Command line: ledger add | list | report | delete."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from importlib.metadata import version

from ledger import db
from ledger.money import format_cents, parse_amount
from ledger.report import totals_by_category


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ledger")
    p.add_argument("--version", action="version", version=f"%(prog)s {version('ledger')}")
    sub = p.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="record an expense")
    add.add_argument("amount")
    add.add_argument("category")
    add.add_argument("--note", default="")
    add.add_argument("--on", type=date.fromisoformat, default=None, help="YYYY-MM-DD")

    ls = sub.add_parser("list", help="list expenses")
    ls.add_argument("--category")

    sub.add_parser("report", help="totals by category")

    rm = sub.add_parser("delete", help="delete an expense by id")
    rm.add_argument("id", type=int)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    conn = db.connect()
    try:
        if args.cmd == "add":
            try:
                cents = parse_amount(args.amount)
                new_id = db.add_expense(conn, args.on or date.today(), args.category, cents, args.note)
            except ValueError as e:
                print(f"error: {e}", file=sys.stderr)
                return 2
            print(f"added #{new_id}")
        elif args.cmd == "list":
            for row in db.list_expenses(conn, args.category):
                print(f"{row.id}\t{row.spent_on}\t{row.category}\t{format_cents(row.amount_cents)}\t{row.note}")
        elif args.cmd == "report":
            for cat, cents in totals_by_category(db.list_expenses(conn)).items():
                print(f"{cat}\t{format_cents(cents)}")
        elif args.cmd == "delete":
            if not db.delete_expense(conn, args.id):
                print(f"error: no expense #{args.id}", file=sys.stderr)
                return 1
            print(f"deleted #{args.id}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

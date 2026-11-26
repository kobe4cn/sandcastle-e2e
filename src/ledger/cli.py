"""Command line: ledger add | list | report | delete | budget | status | categories | count."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from importlib.metadata import version

from ledger import db
from ledger.money import format_cents, parse_amount
from ledger.report import average_by_category, budget_status, totals_by_category


def _month(text: str) -> str:
    try:
        dt = datetime.strptime(text, "%Y-%m")
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid month {text!r}, expected YYYY-MM") from None
    return dt.strftime("%Y-%m")


def _positive_int(text: str) -> int:
    try:
        n = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid limit {text!r}, expected an integer") from None
    if n <= 0:
        raise argparse.ArgumentTypeError(f"invalid limit {text!r}, must be at least 1")
    return n


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ledger")
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {version('ledger')}")
    sub = p.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="record an expense")
    add.add_argument("amount")
    add.add_argument("category")
    add.add_argument("--note", default="")
    add.add_argument("--on", type=date.fromisoformat, default=None, help="YYYY-MM-DD")

    ls = sub.add_parser("list", help="list expenses")
    ls.add_argument("--category")
    ls.add_argument("--limit", type=_positive_int, default=None, help="show at most N expenses")

    report = sub.add_parser("report", help="totals by category")
    report.add_argument(
        "--average", action="store_true", help="average spend per expense by category"
    )

    rm = sub.add_parser("delete", help="delete an expense by id")
    rm.add_argument("id", type=int)

    budget = sub.add_parser("budget", help="monthly budgets per category")
    budget_sub = budget.add_subparsers(dest="budget_cmd", required=True)
    bset = budget_sub.add_parser("set", help="set a category's monthly budget")
    bset.add_argument("category")
    bset.add_argument("amount")
    budget_sub.add_parser("list", help="list budgets")
    brm = budget_sub.add_parser("rm", help="remove a category's budget")
    brm.add_argument("category")

    status = sub.add_parser("status", help="spending vs budget per category for a month")
    status.add_argument("--month", type=_month, default=None, help="YYYY-MM, default this month")

    sub.add_parser("categories", help="list categories used by expenses")

    count = sub.add_parser("count", help="number of recorded expenses")
    count.add_argument("--category")
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
            expenses = db.list_expenses(conn, args.category)
            if args.limit is not None:
                expenses = expenses[: args.limit]
            for row in expenses:
                print(f"{row.id}\t{row.spent_on}\t{row.category}\t{format_cents(row.amount_cents)}\t{row.note}")
        elif args.cmd == "report":
            if args.average:
                for cat, avg in average_by_category(db.list_expenses(conn)).items():
                    print(f"{cat}\t{format_cents(avg)}")
            else:
                for cat, cents in totals_by_category(db.list_expenses(conn)).items():
                    print(f"{cat}\t{format_cents(cents)}")
        elif args.cmd == "delete":
            if not db.delete_expense(conn, args.id):
                print(f"error: no expense #{args.id}", file=sys.stderr)
                return 1
            print(f"deleted #{args.id}")
        elif args.cmd == "budget":
            if args.budget_cmd == "set":
                try:
                    db.set_budget(conn, args.category, parse_amount(args.amount))
                except ValueError as e:
                    print(f"error: {e}", file=sys.stderr)
                    return 2
            elif args.budget_cmd == "list":
                for cat, cents in db.list_budgets(conn).items():
                    print(f"{cat}\t{format_cents(cents)}")
            elif args.budget_cmd == "rm":
                if not db.delete_budget(conn, args.category):
                    print(f"error: no budget for {args.category}", file=sys.stderr)
                    return 1
                print(f"removed budget for {args.category}")
        elif args.cmd == "status":
            month = args.month or date.today().strftime("%Y-%m")
            rows = budget_status(db.list_expenses(conn), db.list_budgets(conn), month)
            for cat, spent, budget, remaining in rows:
                print(
                    f"{cat}\t{format_cents(spent)}\t{format_cents(budget)}\t{format_cents(remaining)}"
                )
        elif args.cmd == "categories":
            for cat in db.list_categories(conn):
                print(cat)
        elif args.cmd == "count":
            print(db.count_expenses(conn, args.category))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

"""Command line: ledger add | list | report | delete | budget | status | categories | count."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime

from ledger import __version__, db
from ledger.money import format_cents, parse_amount
from ledger.report import (
    average_by_category,
    budget_status,
    category_share,
    totals_by_category,
)


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


def _amount(text: str) -> int:
    try:
        return parse_amount(text)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"invalid amount {text!r}: {e}") from None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ledger")
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="record an expense")
    add.add_argument("amount")
    add.add_argument("category")
    add.add_argument("--note", default="")
    add.add_argument("--on", type=date.fromisoformat, default=None, help="YYYY-MM-DD")

    ls = sub.add_parser("list", help="list expenses")
    ls.add_argument("--category")
    ls.add_argument("--limit", type=_positive_int, default=None, help="show at most N expenses")
    ls.add_argument("--reverse", action="store_true", help="newest first")
    ls.add_argument(
        "--min",
        type=_amount,
        default=None,
        dest="min_cents",
        metavar="AMOUNT",
        help="only expenses of at least this amount",
    )
    ls.add_argument(
        "--max",
        type=_amount,
        default=None,
        dest="max_cents",
        metavar="AMOUNT",
        help="only expenses of at most this amount",
    )
    ls.add_argument("--json", action="store_true", help="print expenses as a JSON array")

    report = sub.add_parser("report", help="totals by category")
    report_mode = report.add_mutually_exclusive_group()
    report_mode.add_argument(
        "--average", action="store_true", help="average spend per expense, per category"
    )
    report_mode.add_argument(
        "--share", action="store_true", help="percentage of total spending, per category"
    )
    report.add_argument("--category", help="only report this category")

    rm = sub.add_parser("delete", help="delete an expense by id")
    rm.add_argument("id", type=int)

    budget = sub.add_parser("budget", help="monthly budgets per category")
    budget_sub = budget.add_subparsers(dest="budget_cmd", required=True)
    bset = budget_sub.add_parser("set", help="set a category's monthly budget")
    bset.add_argument("category")
    bset.add_argument("amount")
    blist = budget_sub.add_parser("list", help="list budgets")
    blist.add_argument("--json", action="store_true", help="print budgets as a JSON object")
    brm = budget_sub.add_parser("rm", help="remove a category's budget")
    brm.add_argument("category")

    status = sub.add_parser("status", help="spending vs budget per category for a month")
    status.add_argument("--month", type=_month, default=None, help="YYYY-MM, default this month")
    status.add_argument("--json", action="store_true", help="print status as a JSON array")

    cats = sub.add_parser("categories", help="list categories used by expenses")
    cats.add_argument("--json", action="store_true", help="print categories as a JSON array")

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
            expenses = db.list_expenses(
                conn, args.category, min_cents=args.min_cents, max_cents=args.max_cents
            )
            if args.reverse:
                expenses = expenses[::-1]
            if args.limit is not None:
                expenses = expenses[: args.limit]
            if args.json:
                print(
                    json.dumps(
                        [
                            {
                                "id": e.id,
                                "date": e.spent_on.isoformat(),
                                "amount": format_cents(e.amount_cents),
                                "category": e.category,
                                "note": e.note,
                            }
                            for e in expenses
                        ],
                        ensure_ascii=False,
                    )
                )
            else:
                for row in expenses:
                    print(f"{row.id}\t{row.spent_on}\t{row.category}\t{format_cents(row.amount_cents)}\t{row.note}")
        elif args.cmd == "report":
            rows = list(db.list_expenses(conn, args.category))
            if args.average:
                for cat, avg in average_by_category(rows).items():
                    print(f"{cat}\t{format_cents(avg)}")
            elif args.share:
                for cat, share in category_share(rows).items():
                    print(f"{cat}\t{share:.1f}%")
            else:
                for cat, cents in totals_by_category(rows).items():
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
                budgets = db.list_budgets(conn)
                if args.json:
                    amounts = {cat: format_cents(cents) for cat, cents in budgets.items()}
                    print(json.dumps(amounts, ensure_ascii=False))
                else:
                    for cat, cents in budgets.items():
                        print(f"{cat}\t{format_cents(cents)}")
            elif args.budget_cmd == "rm":
                if not db.delete_budget(conn, args.category):
                    print(f"error: no budget for {args.category}", file=sys.stderr)
                    return 1
                print(f"removed budget for {args.category}")
        elif args.cmd == "status":
            month = args.month or date.today().strftime("%Y-%m")
            statuses = budget_status(db.list_expenses(conn), db.list_budgets(conn), month)
            if args.json:
                print(
                    json.dumps(
                        [
                            {
                                "category": cat,
                                "spent": format_cents(spent),
                                "budget": format_cents(budget),
                            }
                            for cat, spent, budget, _ in statuses
                        ],
                        ensure_ascii=False,
                    )
                )
            else:
                for cat, spent, budget, remaining in statuses:
                    print(
                        f"{cat}\t{format_cents(spent)}\t{format_cents(budget)}\t"
                        f"{format_cents(remaining)}"
                    )
        elif args.cmd == "categories":
            categories = db.list_categories(conn)
            if args.json:
                print(json.dumps(categories, ensure_ascii=False))
            else:
                for cat in categories:
                    print(cat)
        elif args.cmd == "count":
            print(db.count_expenses(conn, args.category))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

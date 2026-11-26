"""Command line: ledger add | list | report | delete | budget | status | categories | count | export | compare."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta

from ledger import __version__, db
from ledger.export import expenses_to_csv
from ledger.money import format_cents, format_signed_cents, parse_amount
from ledger.report import (
    average_by_category,
    budget_status,
    category_share,
    change_percent,
    compare_months,
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
    cats_fmt = cats.add_mutually_exclusive_group()
    cats_fmt.add_argument("--json", action="store_true", help="print categories as a JSON array")
    cats_fmt.add_argument(
        "--count", action="store_true", help="print each category with its expense count"
    )

    count = sub.add_parser("count", help="number of recorded expenses")
    count.add_argument("--category")
    count.add_argument("--month", type=_month, default=None, help="YYYY-MM")
    count.add_argument("--json", action="store_true", help="print the count as a JSON object")

    compare = sub.add_parser("compare", help="per-category spending vs the previous month")
    compare.add_argument("--month", type=_month, default=None, help="YYYY-MM, default this month")

    export = sub.add_parser("export", help="write expenses as CSV")
    export.add_argument("--category")
    export.add_argument("--output", metavar="PATH", help="write to a file instead of stdout")
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
            elif not expenses:
                print("no expenses")
            else:
                for row in expenses:
                    print(f"{row.id}\t{row.spent_on}\t{row.category}\t{format_cents(row.amount_cents)}\t{row.note}")
        elif args.cmd == "report":
            rows = list(db.list_expenses(conn, args.category))
            if not rows:
                print("no expenses")
            elif args.average:
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
            print(f"deleted expense id {args.id}")
        elif args.cmd == "budget":
            if args.budget_cmd == "set":
                try:
                    cents = parse_amount(args.amount)
                    db.set_budget(conn, args.category, cents)
                except ValueError as e:
                    print(f"error: {e}", file=sys.stderr)
                    return 2
                print(f"budget for {args.category.strip().lower()} set to {format_cents(cents)}")
            elif args.budget_cmd == "list":
                budgets = db.list_budgets(conn)
                if args.json:
                    amounts = {cat: format_cents(cents) for cat, cents in budgets.items()}
                    print(json.dumps(amounts, ensure_ascii=False))
                elif not budgets:
                    print("no budgets set")
                else:
                    for cat, cents in budgets.items():
                        print(f"{cat}\t{format_cents(cents)}")
            elif args.budget_cmd == "rm":
                cat = args.category
                if not db.delete_budget(conn, cat):
                    print(f"error: no budget for {cat}", file=sys.stderr)
                    return 1
                print(f"Removed budget for {cat}")
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
            elif not statuses:
                print("no budgets set")
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
            elif args.count:
                counts = [(cat, db.count_expenses(conn, cat)) for cat in categories]
                for cat, n in sorted(counts, key=lambda p: -p[1]):
                    print(f"{cat}\t{n}")
            elif not categories:
                print("no categories")
            else:
                for cat in categories:
                    print(cat)
        elif args.cmd == "count":
            n = db.count_expenses(conn, args.category, month=args.month)
            if args.json:
                print(json.dumps({"count": n}))
            else:
                print(n)
        elif args.cmd == "compare":
            month = args.month or date.today().strftime("%Y-%m")
            # The day before the 1st is in the previous month, including across a year boundary.
            previous = (date.fromisoformat(month + "-01") - timedelta(days=1)).strftime("%Y-%m")
            changes = compare_months(db.list_expenses(conn), month, previous)
            if not changes:
                print("no expenses")
            for cat, cur, prev in changes:
                pct = change_percent(cur, prev)
                if pct is None:
                    pct_text = "n/a"
                else:
                    pct_text = f"{'-' if pct < 0 else '+'}{abs(pct)}%"
                print(
                    f"{cat}\t{format_cents(cur)}\t{format_cents(prev)}\t"
                    f"{format_signed_cents(cur - prev)}\t{pct_text}"
                )
        elif args.cmd == "export":
            rows = db.list_expenses(conn, args.category)
            text = expenses_to_csv(rows)
            if args.output is None:
                sys.stdout.write(text)
            else:
                try:
                    with open(args.output, "w", newline="", encoding="utf-8") as f:
                        f.write(text)
                except OSError as e:
                    print(f"error: {e}", file=sys.stderr)
                    return 1
                print(f"exported {len(rows)} expenses to {args.output}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

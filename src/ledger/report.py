"""Aggregations over expenses."""

from __future__ import annotations

from collections import defaultdict

from ledger.db import Expense


def totals_by_category(expenses: list[Expense]) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for e in expenses:
        totals[e.category] += e.amount_cents
    return dict(sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])))


def monthly_totals(expenses: list[Expense]) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for e in expenses:
        totals[e.spent_on.strftime("%Y-%m")] += e.amount_cents
    return dict(sorted(totals.items()))

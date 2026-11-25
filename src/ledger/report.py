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


def average_by_category(expenses: list[Expense]) -> dict[str, int]:
    # Integer half-up rounding; built-in round() is banker's rounding. Amounts are always > 0.
    totals: dict[str, int] = defaultdict(int)
    counts: dict[str, int] = defaultdict(int)
    for e in expenses:
        totals[e.category] += e.amount_cents
        counts[e.category] += 1
    return {
        category: (2 * total + counts[category]) // (2 * counts[category])
        for category, total in sorted(totals.items())
    }

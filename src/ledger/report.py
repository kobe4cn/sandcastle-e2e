"""Aggregations over expenses."""

from __future__ import annotations

from collections import defaultdict

from ledger.db import Expense


def totals_by_category(expenses: list[Expense]) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for e in expenses:
        totals[e.category] += e.amount_cents
    return dict(sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])))


def category_share(expenses: list[Expense]) -> dict[str, float]:
    """Percentage (0-100, one decimal) of total spending per category, largest first."""
    totals = totals_by_category(expenses)
    total = sum(totals.values())
    if total == 0:
        return {}
    # Integer half-up on tenths of a percent; built-in round() is banker's rounding on floats.
    return {
        category: (2000 * cents + total) // (2 * total) / 10
        for category, cents in totals.items()
    }


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


def budget_status(
    expenses: list[Expense], budgets: dict[str, int], month: str
) -> list[tuple[str, int, int, int]]:
    """(category, spent, budget, remaining) for each budgeted category in `month` (YYYY-MM)."""
    spent: dict[str, int] = defaultdict(int)
    for e in expenses:
        if e.spent_on.strftime("%Y-%m") == month:
            spent[e.category] += e.amount_cents
    return [(cat, spent[cat], budgets[cat], budgets[cat] - spent[cat]) for cat in sorted(budgets)]

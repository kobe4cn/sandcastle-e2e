# ledger

A tiny personal expense ledger backed by SQLite. Used as the end-to-end test project for sandcastle-pipeline.

```bash
uv sync
uv run ledger add 12.50 food --note lunch   # note: at most 200 characters
uv run ledger add '$12.50' food   # leading $ is accepted; single quotes stop the shell expanding $1
uv run ledger list
uv run ledger list --limit 2   # at most 2 expenses, oldest first
uv run ledger list --reverse   # newest first; combines with --category and --limit
uv run ledger list --min 10   # only expenses of at least 10.00; combines with --category, --reverse and --limit (filters first)
uv run ledger list --max 10   # only expenses of at most 10.00; combines with --category, --min, --reverse and --limit (filters first)
uv run ledger list --json   # same, as a JSON array of objects with id, date, amount, category and note; combines with --category, --min, --max, --reverse and --limit
uv run ledger delete 3   # delete an expense by id (ids come from ledger list)
uv run ledger report
uv run ledger report --average   # average spend per expense, by category
uv run ledger report --share   # percentage of total spending, by category; not with --average
uv run ledger report --category food   # only one category; combines with --average or --share
uv run ledger budget set food 300   # monthly budget for a category
uv run ledger budget list
uv run ledger budget list --json   # same, as a JSON object, e.g. {"food": "100.00"}
uv run ledger budget rm food
uv run ledger status --month 2026-01   # spent / budget / remaining per budgeted category; default: current month
uv run ledger status --json   # same, as a JSON array of {category, spent, budget}; combines with --month
uv run ledger categories   # distinct expense categories, sorted
uv run ledger categories --json   # same, as a JSON array, e.g. ["food", "rent"]
uv run ledger count   # number of recorded expenses
uv run ledger count --category food   # number of expenses in one category
uv run ledger --version   # or: uv run ledger -V
```

## Deleting an expense

Find the id in the first column of `ledger list`, then pass it to `ledger delete`:

```bash
uv run ledger list
# 1	2026-01-02	food	12.50	lunch
# 2	2026-01-03	coffee	4.20
uv run ledger delete 1
# deleted #1
```

If no expense has that id, nothing is deleted: the command prints `error: no expense #<id>`
(e.g. `error: no expense #9`) to stderr and exits with status 1. A non-integer id is a usage
error (exit status 2). Ids are never reused, so a deleted id stays unused.

## Budgets

Each category can have one monthly budget. Note the argument order of `budget set`: category
first, then amount (the reverse of `ledger add`). `ledger status` compares a month's spending
with the budgets:

```bash
uv run ledger add 12.50 food --on 2026-01-02
# Added #1
uv run ledger budget set food 10
uv run ledger budget set travel 50
uv run ledger budget list
# food	10.00
# travel	50.00
uv run ledger budget list --json
# {"food": "10.00", "travel": "50.00"}
uv run ledger status --month 2026-01
# food	12.50	10.00	-2.50
# travel	0.00	50.00	50.00
uv run ledger status --month 2026-01 --json
# [{"category": "food", "spent": "12.50", "budget": "10.00"}, {"category": "travel", "spent": "0.00", "budget": "50.00"}]
uv run ledger budget rm travel
# removed budget for travel
```

`budget set` prints nothing on success. Setting a category again replaces its budget, and
categories are stored trimmed and lowercased (`Food` and `food` are the same budget). An invalid
amount prints e.g. `error: amount must be positive` to stderr and exits with status 2.

`budget list` prints one tab-separated `<category> <amount>` line per budget, sorted by
category, and nothing when there are no budgets (`--json` then prints `{}`).

`budget rm` on a category without a budget prints `error: no budget for <category>` to stderr
and exits with status 1.

`status` prints tab-separated `<category> <spent> <budget> <remaining>` lines, one per
budgeted category, with no header; remaining is negative when the category is over budget.
Categories without a budget are not listed. Without `--month` it reports the current month. `--json`
prints an array of objects with `category`, `spent` and `budget` only (no remaining). A
malformed month such as `--month 2026-13` is a usage error (exit status 2).

## Spending share by category

`ledger report --share` prints each category's percentage of total spending over all recorded
expenses, one tab-separated `<category> <percent>` line per category with one decimal place,
largest first (ties sorted by category name). It cannot be combined with `--average`; with
`--category` the single category is always 100.0%:

```bash
uv run ledger add 50 rent --on 2026-01-01
uv run ledger add 12.50 food --on 2026-01-02
uv run ledger add 25 food --on 2026-01-03
uv run ledger add 12.50 coffee --on 2026-01-03
uv run ledger report --share
# rent	50.0%
# food	37.5%
# coffee	12.5%
uv run ledger report --share --category food
# food	100.0%
```

Percentages are rounded to one decimal place, so they do not always add up to exactly 100.0%.

## Development

- Tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Types: `uv run mypy`

Money is always integer cents (`src/ledger/money.py`); format only for display.
The CLI reads the database path from `LEDGER_DB`.

# ledger

A tiny personal expense ledger backed by SQLite. Used as the end-to-end test project for sandcastle-pipeline.

```bash
uv sync
uv run ledger add 12.50 food --note lunch
uv run ledger add '$12.50' food   # leading $ is accepted; single quotes stop the shell expanding $1
uv run ledger list
uv run ledger list --limit 2   # at most 2 expenses, oldest first
uv run ledger list --reverse   # newest first; combines with --category and --limit
uv run ledger delete 3   # delete an expense by id (ids come from ledger list)
uv run ledger report
uv run ledger report --average   # average spend per expense, by category
uv run ledger report --category food   # only one category; combines with --average
uv run ledger budget set food 300   # monthly budget for a category
uv run ledger budget list
uv run ledger budget rm food
uv run ledger status --month 2026-01   # spent / budget / remaining per budgeted category; default: current month
uv run ledger categories   # distinct expense categories, sorted
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

## Development

- Tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Types: `uv run mypy`

Money is always integer cents (`src/ledger/money.py`); format only for display.
The CLI reads the database path from `LEDGER_DB`.

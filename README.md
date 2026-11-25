# ledger

A tiny personal expense ledger backed by SQLite. Used as the end-to-end test project for sandcastle-pipeline.

```bash
uv sync
uv run ledger add 12.50 food --note lunch
uv run ledger list
uv run ledger report
uv run ledger report --average   # average spend per expense, by category
uv run ledger budget set food 300   # monthly budget for a category
uv run ledger budget list
uv run ledger budget rm food
uv run ledger status --month 2026-01   # spent / budget / remaining per budgeted category; default: current month
uv run ledger categories   # distinct expense categories, sorted
uv run ledger --version   # or: uv run ledger -V
```

## Development

- Tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Types: `uv run mypy`

Money is always integer cents (`src/ledger/money.py`); format only for display.
The CLI reads the database path from `LEDGER_DB`.

# ledger

A tiny personal expense ledger backed by SQLite. Used as the end-to-end test project for sandcastle-pipeline.

```bash
uv sync
uv run ledger add 12.50 food --note lunch
uv run ledger list
uv run ledger report
uv run ledger report --average   # average spend per expense, by category
uv run ledger --version   # or: uv run ledger -V
```

## Development

- Tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Types: `uv run mypy`

Money is always integer cents (`src/ledger/money.py`); format only for display.
The CLI reads the database path from `LEDGER_DB`.

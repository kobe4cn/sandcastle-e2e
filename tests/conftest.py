from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from ledger import db


@pytest.fixture
def conn(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    c = db.connect(str(tmp_path / "test.db"))
    yield c
    c.close()


@pytest.fixture
def ledger_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the CLI at a fresh database file."""
    path = tmp_path / "cli.db"
    monkeypatch.setenv("LEDGER_DB", str(path))
    return path

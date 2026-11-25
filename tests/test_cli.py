from __future__ import annotations

from importlib.metadata import version
from pathlib import Path

import pytest

from ledger.cli import main


def test_add_list_report(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "12.50", "food", "--on", "2026-01-02", "--note", "lunch"]) == 0
    assert main(["add", "3", "travel", "--on", "2026-01-03"]) == 0
    capsys.readouterr()
    assert main(["list"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out == ["1\t2026-01-02\tfood\t12.50\tlunch", "2\t2026-01-03\ttravel\t3.00\t"]
    assert main(["report"]) == 0
    assert capsys.readouterr().out.splitlines() == ["food\t12.50", "travel\t3.00"]


def test_add_rejects_bad_amount(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "abc", "food"]) == 2
    assert "not a number" in capsys.readouterr().err


def test_delete_missing(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["delete", "9"]) == 1
    assert "no expense #9" in capsys.readouterr().err


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_version(flag: str, ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main([flag])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert captured.out == f"ledger {version('ledger')}\n"
    assert captured.err == ""


def test_budget_set_and_list(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["budget", "set", "travel", "50"]) == 0
    assert main(["budget", "set", "Food", "200"]) == 0
    assert main(["budget", "set", "food", "300"]) == 0
    capsys.readouterr()
    assert main(["budget", "list"]) == 0
    assert capsys.readouterr().out.splitlines() == ["food\t300.00", "travel\t50.00"]


@pytest.mark.parametrize("amount", ["abc", "0", "1.234"])
def test_budget_set_rejects_bad_amount(
    amount: str, ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["budget", "set", "food", amount]) == 2
    assert capsys.readouterr().err.startswith("error: ")
    assert main(["budget", "list"]) == 0
    assert capsys.readouterr().out == ""

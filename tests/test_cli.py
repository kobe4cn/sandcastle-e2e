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


def test_add_accepts_leading_dollar_sign(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "$12.50", "food", "--on", "2026-01-02"]) == 0
    capsys.readouterr()
    assert main(["list"]) == 0
    assert capsys.readouterr().out.splitlines() == ["1\t2026-01-02\tfood\t12.50\t"]


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


def test_budget_rm_missing(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["budget", "rm", "food"]) == 1
    assert capsys.readouterr().err.startswith("error: ")


def test_budget_rm(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["budget", "set", "food", "100"]) == 0
    capsys.readouterr()
    assert main(["budget", "rm", "food"]) == 0
    assert capsys.readouterr().out == "removed budget for food\n"
    assert main(["budget", "list"]) == 0
    assert capsys.readouterr().out == ""


def test_report_average_sorted_by_category(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "3", "travel", "--on", "2026-01-02"]) == 0
    assert main(["add", "10", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "20", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "1.50", "books", "--on", "2026-01-02"]) == 0
    capsys.readouterr()
    assert main(["report", "--average"]) == 0
    assert capsys.readouterr().out.splitlines() == ["books\t1.50", "food\t15.00", "travel\t3.00"]


def test_report_category_prints_only_that_category(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "10.00", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "20.00", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "3", "travel", "--on", "2026-01-02"]) == 0
    capsys.readouterr()
    assert main(["report", "--category", "food"]) == 0
    assert capsys.readouterr().out.splitlines() == ["food\t30.00"]


def test_report_category_with_average_prints_only_that_category(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "10.00", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "20.00", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "3", "travel", "--on", "2026-01-02"]) == 0
    capsys.readouterr()
    assert main(["report", "--category", "FOOD", "--average"]) == 0
    assert capsys.readouterr().out.splitlines() == ["food\t15.00"]


def test_report_unknown_category_prints_nothing(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "10.00", "food", "--on", "2026-01-02"]) == 0
    capsys.readouterr()
    assert main(["report", "--category", "rent"]) == 0
    assert capsys.readouterr().out == ""


def test_report_average_rounds_half_up(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "1.00", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "1.01", "food", "--on", "2026-01-02"]) == 0
    capsys.readouterr()
    assert main(["report", "--average"]) == 0
    assert capsys.readouterr().out.splitlines() == ["food\t1.01"]


def test_report_average_empty(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["report", "--average"]) == 0
    assert capsys.readouterr().out == ""


def test_status_shows_spent_budget_and_negative_remaining(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "12.50", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "99", "food", "--on", "2026-02-01"]) == 0
    assert main(["budget", "set", "food", "10"]) == 0
    assert main(["budget", "set", "travel", "50"]) == 0
    capsys.readouterr()
    assert main(["status", "--month", "2026-01"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "food\t12.50\t10.00\t-2.50",
        "travel\t0.00\t50.00\t50.00",
    ]


def test_status_accepts_month_without_zero_padding(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "3", "food", "--on", "2026-01-02"]) == 0
    assert main(["budget", "set", "food", "10"]) == 0
    capsys.readouterr()
    assert main(["status", "--month", "2026-1"]) == 0
    assert capsys.readouterr().out.splitlines() == ["food\t3.00\t10.00\t7.00"]


def test_status_rejects_invalid_month(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["status", "--month", "2026-13"])
    assert exc.value.code == 2
    assert "invalid month" in capsys.readouterr().err


def test_status_defaults_to_current_month(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # `add` without --on records today, so the default month must pick it up.
    assert main(["add", "4", "food"]) == 0
    assert main(["add", "99", "food", "--on", "2000-01-01"]) == 0
    assert main(["budget", "set", "food", "10"]) == 0
    capsys.readouterr()
    assert main(["status"]) == 0
    assert capsys.readouterr().out.splitlines() == ["food\t4.00\t10.00\t6.00"]


def test_categories_distinct_sorted(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "3", "travel", "--on", "2026-01-02"]) == 0
    assert main(["add", "10", "Food", "--on", "2026-01-02"]) == 0
    assert main(["add", "20", "food ", "--on", "2026-01-03"]) == 0
    assert main(["add", "1.50", "books", "--on", "2026-01-03"]) == 0
    assert main(["budget", "set", "rent", "1000"]) == 0
    capsys.readouterr()
    assert main(["categories"]) == 0
    assert capsys.readouterr().out.splitlines() == ["books", "food", "travel"]


def test_categories_empty(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["categories"]) == 0
    assert capsys.readouterr().out == ""


def test_count_empty_prints_zero(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["count"]) == 0
    assert capsys.readouterr().out.splitlines() == ["0"]


def test_count_prints_total_expenses(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "10", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "3", "travel", "--on", "2026-01-02"]) == 0
    assert main(["add", "5", "Food", "--on", "2026-01-03"]) == 0
    capsys.readouterr()
    assert main(["count"]) == 0
    assert capsys.readouterr().out.splitlines() == ["3"]


def test_count_with_category_counts_only_that_category(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "10", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "3", "travel", "--on", "2026-01-02"]) == 0
    assert main(["add", "5", "Food", "--on", "2026-01-03"]) == 0
    capsys.readouterr()
    assert main(["count", "--category", "FOOD"]) == 0
    assert capsys.readouterr().out.splitlines() == ["2"]


def test_list_limit_prints_first_n(ledger_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "1", "food", "--on", "2026-01-03"]) == 0
    assert main(["add", "2", "food", "--on", "2026-01-01"]) == 0
    assert main(["add", "3", "travel", "--on", "2026-01-02"]) == 0
    capsys.readouterr()
    assert main(["list", "--limit", "2"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "2\t2026-01-01\tfood\t2.00\t",
        "3\t2026-01-02\ttravel\t3.00\t",
    ]
    assert main(["list"]) == 0
    assert len(capsys.readouterr().out.splitlines()) == 3


@pytest.mark.parametrize("limit_args", [["--limit", "0"], ["--limit=-1"]])
def test_list_rejects_non_positive_limit(
    ledger_db: Path, capsys: pytest.CaptureFixture[str], limit_args: list[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["list", *limit_args])
    assert exc.value.code == 2
    assert "invalid limit" in capsys.readouterr().err


def _add_three_out_of_order(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["add", "1", "food", "--on", "2026-01-03"]) == 0
    assert main(["add", "2", "food", "--on", "2026-01-01"]) == 0
    assert main(["add", "3", "travel", "--on", "2026-01-02"]) == 0
    capsys.readouterr()


def test_list_reverse_prints_newest_first(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _add_three_out_of_order(capsys)
    assert main(["list"]) == 0
    oldest_first = capsys.readouterr().out.splitlines()
    assert main(["list", "--reverse"]) == 0
    newest_first = capsys.readouterr().out.splitlines()
    assert newest_first == [
        "1\t2026-01-03\tfood\t1.00\t",
        "3\t2026-01-02\ttravel\t3.00\t",
        "2\t2026-01-01\tfood\t2.00\t",
    ]
    assert newest_first == oldest_first[::-1]


def test_list_reverse_with_limit_prints_n_newest(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _add_three_out_of_order(capsys)
    assert main(["list", "--reverse", "--limit", "2"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "1\t2026-01-03\tfood\t1.00\t",
        "3\t2026-01-02\ttravel\t3.00\t",
    ]


def test_list_reverse_with_category_filters_then_reverses(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _add_three_out_of_order(capsys)
    assert main(["list", "--reverse", "--category", "FOOD"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "1\t2026-01-03\tfood\t1.00\t",
        "2\t2026-01-01\tfood\t2.00\t",
    ]


def test_list_min_hides_expenses_below_amount(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "9.99", "food", "--on", "2026-01-01"]) == 0
    assert main(["add", "10.00", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "12.50", "travel", "--on", "2026-01-03"]) == 0
    capsys.readouterr()
    assert main(["list", "--min", "10"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "2\t2026-01-02\tfood\t10.00\t",
        "3\t2026-01-03\ttravel\t12.50\t",
    ]


@pytest.mark.parametrize(
    "min_args", [["--min", "abc"], ["--min", "0"], ["--min=-1"], ["--min", "1.234"]]
)
def test_list_rejects_invalid_min(
    ledger_db: Path, capsys: pytest.CaptureFixture[str], min_args: list[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["list", *min_args])
    assert exc.value.code == 2
    assert "invalid amount" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("list_args", "expected"),
    [
        (["--min", "3", "--limit", "1"], ["3\t2026-01-02\ttravel\t3.00\t"]),
        (["--reverse", "--min", "2", "--limit", "1"], ["3\t2026-01-02\ttravel\t3.00\t"]),
        (["--category", "FOOD", "--min", "2"], ["2\t2026-01-01\tfood\t2.00\t"]),
    ],
)
def test_list_min_filters_before_category_reverse_and_limit(
    ledger_db: Path,
    capsys: pytest.CaptureFixture[str],
    list_args: list[str],
    expected: list[str],
) -> None:
    _add_three_out_of_order(capsys)
    assert main(["list", *list_args]) == 0
    assert capsys.readouterr().out.splitlines() == expected


def test_list_max_hides_expenses_above_amount(
    ledger_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["add", "9.99", "food", "--on", "2026-01-01"]) == 0
    assert main(["add", "10.00", "food", "--on", "2026-01-02"]) == 0
    assert main(["add", "12.50", "travel", "--on", "2026-01-03"]) == 0
    capsys.readouterr()
    assert main(["list", "--max", "10"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "1\t2026-01-01\tfood\t9.99\t",
        "2\t2026-01-02\tfood\t10.00\t",
    ]


@pytest.mark.parametrize(
    "max_args", [["--max", "abc"], ["--max", "0"], ["--max=-1"], ["--max", "1.234"]]
)
def test_list_rejects_invalid_max(
    ledger_db: Path, capsys: pytest.CaptureFixture[str], max_args: list[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["list", *max_args])
    assert exc.value.code == 2
    assert "invalid amount" in capsys.readouterr().err

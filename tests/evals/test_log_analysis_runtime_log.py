from __future__ import annotations

from pathlib import Path

import pytest

from aidd.evals.log_analysis import (
    parse_runtime_log,
    parse_runtime_log_text,
    summarize_first_failure,
)


def test_parse_runtime_log_text_classifies_coarse_events() -> None:
    runtime_log_text = "\n".join(
        (
            "Stage plan -> research",
            "Validator verdict: fail",
            "Need clarification from user?",
            "Repair attempt #1",
            "WARNING: nearing token budget",
            "Traceback (most recent call last):",
            "plain informational line",
        )
    )

    events = parse_runtime_log_text(runtime_log_text)

    assert [event.category for event in events] == [
        "stage",
        "validator",
        "question",
        "repair",
        "warning",
        "error",
        "info",
    ]
    assert events[0].line_number == 1
    assert events[-1].line_number == 7


def test_parse_runtime_log_ignores_blank_lines(tmp_path: Path) -> None:
    runtime_log_path = tmp_path / "runtime.log"
    runtime_log_path.write_text(
        "line one\n\n   \nline two\n",
        encoding="utf-8",
    )

    events = parse_runtime_log(runtime_log_path)

    assert [event.message for event in events] == ["line one", "line two"]
    assert [event.line_number for event in events] == [1, 4]


def test_parse_runtime_log_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="runtime.log file does not exist"):
        parse_runtime_log(tmp_path / "missing-runtime.log")


def test_summarize_first_failure_returns_first_error_signal() -> None:
    summary = summarize_first_failure(
        runtime_log_text="\n".join(
            (
                "initial info",
                "validator says fail",
                "runtime failed with exit 1",
                "another error line",
            )
        )
    )

    assert summary == "line 3: runtime failed with exit 1"


def test_summarize_first_failure_reports_absence_of_error_signal() -> None:
    summary = summarize_first_failure(runtime_log_text="all good\nstill good\n")

    assert summary == "no failure signal found"

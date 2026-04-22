from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.evals.log_analysis import (
    parse_stage_metadata_validation_failures,
    parse_stage_metadata_validation_failures_text,
    parse_validator_report_failures,
    parse_validator_report_failures_text,
)


def test_parse_validator_report_failures_extracts_findings() -> None:
    report_text = "\n".join(
        (
            "# Validator Report",
            "",
            "## Structural checks",
            "",
            "- `STRUCT-001` (`high`) in "
            "`workitems/WI-001/stages/qa/stage-result.md`: missing section",
            "",
            "## Result",
            "",
            "- Verdict: `fail`",
        )
    )

    events = parse_validator_report_failures_text(report_text)

    assert len(events) == 1
    assert events[0].category == "validator"
    assert "STRUCT-001 (high)" in events[0].message
    assert events[0].line_number == 5


def test_parse_validator_report_failures_uses_verdict_when_findings_missing() -> None:
    events = parse_validator_report_failures_text(
        "# Validator Report\n\n## Result\n\n- Verdict: `fail`\n"
    )

    assert len(events) == 1
    assert events[0].category == "validator"
    assert events[0].message == "validator report verdict is fail"


def test_parse_validator_report_failures_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="validator-report.md file does not exist"):
        parse_validator_report_failures(tmp_path / "missing-validator-report.md")


def test_parse_stage_metadata_validation_failures_extracts_status_and_repair_signals() -> None:
    payload = {
        "stage": "qa",
        "status_history": [
            {"status": "running", "changed_at_utc": "2026-04-22T09:00:00Z"},
            {"status": "repair_needed", "changed_at_utc": "2026-04-22T09:01:00Z"},
            {"status": "failed", "changed_at_utc": "2026-04-22T09:02:00Z"},
        ],
        "repair_history": [
            {"attempt_number": 1, "outcome": "failed validation"},
            {"attempt_number": 2, "outcome": "succeeded"},
        ],
    }

    events = parse_stage_metadata_validation_failures_text(json.dumps(payload))

    assert [event.category for event in events] == ["validator", "error", "validator"]
    assert "status `repair_needed`" in events[0].message
    assert "status `failed`" in events[1].message
    assert "repair attempt `1`" in events[2].message


def test_parse_stage_metadata_validation_failures_rejects_invalid_json() -> None:
    with pytest.raises(ValueError, match="Invalid JSON in stage metadata payload"):
        parse_stage_metadata_validation_failures_text("{not-json}")


def test_parse_stage_metadata_validation_failures_rejects_non_object_payload() -> None:
    with pytest.raises(ValueError, match="stage metadata payload must be a JSON object"):
        parse_stage_metadata_validation_failures_text('["not-object"]')


def test_parse_stage_metadata_validation_failures_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="stage metadata file does not exist"):
        parse_stage_metadata_validation_failures(tmp_path / "missing-stage-metadata.json")

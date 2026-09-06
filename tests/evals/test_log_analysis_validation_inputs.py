from __future__ import annotations

import pytest

from aidd.evals.log_analysis import (
    parse_validator_report_failures_text,
)
from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.protocol import ValidatorReportProtocolError
from aidd.validators.reports import render_validator_report


def test_parse_validator_report_failures_extracts_findings() -> None:
    report_text = render_validator_report(
        (
            ValidationFinding(
                code="STRUCT-MISSING-REQUIRED-SECTION",
                severity="high",
                location=ValidationIssueLocation("workitems/WI-001/stages/qa/stage-result.md"),
                message="missing section",
            ),
        )
    )

    events = parse_validator_report_failures_text(report_text)

    assert len(events) == 1
    assert events[0].category == "validator"
    assert "STRUCT-MISSING-REQUIRED-SECTION (high)" in events[0].message
    assert report_text.splitlines()[events[0].line_number - 1].startswith("- `STRUCT-")


def test_parse_validator_report_failures_rejects_verdict_without_findings() -> None:
    report = render_validator_report(()).replace("- Verdict: `pass`", "- Verdict: `fail`")
    with pytest.raises(ValidatorReportProtocolError, match="requires at least one"):
        parse_validator_report_failures_text(report)


def test_log_analysis_reader_rejects_retired_protocol_vocabulary() -> None:
    with pytest.raises(ValidatorReportProtocolError):
        parse_validator_report_failures_text(
            "## Structural checks\n\n"
            "- `STRUCT-MISSING-DOCUMENT` (`high`) in `plan.md`: missing.\n\n"
            "## Result\n\n- Validator verdict: `fail`\n"
        )


def test_log_analysis_reader_rejects_unknown_protocol_code() -> None:
    with pytest.raises(ValidatorReportProtocolError):
        parse_validator_report_failures_text(
            "## Semantic checks\n\n- `SEM-UNKNOWN-CODE` (`high`) in `plan.md`: unknown.\n"
        )

from __future__ import annotations

from pathlib import Path

import pytest

from aidd.validators.models import ValidationFinding, ValidationIssueLocation


def test_validation_finding_normalizes_code_and_uses_default_severity() -> None:
    finding = ValidationFinding(
        code=" struct-missing-document ",
        message=" Missing required document. ",
    )

    assert finding.code == "STRUCT-MISSING-DOCUMENT"
    assert finding.severity == "high"
    assert finding.message == "Missing required document."
    assert finding.location is None


def test_validation_finding_rejects_invalid_code_or_empty_message() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ValidationFinding(code=" ", message="valid message")

    with pytest.raises(ValueError, match="subsystem-prefixed format"):
        ValidationFinding(code="INVALIDCODE", message="valid message")

    with pytest.raises(ValueError, match="must not be empty"):
        ValidationFinding(code="STRUCT-INVALID", message=" ")


def test_validation_issue_location_rejects_absolute_or_invalid_line_number() -> None:
    with pytest.raises(ValueError, match="workspace-relative"):
        ValidationIssueLocation(workspace_relative_path=str(Path("/abs/path.md")))

    with pytest.raises(ValueError, match="line number must be positive"):
        ValidationIssueLocation(
            workspace_relative_path="workitems/WI-001/stages/qa/qa-report.md",
            line_number=0,
        )

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from aidd.validators.protocol import (
    DOCUMENT_READ_FAILURES,
    VALIDATOR_FINDING_CODES,
    VALIDATOR_REPORT_FIELDS,
    DocumentReadFailureKind,
    ValidatorReportProtocolError,
    parse_validator_report,
    resolve_document_read_failure,
    resolve_validator_finding_code,
    resolve_validator_report_field,
    validator_report_field,
)

_CODE_PATTERN = re.compile(r"^(?:CROSS|INTERVIEW|SEM|STRUCT)-[A-Z0-9-]+$")
_NON_FINDING_PROTOCOL_LITERALS = {"STRUCT-MISSING"}


def test_protocol_registry_is_collision_free() -> None:
    assert len({field.key for field in VALIDATOR_REPORT_FIELDS}) == len(VALIDATOR_REPORT_FIELDS)
    labels = [field.label.casefold() for field in VALIDATOR_REPORT_FIELDS]
    assert len(set(labels)) == len(labels)
    assert len({spec.code for spec in VALIDATOR_FINDING_CODES}) == len(VALIDATOR_FINDING_CODES)


def test_protocol_registry_resolves_only_current_fields() -> None:
    assert validator_report_field("verdict").label == "Verdict"
    assert resolve_validator_report_field("Verdict").key == "verdict"
    assert (
        resolve_validator_report_field("Repair required for progression").key == "repair_required"
    )
    for label in ("Validator verdict", "Repair required", "Validation result"):
        with pytest.raises(ValidatorReportProtocolError, match="Unknown.*field"):
            resolve_validator_report_field(label)


def test_document_read_failure_registry_maps_canonical_kinds_to_finding_codes() -> None:
    assert tuple(spec.kind for spec in DOCUMENT_READ_FAILURES) == (
        DocumentReadFailureKind.NON_FILE,
        DocumentReadFailureKind.UNREADABLE,
        DocumentReadFailureKind.INVALID_UTF8,
        DocumentReadFailureKind.MALFORMED_FRONTMATTER,
    )
    assert len({spec.kind for spec in DOCUMENT_READ_FAILURES}) == len(DOCUMENT_READ_FAILURES)
    assert len({spec.code for spec in DOCUMENT_READ_FAILURES}) == len(DOCUMENT_READ_FAILURES)
    assert all(
        resolve_document_read_failure(spec.kind) is spec
        and spec.code in {finding.code for finding in VALIDATOR_FINDING_CODES}
        for spec in DOCUMENT_READ_FAILURES
    )


def test_document_read_failure_registry_rejects_unknown_kind() -> None:
    with pytest.raises(ValidatorReportProtocolError, match="Unknown document-read failure"):
        resolve_document_read_failure("missing")


def test_document_read_failure_registry_rejects_unknown_finding_code() -> None:
    with pytest.raises(ValidatorReportProtocolError, match="Unknown validator finding"):
        resolve_validator_finding_code("STRUCT-UNKNOWN-DOCUMENT-READ")


@pytest.mark.parametrize(
    "retired",
    (
        "STRUCT-MISSING-DOCUMENT",
        "STRUCT-MISSING-HEADING",
        "STRUCT-EMPTY-SECTION",
        "CROSS-REFERENCE-MISMATCH",
    ),
)
def test_protocol_registry_rejects_retired_codes(retired: str) -> None:
    with pytest.raises(ValidatorReportProtocolError, match="Unknown validator finding"):
        resolve_validator_finding_code(retired)


def test_unknown_finding_code_is_rejected() -> None:
    with pytest.raises(ValidatorReportProtocolError, match="Unknown validator finding"):
        resolve_validator_finding_code("SEM-NEW-UNDECLARED-CODE")


def test_all_validator_finding_literals_are_registered() -> None:
    source_root = Path(__file__).parents[2] / "src" / "aidd"
    emitted_literals: set[str] = set()
    for source_path in source_root.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        emitted_literals.update(
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and _CODE_PATTERN.fullmatch(node.value)
            and node.value not in _NON_FINDING_PROTOCOL_LITERALS
        )

    registered = {spec.code for spec in VALIDATOR_FINDING_CODES}
    assert emitted_literals <= registered


def test_validator_report_reader_rejects_incomplete_historical_reports() -> None:
    with pytest.raises(
        ValidatorReportProtocolError, match="missing required current-format fields"
    ):
        parse_validator_report("## Result\n\n- Verdict: `pass`\n")


def test_validator_report_reader_rejects_fail_with_optional_only_corrections() -> None:
    with pytest.raises(
        ValidatorReportProtocolError,
        match="fail-causing findings cannot be optional",
    ):
        parse_validator_report(
            """# Validator Report

## Summary

- Total issues: 1
- Blocking issues: no
- Affected documents: none
- Dominant failure categories: none

## Semantic checks

- `SEM-PLACEHOLDER-CONTENT` (`low`) in `plan.md`: Placeholder remains.

## Result

- Verdict: `fail`
- Repair required for progression: no
"""
        )


def test_validator_report_reader_treats_low_findings_as_progression_blocking() -> None:
    report = parse_validator_report(
        """# Validator Report

## Summary

- Total issues: 1
- Blocking issues: yes
- Affected documents: `plan.md`
- Dominant failure categories: semantic checks

## Semantic checks

- `SEM-PLACEHOLDER-CONTENT` (`low`) in `plan.md`: Placeholder remains.

## Result

- Verdict: `fail`
- Repair required for progression: yes
"""
    )

    assert report.verdict == "fail"
    assert report.findings[0].severity == "low"


def test_validator_report_reader_keeps_advisory_observations_out_of_verdict() -> None:
    report = parse_validator_report(
        """# Validator Report

## Summary

- Total issues: 0
- Blocking issues: no
- Affected documents: none
- Dominant failure categories: none

## Advisory observations

- `SEM-RISK-UNDERREPORT` (`low`) in `plan.md`: A non-blocking observation.

## Result

- Verdict: `pass`
- Repair required for progression: no
"""
    )

    assert report.findings == ()
    assert len(report.advisories) == 1
    assert report.advisories[0].code == "SEM-RISK-UNDERREPORT"
    assert report.verdict == "pass"


@pytest.mark.parametrize(
    "markdown",
    [
        "## Result\n\n- Validation result: `fail`\n",
        ("## Semantic checks\n\n- `SEM-UNDECLARED-CODE` (`high`) in `plan.md`: Unknown.\n"),
        (
            "## Structural checks\n\n"
            "- `SEM-PLACEHOLDER-CONTENT` (`high`) in `plan.md`: Wrong section.\n"
        ),
    ],
)
def test_validator_report_reader_rejects_undeclared_or_misplaced_vocabulary(
    markdown: str,
) -> None:
    with pytest.raises(ValidatorReportProtocolError):
        parse_validator_report(markdown)

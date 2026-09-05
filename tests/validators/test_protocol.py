from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from aidd.validators.protocol import (
    DOCUMENT_READ_FAILURES,
    VALIDATOR_FINDING_CODES,
    VALIDATOR_REPORT_FIELDS,
    VALIDATOR_REPORT_PROTOCOL_VERSION,
    DocumentReadFailureKind,
    ValidatorReportProtocolError,
    ValidatorReportSection,
    canonical_validator_finding_code,
    parse_validator_report,
    resolve_document_read_failure,
    resolve_document_read_failure_code,
    resolve_validator_finding_code,
    resolve_validator_report_field,
    validator_report_field,
)

_CODE_PATTERN = re.compile(r"^(?:CROSS|INTERVIEW|SEM|STRUCT)-[A-Z0-9-]+$")
_NON_FINDING_PROTOCOL_LITERALS = {"STRUCT-MISSING"}


def test_protocol_registry_is_versioned_and_collision_free() -> None:
    assert VALIDATOR_REPORT_PROTOCOL_VERSION == 1
    assert len({field.key for field in VALIDATOR_REPORT_FIELDS}) == len(
        VALIDATOR_REPORT_FIELDS
    )
    labels = [
        label.casefold()
        for field in VALIDATOR_REPORT_FIELDS
        for label in (field.label, *field.aliases)
    ]
    assert len(set(labels)) == len(labels)
    assert len({spec.code for spec in VALIDATOR_FINDING_CODES}) == len(
        VALIDATOR_FINDING_CODES
    )


def test_protocol_registry_resolves_fields_and_declared_aliases() -> None:
    assert validator_report_field("verdict").label == "Verdict"
    assert resolve_validator_report_field("Validator verdict").key == "verdict"
    assert resolve_validator_report_field("Repair required").key == "repair_required"
    with pytest.raises(ValidatorReportProtocolError, match="Unknown.*field"):
        resolve_validator_report_field("Validation result")


def test_document_read_failure_registry_is_canonical_and_bidirectional() -> None:
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
        and resolve_document_read_failure_code(spec.code) is spec
        and spec.finding_code == spec.code
        and spec.code in {finding.code for finding in VALIDATOR_FINDING_CODES}
        for spec in DOCUMENT_READ_FAILURES
    )


@pytest.mark.parametrize("value", ("missing", "STRUCT-UNKNOWN-DOCUMENT-READ"))
def test_document_read_failure_registry_rejects_unknown_values(value: str) -> None:
    resolver = (
        resolve_document_read_failure_code
        if value.startswith("STRUCT-")
        else resolve_document_read_failure
    )
    with pytest.raises(ValidatorReportProtocolError, match="Unknown document-read failure"):
        resolver(value)


@pytest.mark.parametrize(
    ("legacy", "canonical"),
    [
        ("STRUCT-MISSING-DOCUMENT", "STRUCT-MISSING-REQUIRED-DOCUMENT"),
        ("STRUCT-MISSING-HEADING", "STRUCT-MISSING-REQUIRED-SECTION"),
        ("STRUCT-EMPTY-SECTION", "STRUCT-EMPTY-REQUIRED-SECTION"),
    ],
)
def test_protocol_registry_maps_unambiguous_legacy_codes(
    legacy: str, canonical: str
) -> None:
    assert canonical_validator_finding_code(legacy) == canonical
    with pytest.raises(ValidatorReportProtocolError, match="cannot be written"):
        resolve_validator_finding_code(legacy, for_write=True)


def test_ambiguous_legacy_code_remains_read_only_without_replacement() -> None:
    spec = resolve_validator_finding_code("CROSS-REFERENCE-MISMATCH")
    assert spec.status == "legacy"
    assert spec.replacement is None
    assert spec.section is ValidatorReportSection.CROSS_DOCUMENT


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


def test_validator_report_reader_normalizes_declared_legacy_vocabulary() -> None:
    canonical = parse_validator_report(
        """# Validator Report

## Structural checks

- `STRUCT-MISSING-REQUIRED-DOCUMENT` (`high`) in `plan.md`: Missing document.

## Result

- Verdict: `fail`
- Repair required for progression: yes
"""
    )
    legacy = parse_validator_report(
        """# Validator Report

## Structural checks

- `STRUCT-MISSING-DOCUMENT` (`high`) in `plan.md`: Missing document.

## Result

- Validator verdict: `fail`
- Repair required: yes
"""
    )

    assert legacy.verdict == canonical.verdict == "fail"
    assert legacy.findings == canonical.findings
    assert all(field.used_legacy_alias for field in legacy.fields)


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
        (
            "## Semantic checks\n\n"
            "- `SEM-UNDECLARED-CODE` (`high`) in `plan.md`: Unknown.\n"
        ),
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

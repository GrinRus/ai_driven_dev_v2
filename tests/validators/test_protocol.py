from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from aidd.validators.protocol import (
    VALIDATOR_FINDING_CODES,
    VALIDATOR_REPORT_FIELDS,
    VALIDATOR_REPORT_PROTOCOL_VERSION,
    ValidatorReportProtocolError,
    ValidatorReportSection,
    canonical_validator_finding_code,
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

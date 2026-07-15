from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Literal

VALIDATOR_REPORT_PROTOCOL_VERSION = 1

ProtocolEntryStatus = Literal["canonical", "legacy"]


class ValidatorReportProtocolError(ValueError):
    """Raised when validator-report protocol vocabulary is unknown or invalid."""


class ValidatorReportSection(StrEnum):
    SUMMARY = "Summary"
    STRUCTURAL = "Structural checks"
    SEMANTIC = "Semantic checks"
    CROSS_DOCUMENT = "Cross-document checks"
    RESULT = "Result"


@dataclass(frozen=True, slots=True)
class ValidatorReportFieldSpec:
    key: str
    label: str
    section: ValidatorReportSection
    required: bool = True
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidatorFindingCodeSpec:
    code: str
    section: ValidatorReportSection
    status: ProtocolEntryStatus = "canonical"
    replacement: str | None = None


VALIDATOR_REPORT_FIELDS = (
    ValidatorReportFieldSpec("total_issues", "Total issues", ValidatorReportSection.SUMMARY),
    ValidatorReportFieldSpec(
        "blocking_issues", "Blocking issues", ValidatorReportSection.SUMMARY
    ),
    ValidatorReportFieldSpec(
        "affected_documents", "Affected documents", ValidatorReportSection.SUMMARY
    ),
    ValidatorReportFieldSpec(
        "dominant_failure_categories",
        "Dominant failure categories",
        ValidatorReportSection.SUMMARY,
    ),
    ValidatorReportFieldSpec(
        "finding_occurrences",
        "Finding occurrences",
        ValidatorReportSection.SUMMARY,
        required=False,
    ),
    ValidatorReportFieldSpec(
        "verdict",
        "Verdict",
        ValidatorReportSection.RESULT,
        aliases=("Validator verdict",),
    ),
    ValidatorReportFieldSpec(
        "repair_required",
        "Repair required for progression",
        ValidatorReportSection.RESULT,
        aliases=("Repair required",),
    ),
)

_STRUCTURAL_CODES = (
    "INTERVIEW-MALFORMED-DOCUMENT",
    "STRUCT-DUPLICATE-REQUIRED-SECTION",
    "STRUCT-EMPTY-REQUIRED-SECTION",
    "STRUCT-MISSING-REQUIRED-DOCUMENT",
    "STRUCT-MISSING-REQUIRED-SECTION",
    "STRUCT-OUTPUT-PROMOTED",
    "STRUCT-STALE-STAGE-RESULT-PLACEHOLDER",
)
_SEMANTIC_CODES = (
    "SEM-INCOMPLETE-EXECUTION-SUMMARY",
    "SEM-INCOMPLETE-SECTION",
    "SEM-MISSING-DIFF-EVIDENCE",
    "SEM-MISSING-EVIDENCE-LINK",
    "SEM-MISSING-EVIDENCE-REF",
    "SEM-PLACEHOLDER-CONTENT",
    "SEM-RISK-UNDERREPORT",
    "SEM-TASK-DIFF-MISMATCH",
    "SEM-TASK-SCOPE-MISMATCH",
    "SEM-UNSUPPORTED-CLAIM",
    "SEM-UNSUPPORTED-VERDICT",
    "SEM-UNVERIFIABLE-CHECK-CLAIM",
)
_CROSS_DOCUMENT_CODES = (
    "CROSS-ANSWER-WITHOUT-QUESTION",
    "CROSS-BLOCKING-UNANSWERED",
    "CROSS-DUPLICATE-ANSWER-ID",
    "CROSS-DUPLICATE-QUESTION-ID",
    "CROSS-IMPLEMENTATION-FINALIZATION",
    "CROSS-PROJECT-SET-EVIDENCE-MISSING",
    "CROSS-QA-REVIEW-RISK",
    "CROSS-QA-UPSTREAM-EVIDENCE",
    "CROSS-QA-UPSTREAM-VERDICT",
    "CROSS-REPAIR-BRIEF-NOT-REFERENCED",
    "CROSS-REPAIR-BUDGET-EXHAUSTED",
    "CROSS-REPAIR-MENTION-WITHOUT-BRIEF",
    "CROSS-REVIEW-IMPLEMENT-EVIDENCE",
    "CROSS-REVIEW-IMPLEMENT-FINDING",
    "CROSS-REVIEW-IMPLEMENT-PATH",
    "CROSS-TASKLIST-PLAN-DEPENDENCY",
    "CROSS-TASKLIST-PLAN-MILESTONE",
    "CROSS-TASKLIST-PLAN-VERIFICATION",
)

VALIDATOR_FINDING_CODES = (
    *(
        ValidatorFindingCodeSpec(code, ValidatorReportSection.STRUCTURAL)
        for code in _STRUCTURAL_CODES
    ),
    *(
        ValidatorFindingCodeSpec(code, ValidatorReportSection.SEMANTIC)
        for code in _SEMANTIC_CODES
    ),
    *(
        ValidatorFindingCodeSpec(code, ValidatorReportSection.CROSS_DOCUMENT)
        for code in _CROSS_DOCUMENT_CODES
    ),
    ValidatorFindingCodeSpec(
        "STRUCT-MISSING-DOCUMENT",
        ValidatorReportSection.STRUCTURAL,
        status="legacy",
        replacement="STRUCT-MISSING-REQUIRED-DOCUMENT",
    ),
    ValidatorFindingCodeSpec(
        "STRUCT-MISSING-HEADING",
        ValidatorReportSection.STRUCTURAL,
        status="legacy",
        replacement="STRUCT-MISSING-REQUIRED-SECTION",
    ),
    ValidatorFindingCodeSpec(
        "STRUCT-EMPTY-SECTION",
        ValidatorReportSection.STRUCTURAL,
        status="legacy",
        replacement="STRUCT-EMPTY-REQUIRED-SECTION",
    ),
    ValidatorFindingCodeSpec(
        "CROSS-REFERENCE-MISMATCH",
        ValidatorReportSection.CROSS_DOCUMENT,
        status="legacy",
    ),
)

_FIELDS_BY_KEY = MappingProxyType({field.key: field for field in VALIDATOR_REPORT_FIELDS})
_FIELDS_BY_LABEL = MappingProxyType(
    {
        label.casefold(): field
        for field in VALIDATOR_REPORT_FIELDS
        for label in (field.label, *field.aliases)
    }
)
_CODES_BY_VALUE = MappingProxyType({spec.code: spec for spec in VALIDATOR_FINDING_CODES})


def validator_report_field(key: str) -> ValidatorReportFieldSpec:
    try:
        return _FIELDS_BY_KEY[key.strip()]
    except KeyError as exc:
        raise ValidatorReportProtocolError(
            f"Unknown validator-report field key: {key!r}."
        ) from exc


def resolve_validator_report_field(label: str) -> ValidatorReportFieldSpec:
    try:
        return _FIELDS_BY_LABEL[label.strip().casefold()]
    except KeyError as exc:
        raise ValidatorReportProtocolError(
            f"Unknown validator-report field label: {label!r}."
        ) from exc


def resolve_validator_finding_code(
    code: str, *, for_write: bool = False
) -> ValidatorFindingCodeSpec:
    normalized = code.strip().upper()
    try:
        spec = _CODES_BY_VALUE[normalized]
    except KeyError as exc:
        raise ValidatorReportProtocolError(
            f"Unknown validator finding code: {code!r}."
        ) from exc
    if for_write and spec.status != "canonical":
        raise ValidatorReportProtocolError(
            f"Legacy validator finding code cannot be written: {normalized}."
        )
    return spec


def canonical_validator_finding_code(code: str) -> str:
    spec = resolve_validator_finding_code(code)
    return spec.replacement or spec.code

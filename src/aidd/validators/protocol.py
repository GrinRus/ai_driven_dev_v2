from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Literal

VALIDATOR_REPORT_PROTOCOL_VERSION = 1
ADVISORY_OBSERVATIONS_HEADING = "Advisory observations"

ValidatorFindingCategory = Literal["structural", "semantic", "cross-document", "interview"]


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


@dataclass(frozen=True, slots=True)
class ValidatorFindingCodeSpec:
    code: str
    section: ValidatorReportSection

    @property
    def category(self) -> ValidatorFindingCategory:
        if self.code.startswith("INTERVIEW-"):
            return "interview"
        if self.section is ValidatorReportSection.STRUCTURAL:
            return "structural"
        if self.section is ValidatorReportSection.SEMANTIC:
            return "semantic"
        return "cross-document"


@dataclass(frozen=True, slots=True)
class ParsedValidatorReportField:
    key: str
    value: str
    line_number: int


@dataclass(frozen=True, slots=True)
class ParsedValidatorFinding:
    code: str
    severity: str
    message: str
    source_path: str | None
    source_line_number: int | None
    report_line_number: int
    occurrence_count: int
    category: ValidatorFindingCategory


@dataclass(frozen=True, slots=True)
class ValidatorReportReadModel:
    fields: tuple[ParsedValidatorReportField, ...]
    findings: tuple[ParsedValidatorFinding, ...]
    advisories: tuple[ParsedValidatorFinding, ...] = ()

    def field(self, key: str) -> ParsedValidatorReportField | None:
        return next((field for field in self.fields if field.key == key), None)

    @property
    def verdict(self) -> str | None:
        field = self.field("verdict")
        return None if field is None else field.value.strip("`").strip().lower()


VALIDATOR_REPORT_FIELDS = (
    ValidatorReportFieldSpec("total_issues", "Total issues", ValidatorReportSection.SUMMARY),
    ValidatorReportFieldSpec("blocking_issues", "Blocking issues", ValidatorReportSection.SUMMARY),
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
    ),
    ValidatorReportFieldSpec(
        "repair_required",
        "Repair required for progression",
        ValidatorReportSection.RESULT,
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
    "SEM-PLAN-SCOPE-MISMATCH",
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
    *(ValidatorFindingCodeSpec(code, ValidatorReportSection.SEMANTIC) for code in _SEMANTIC_CODES),
    *(
        ValidatorFindingCodeSpec(code, ValidatorReportSection.CROSS_DOCUMENT)
        for code in _CROSS_DOCUMENT_CODES
    ),
)

_FIELDS_BY_KEY = MappingProxyType({field.key: field for field in VALIDATOR_REPORT_FIELDS})
_FIELDS_BY_LABEL = MappingProxyType(
    {field.label.casefold(): field for field in VALIDATOR_REPORT_FIELDS}
)
_CODES_BY_VALUE = MappingProxyType({spec.code: spec for spec in VALIDATOR_FINDING_CODES})

_FIELD_LINE_PATTERN = re.compile(r"^\s*[-*]\s*(?P<label>[^:]+):\s*(?P<value>.*?)\s*$")
_FINDING_LINE_PATTERN = re.compile(
    r"^\s*-\s+`(?P<code>[^`]+)`\s+\(`(?P<severity>[^`]+)`\)\s+"
    r"in\s+(?P<location>`[^`]+`(?::\d+)?|unknown location|[^:]+):\s+"
    r"(?P<message>.+?)\s*$"
)
_BACKTICKED_LOCATION_PATTERN = re.compile(r"^`(?P<path>[^`]+)`(?::(?P<line>\d+))?$")
_REPEATED_SUFFIX_PATTERN = re.compile(r"^(?P<message>.+?)\s+\(repeated (?P<count>\d+) times\)$")


def validator_report_field(key: str) -> ValidatorReportFieldSpec:
    try:
        return _FIELDS_BY_KEY[key.strip()]
    except KeyError as exc:
        raise ValidatorReportProtocolError(f"Unknown validator-report field key: {key!r}.") from exc


def resolve_validator_report_field(label: str) -> ValidatorReportFieldSpec:
    try:
        return _FIELDS_BY_LABEL[label.strip().casefold()]
    except KeyError as exc:
        raise ValidatorReportProtocolError(
            f"Unknown validator-report field label: {label!r}."
        ) from exc


def resolve_validator_finding_code(code: str) -> ValidatorFindingCodeSpec:
    normalized = code.strip().upper()
    try:
        spec = _CODES_BY_VALUE[normalized]
    except KeyError as exc:
        raise ValidatorReportProtocolError(f"Unknown validator finding code: {code!r}.") from exc
    return spec


def _parse_finding_location(raw_location: str) -> tuple[str | None, int | None]:
    normalized = raw_location.strip()
    if normalized.casefold() == "unknown location":
        return None, None
    match = _BACKTICKED_LOCATION_PATTERN.fullmatch(normalized)
    if match is None:
        return normalized or None, None
    line_number = match.group("line")
    return match.group("path"), int(line_number) if line_number is not None else None


def _parse_finding_message(raw_message: str) -> tuple[str, int]:
    normalized = raw_message.strip()
    match = _REPEATED_SUFFIX_PATTERN.fullmatch(normalized)
    if match is None:
        return normalized, 1
    return match.group("message").strip(), int(match.group("count"))


def _validate_progression_semantics(
    *,
    fields: tuple[ParsedValidatorReportField, ...],
    findings: tuple[ParsedValidatorFinding, ...],
) -> None:
    """Require the current report fields and one unambiguous progression decision."""
    field_values = {field.key: field.value.strip("`").strip().lower() for field in fields}
    missing = [
        field.label
        for field in VALIDATOR_REPORT_FIELDS
        if field.required and field.key not in field_values
    ]
    if missing:
        raise ValidatorReportProtocolError(
            "Validator report is missing required current-format fields: "
            + ", ".join(missing)
            + "."
        )
    verdict = field_values["verdict"]
    repair_required = field_values["repair_required"]
    if not field_values["total_issues"].isdigit():
        raise ValidatorReportProtocolError("Total issues must be a non-negative integer.")
    if int(field_values["total_issues"]) != len(findings):
        raise ValidatorReportProtocolError(
            "Total issues must equal the number of canonical findings."
        )

    if verdict == "fail":
        if not findings:
            raise ValidatorReportProtocolError(
                "Validator verdict `fail` requires at least one canonical finding."
            )
        if repair_required != "yes":
            raise ValidatorReportProtocolError(
                "A failing validator report must require repair for progression; "
                "fail-causing findings cannot be optional."
            )
    elif verdict == "pass":
        if findings:
            raise ValidatorReportProtocolError(
                "Validator verdict `pass` cannot include canonical findings."
            )
        if repair_required != "no":
            raise ValidatorReportProtocolError(
                "A passing validator report must not require repair for progression."
            )
    else:
        raise ValidatorReportProtocolError(f"Unsupported validator verdict: {verdict!r}.")

    blocking_issues = field_values.get("blocking_issues")
    if blocking_issues not in {"yes", "no"}:
        raise ValidatorReportProtocolError("Blocking issues must be `yes` or `no`.")
    expected_blocking = bool(findings)
    if (blocking_issues == "yes") != expected_blocking:
        expected = "yes" if expected_blocking else "no"
        raise ValidatorReportProtocolError(
            "Blocking issues must be `"
            f"{expected}` because canonical findings, not severity, determine "
            "progression blocking."
        )


def parse_validator_report(markdown: str) -> ValidatorReportReadModel:
    """Parse the current canonical validator-report protocol vocabulary."""

    fields: list[ParsedValidatorReportField] = []
    findings: list[ParsedValidatorFinding] = []
    advisories: list[ParsedValidatorFinding] = []
    field_keys: set[str] = set()
    current_section: ValidatorReportSection | None = None
    in_advisory_section = False
    sections_by_heading = {section.value: section for section in ValidatorReportSection}

    for line_number, raw_line in enumerate(markdown.splitlines(), start=1):
        normalized_line = raw_line.strip()
        if normalized_line.startswith("## "):
            heading = normalized_line[3:].strip()
            in_advisory_section = heading == ADVISORY_OBSERVATIONS_HEADING
            current_section = sections_by_heading.get(heading)
            continue

        finding_match = _FINDING_LINE_PATTERN.fullmatch(raw_line)
        if finding_match is not None:
            code_spec = resolve_validator_finding_code(finding_match.group("code"))
            if (
                current_section
                in {
                    ValidatorReportSection.STRUCTURAL,
                    ValidatorReportSection.SEMANTIC,
                    ValidatorReportSection.CROSS_DOCUMENT,
                }
                and code_spec.section is not current_section
            ):
                raise ValidatorReportProtocolError(
                    f"Finding {code_spec.code} is in the wrong report section on line "
                    f"{line_number}."
                )
            severity = finding_match.group("severity").strip().lower()
            if severity not in {"critical", "high", "medium", "low"}:
                raise ValidatorReportProtocolError(
                    f"Unsupported validator finding severity on line {line_number}: {severity!r}."
                )
            source_path, source_line_number = _parse_finding_location(
                finding_match.group("location")
            )
            message, occurrence_count = _parse_finding_message(finding_match.group("message"))
            parsed_finding = ParsedValidatorFinding(
                code=code_spec.code,
                severity=severity,
                message=message,
                source_path=source_path,
                source_line_number=source_line_number,
                report_line_number=line_number,
                occurrence_count=occurrence_count,
                category=code_spec.category,
            )
            (advisories if in_advisory_section else findings).append(parsed_finding)
            continue

        field_match = _FIELD_LINE_PATTERN.fullmatch(raw_line)
        if field_match is None:
            continue
        label = field_match.group("label").strip()
        try:
            field_spec = resolve_validator_report_field(label)
        except ValidatorReportProtocolError:
            if current_section in {
                ValidatorReportSection.SUMMARY,
                ValidatorReportSection.RESULT,
            }:
                raise
            continue
        if current_section is not None and field_spec.section is not current_section:
            raise ValidatorReportProtocolError(
                f"Field {label!r} is in the wrong report section on line {line_number}."
            )
        if field_spec.key in field_keys:
            raise ValidatorReportProtocolError(
                f"Duplicate validator-report field {field_spec.label!r}."
            )
        field_keys.add(field_spec.key)
        fields.append(
            ParsedValidatorReportField(
                key=field_spec.key,
                value=field_match.group("value").strip(),
                line_number=line_number,
            )
        )

    parsed_fields = tuple(fields)
    parsed_findings = tuple(findings)
    parsed_advisories = tuple(advisories)
    _validate_progression_semantics(fields=parsed_fields, findings=parsed_findings)
    return ValidatorReportReadModel(
        fields=parsed_fields,
        findings=parsed_findings,
        advisories=parsed_advisories,
    )

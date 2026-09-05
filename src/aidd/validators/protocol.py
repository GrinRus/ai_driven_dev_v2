from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Literal

VALIDATOR_REPORT_PROTOCOL_VERSION = 1
ADVISORY_OBSERVATIONS_HEADING = "Advisory observations"

ProtocolEntryStatus = Literal["canonical", "legacy"]
ValidatorFindingCategory = Literal[
    "structural", "semantic", "cross-document", "interview"
]


class ValidatorReportProtocolError(ValueError):
    """Raised when validator-report protocol vocabulary is unknown or invalid."""


class DocumentReadFailureKind(StrEnum):
    """Canonical machine-readable causes for a Markdown document read failure."""

    NON_FILE = "non_file"
    UNREADABLE = "unreadable"
    INVALID_UTF8 = "invalid_utf8"
    MALFORMED_FRONTMATTER = "malformed_frontmatter"


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
class DocumentReadFailureSpec:
    """Map one document-read failure kind to its canonical finding code."""

    kind: DocumentReadFailureKind
    code: str
    description: str

    @property
    def finding_code(self) -> str:
        """Explicit alias for callers that emit a :class:`ValidationFinding`."""

        return self.code


@dataclass(frozen=True, slots=True)
class ParsedValidatorReportField:
    key: str
    value: str
    line_number: int
    used_legacy_alias: bool


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

    @property
    def advisory_observations(self) -> tuple[ParsedValidatorFinding, ...]:
        """Alias that makes the non-verdict channel explicit to evidence consumers."""

        return self.advisories


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
    "STRUCT-DOCUMENT-NON-FILE",
    "STRUCT-DOCUMENT-UNREADABLE",
    "STRUCT-DOCUMENT-INVALID-UTF8",
    "STRUCT-DOCUMENT-MALFORMED-FRONTMATTER",
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

DOCUMENT_READ_FAILURES = (
    DocumentReadFailureSpec(
        kind=DocumentReadFailureKind.NON_FILE,
        code="STRUCT-DOCUMENT-NON-FILE",
        description="The discovered Markdown path exists but is not a regular file.",
    ),
    DocumentReadFailureSpec(
        kind=DocumentReadFailureKind.UNREADABLE,
        code="STRUCT-DOCUMENT-UNREADABLE",
        description="The Markdown path cannot be opened or read.",
    ),
    DocumentReadFailureSpec(
        kind=DocumentReadFailureKind.INVALID_UTF8,
        code="STRUCT-DOCUMENT-INVALID-UTF8",
        description="The Markdown bytes are not valid UTF-8.",
    ),
    DocumentReadFailureSpec(
        kind=DocumentReadFailureKind.MALFORMED_FRONTMATTER,
        code="STRUCT-DOCUMENT-MALFORMED-FRONTMATTER",
        description="The optional frontmatter delimiters or entries are malformed.",
    ),
)

DOCUMENT_READ_FAILURE_CODES = tuple(spec.code for spec in DOCUMENT_READ_FAILURES)
DOCUMENT_READ_FAILURE_KINDS = tuple(spec.kind for spec in DOCUMENT_READ_FAILURES)

_FIELDS_BY_KEY = MappingProxyType({field.key: field for field in VALIDATOR_REPORT_FIELDS})
_FIELDS_BY_LABEL = MappingProxyType(
    {
        label.casefold(): field
        for field in VALIDATOR_REPORT_FIELDS
        for label in (field.label, *field.aliases)
    }
)
_CODES_BY_VALUE = MappingProxyType({spec.code: spec for spec in VALIDATOR_FINDING_CODES})
_DOCUMENT_READ_FAILURES_BY_KIND = MappingProxyType(
    {spec.kind: spec for spec in DOCUMENT_READ_FAILURES}
)
_DOCUMENT_READ_FAILURES_BY_CODE = MappingProxyType(
    {spec.code: spec for spec in DOCUMENT_READ_FAILURES}
)

_FIELD_LINE_PATTERN = re.compile(r"^\s*[-*]\s*(?P<label>[^:]+):\s*(?P<value>.*?)\s*$")
_FINDING_LINE_PATTERN = re.compile(
    r"^\s*-\s+`(?P<code>[^`]+)`\s+\(`(?P<severity>[^`]+)`\)\s+"
    r"in\s+(?P<location>`[^`]+`(?::\d+)?|unknown location|[^:]+):\s+"
    r"(?P<message>.+?)\s*$"
)
_BACKTICKED_LOCATION_PATTERN = re.compile(
    r"^`(?P<path>[^`]+)`(?::(?P<line>\d+))?$"
)
_REPEATED_SUFFIX_PATTERN = re.compile(
    r"^(?P<message>.+?)\s+\(repeated (?P<count>\d+) times\)$"
)


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


def resolve_document_read_failure(
    kind: DocumentReadFailureKind | str,
) -> DocumentReadFailureSpec:
    """Resolve a canonical document-read failure kind from a string or enum."""

    normalized = kind.value if isinstance(kind, DocumentReadFailureKind) else kind.strip().lower()
    normalized = normalized.replace("-", "_")
    try:
        return _DOCUMENT_READ_FAILURES_BY_KIND[DocumentReadFailureKind(normalized)]
    except (KeyError, ValueError) as exc:
        raise ValidatorReportProtocolError(
            f"Unknown document-read failure kind: {kind!r}."
        ) from exc


def resolve_document_read_failure_code(code: str) -> DocumentReadFailureSpec:
    """Resolve a canonical document-read failure from its validator finding code."""

    normalized = code.strip().upper()
    try:
        return _DOCUMENT_READ_FAILURES_BY_CODE[normalized]
    except KeyError as exc:
        raise ValidatorReportProtocolError(
            f"Unknown document-read failure code: {code!r}."
        ) from exc


def canonical_validator_finding_code(code: str) -> str:
    spec = resolve_validator_finding_code(code)
    return spec.replacement or spec.code


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
    """Reject a report that makes a failing finding optional for progression.

    The summary/result fields are optional for read compatibility with older
    protocol-v1 evidence, so semantic validation runs only when the canonical
    verdict and repair fields are both present.
    """

    field_values = {field.key: field.value.strip("`").strip().lower() for field in fields}
    verdict = field_values.get("verdict")
    repair_required = field_values.get("repair_required")
    has_canonical_summary = any(
        key in field_values for key in ("total_issues", "blocking_issues")
    )
    if verdict is None or repair_required is None or not has_canonical_summary:
        # Minimal result-only artifacts are retained for compatibility with
        # older stage-summary and runtime evidence readers.
        return

    if verdict in {"fail", "repair"}:
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
        raise ValidatorReportProtocolError(
            f"Unsupported validator verdict: {verdict!r}."
        )

    blocking_issues = field_values.get("blocking_issues")
    if blocking_issues not in {"yes", "no"}:
        # Historical reports used a numeric count. Keep those reports readable
        # during the protocol-v1 compatibility window.
        return
    expected_blocking = bool(findings)
    if (blocking_issues == "yes") != expected_blocking:
        expected = "yes" if expected_blocking else "no"
        raise ValidatorReportProtocolError(
            "Blocking issues must be `"
            f"{expected}` because canonical findings, not severity, determine "
            "progression blocking."
        )


def parse_validator_report(markdown: str) -> ValidatorReportReadModel:
    """Parse canonical or declared-legacy validator-report protocol vocabulary."""

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
            if current_section in {
                ValidatorReportSection.STRUCTURAL,
                ValidatorReportSection.SEMANTIC,
                ValidatorReportSection.CROSS_DOCUMENT,
            } and code_spec.section is not current_section:
                raise ValidatorReportProtocolError(
                    f"Finding {code_spec.code} is in the wrong report section on line "
                    f"{line_number}."
                )
            severity = finding_match.group("severity").strip().lower()
            if severity not in {"critical", "high", "medium", "low"}:
                raise ValidatorReportProtocolError(
                    f"Unsupported validator finding severity on line {line_number}: "
                    f"{severity!r}."
                )
            source_path, source_line_number = _parse_finding_location(
                finding_match.group("location")
            )
            message, occurrence_count = _parse_finding_message(
                finding_match.group("message")
            )
            parsed_finding = ParsedValidatorFinding(
                code=code_spec.replacement or code_spec.code,
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
                used_legacy_alias=label != field_spec.label,
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


def render_validator_report_skeleton() -> str:
    """Render the canonical prompt-facing validator-report protocol skeleton."""

    lines = ["```md", "# Validator Report", ""]
    fields_by_section = {
        section: tuple(
            field for field in VALIDATOR_REPORT_FIELDS if field.section is section
        )
        for section in ValidatorReportSection
    }
    placeholders = {
        "total_issues": "<number>",
        "blocking_issues": "<yes|no>",
        "affected_documents": "<workspace-relative paths or none>",
        "dominant_failure_categories": "<ordered categories or none>",
        "finding_occurrences": "<raw count; remove line when no duplicates were collapsed>",
        "verdict": "`<pass|fail>`",
        "repair_required": "<yes|no>",
    }
    for section in ValidatorReportSection:
        if section is ValidatorReportSection.RESULT:
            lines.extend((f"## {ADVISORY_OBSERVATIONS_HEADING}", "", "- none", ""))
        lines.extend((f"## {section.value}", ""))
        fields = fields_by_section[section]
        if fields:
            lines.extend(f"- {field.label}: {placeholders[field.key]}" for field in fields)
        else:
            lines.append("- none")
        lines.append("")
    lines.append("```")
    return "\n".join(lines)

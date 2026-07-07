from __future__ import annotations

import re
from pathlib import Path

from aidd.core.operator_frontend_models import OperatorValidationFindingView

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


def _finding_category(code: str) -> str:
    normalized = code.strip().upper()
    if normalized.startswith("STRUCT-"):
        return "structural"
    if normalized.startswith("SEM-"):
        return "semantic"
    if normalized.startswith("CROSS-"):
        return "cross-document"
    if normalized.startswith("INTERVIEW-"):
        return "interview"
    return "other"


def _parse_location(raw_location: str) -> tuple[str | None, int | None]:
    normalized = raw_location.strip()
    if normalized.lower() == "unknown location":
        return None, None
    match = _BACKTICKED_LOCATION_PATTERN.match(normalized)
    if match is None:
        return normalized or None, None
    line_number = match.group("line")
    return (
        match.group("path"),
        int(line_number) if line_number is not None else None,
    )


def _operator_hint(code: str, message: str) -> str | None:
    normalized_code = code.strip().upper()
    normalized_message = message.strip().lower()
    if normalized_code == "SEM-UNVERIFIABLE-CHECK-CLAIM":
        if "outcome claim without executable command evidence" in normalized_message:
            return (
                "Rewrite the verification note with the exact command/check and observed "
                "result on the same bullet, or mark it `not-run: <reason>` if it was not run."
            )
        if "must include observed command outcome" in normalized_message:
            return (
                "Keep the command/check, then add the observed result on the same bullet "
                "such as `-> pass`, `-> fail`, or `exit code N`."
            )
    if normalized_code.startswith("STRUCT-MISSING"):
        return "Create the missing required document or section, then rerun validation."
    if normalized_code == "CROSS-BLOCKING-UNANSWERED":
        return "Answer blocking questions with `[resolved]` entries before resuming."
    return None


def _message_and_occurrence_count(message: str) -> tuple[str, int]:
    normalized = message.strip()
    match = _REPEATED_SUFFIX_PATTERN.match(normalized)
    if match is None:
        return normalized, 1
    return match.group("message").strip(), int(match.group("count"))


def _merge_duplicate_findings(
    findings: list[OperatorValidationFindingView],
) -> tuple[OperatorValidationFindingView, ...]:
    merged: list[OperatorValidationFindingView] = []
    index_by_finding: dict[tuple[str, str, str | None, int | None, str], int] = {}
    for finding in findings:
        key = (
            finding.code,
            finding.severity,
            finding.path,
            finding.line_number,
            finding.message,
        )
        existing_index = index_by_finding.get(key)
        if existing_index is None:
            index_by_finding[key] = len(merged)
            merged.append(finding)
            continue
        existing = merged[existing_index]
        merged[existing_index] = OperatorValidationFindingView(
            category=existing.category,
            code=existing.code,
            severity=existing.severity,
            path=existing.path,
            line_number=existing.line_number,
            message=existing.message,
            occurrence_count=existing.occurrence_count + finding.occurrence_count,
            operator_hint=existing.operator_hint,
        )
    return tuple(merged)


def parse_validator_report_findings(
    markdown_text: str,
) -> tuple[OperatorValidationFindingView, ...]:
    findings: list[OperatorValidationFindingView] = []
    for line in markdown_text.splitlines():
        match = _FINDING_LINE_PATTERN.match(line)
        if match is None:
            continue
        path, line_number = _parse_location(match.group("location"))
        code = match.group("code").strip()
        message, occurrence_count = _message_and_occurrence_count(match.group("message"))
        findings.append(
            OperatorValidationFindingView(
                category=_finding_category(code),
                code=code,
                severity=match.group("severity").strip(),
                path=path,
                line_number=line_number,
                message=message,
                occurrence_count=occurrence_count,
                operator_hint=_operator_hint(code=code, message=message),
            )
        )
    return _merge_duplicate_findings(findings)


def load_validator_report_findings(
    *,
    workspace_root: Path,
    validator_report_path: str | Path | None,
) -> tuple[OperatorValidationFindingView, ...]:
    if validator_report_path is None:
        return ()
    relative = Path(validator_report_path)
    if relative.is_absolute():
        return ()
    report_path = (workspace_root / relative).resolve(strict=False)
    resolved_workspace = workspace_root.resolve(strict=False)
    if not report_path.is_relative_to(resolved_workspace):
        return ()
    if not report_path.exists() or not report_path.is_file():
        return ()
    try:
        return parse_validator_report_findings(report_path.read_text(encoding="utf-8"))
    except OSError:
        return ()


__all__ = [
    "load_validator_report_findings",
    "parse_validator_report_findings",
]

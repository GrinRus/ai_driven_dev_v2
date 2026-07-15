from __future__ import annotations

from pathlib import Path

from aidd.core.operator_frontend_models import OperatorValidationFindingView
from aidd.validators.protocol import parse_validator_report


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
    report = parse_validator_report(markdown_text)
    findings = [
            OperatorValidationFindingView(
                category=finding.category,
                code=finding.code,
                severity=finding.severity,
                path=finding.source_path,
                line_number=finding.source_line_number,
                message=finding.message,
                occurrence_count=finding.occurrence_count,
                operator_hint=_operator_hint(code=finding.code, message=finding.message),
            )
            for finding in report.findings
        ]
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

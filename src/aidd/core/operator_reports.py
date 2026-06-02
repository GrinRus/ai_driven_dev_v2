from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aidd.core.workspace import stage_root as workspace_stage_root

_MAX_REPORT_BYTES = 256 * 1024
_BACKTICK_PATH_PATTERN = re.compile(r"`([^`\n]+\.[A-Za-z0-9][^`]*)`")
_FINDING_START_PATTERN = re.compile(
    r"^\s*(?:#{1,6}\s+(?:finding\s+)?|[-*]\s+)?([A-Z]{1,4}-\d+)\b",
    flags=re.IGNORECASE,
)
_EVIDENCE_ID_PATTERN = re.compile(r"\b(EV-\d+)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ImplementationEvidenceView:
    selected_task_id: str | None
    touched_files: tuple[str, ...]
    verification_commands: tuple[str, ...]
    skipped_checks: tuple[str, ...]
    residual_risks: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReviewFindingView:
    finding_id: str
    severity: str | None
    disposition: str | None
    summary: str
    evidence: tuple[str, ...]
    related_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReviewFindingsView:
    approval_status: str | None
    findings: tuple[ReviewFindingView, ...]
    required_changes: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QaVerdictView:
    quality_verdict: str | None
    release_recommendation: str | None
    residual_risks: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    known_issues: tuple[str, ...]
    warnings: tuple[str, ...]


def _read_bounded_markdown(path: Path) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if not path.exists():
        return "", [f"Report is missing: {path.as_posix()}."]
    size = path.stat().st_size
    data = path.read_bytes()[:_MAX_REPORT_BYTES]
    if size > _MAX_REPORT_BYTES:
        warnings.append(f"Report truncated to {_MAX_REPORT_BYTES} bytes.")
    return data.decode("utf-8", errors="replace"), warnings


def _normalize_line(line: str) -> str:
    return line.strip().strip("-*").strip()


def _section_lines(text: str, names: tuple[str, ...]) -> tuple[str, ...]:
    wanted = {name.lower() for name in names}
    captured: list[str] = []
    active = False
    for line in text.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            label = heading.group(2).strip().lower()
            active = any(name in label for name in wanted)
            continue
        if active:
            captured.append(line)
    return tuple(captured)


def _unique(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return tuple(result)


def _extract_backtick_paths(lines: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for line in lines:
        values.extend(match.group(1).strip() for match in _BACKTICK_PATH_PATTERN.finditer(line))
    return _unique(values)


def _extract_list_items(lines: tuple[str, ...]) -> tuple[str, ...]:
    items: list[str] = []
    for line in lines:
        if re.match(r"^\s*[-*]\s+", line):
            items.append(_normalize_line(line))
    return _unique(items)


def _extract_selected_task_id(text: str) -> str | None:
    patterns = (
        r"(?:selected\s+task|task\s+id|selected\s+task\s+id)\s*[:\-]\s*`?([A-Za-z0-9_.:-]+)`?",
        r"\b(TL?-\d+|WI-\d+|TASK-\d+)\b",
    )
    for pattern in patterns:
        matched = re.search(pattern, text, flags=re.IGNORECASE)
        if matched:
            return matched.group(1)
    return None


def _extract_commandish_items(lines: tuple[str, ...]) -> tuple[str, ...]:
    commands: list[str] = []
    for line in lines:
        normalized = _normalize_line(line)
        if not normalized:
            continue
        if "`" in normalized or "->" in normalized or "exit 0" in normalized.lower():
            commands.append(normalized)
    return _unique(commands)


def parse_implementation_report_text(
    text: str,
    warnings: tuple[str, ...] = (),
) -> ImplementationEvidenceView:
    local_warnings = list(warnings)
    touched_section = _section_lines(
        text,
        ("touched files", "changed files", "files changed", "implementation evidence"),
    )
    verification_section = _section_lines(
        text,
        ("verification", "checks", "test evidence"),
    )
    risk_section = _section_lines(
        text,
        ("residual risk", "follow-up", "known risk"),
    )
    touched_files = _extract_backtick_paths(touched_section)
    if not touched_files:
        touched_files = _extract_backtick_paths(tuple(text.splitlines()))
        if touched_files:
            local_warnings.append(
                "Touched files section was not found; inferred paths from report."
            )
    if not touched_files:
        local_warnings.append("No touched files were detected in implementation-report.md.")

    skipped = [
        _normalize_line(line)
        for line in verification_section
        if re.search(r"\b(skipped|not[- ]run|deferred)\b", line, flags=re.IGNORECASE)
    ]
    return ImplementationEvidenceView(
        selected_task_id=_extract_selected_task_id(text),
        touched_files=touched_files,
        verification_commands=_extract_commandish_items(verification_section),
        skipped_checks=_unique(skipped),
        residual_risks=_extract_list_items(risk_section),
        warnings=tuple(local_warnings),
    )


def resolve_implementation_evidence(
    *,
    workspace_root: Path,
    work_item: str,
) -> ImplementationEvidenceView:
    path = workspace_stage_root(root=workspace_root, work_item=work_item, stage="implement") / (
        "implementation-report.md"
    )
    text, warnings = _read_bounded_markdown(path)
    return parse_implementation_report_text(text, warnings=tuple(warnings))


def _approval_status(text: str) -> str | None:
    matched = re.search(
        r"(?:review\s+status|approval\s+status|verdict)\s*[:\-]\s*`?([a-z-]+)`?",
        text,
        flags=re.IGNORECASE,
    )
    if matched:
        value = matched.group(1).lower()
        if value in {"approved", "approved-with-conditions", "rejected"}:
            return value
    for value in ("approved-with-conditions", "approved", "rejected"):
        if re.search(rf"\b{re.escape(value)}\b", text, flags=re.IGNORECASE):
            return value
    return None


def _finding_blocks(text: str) -> tuple[tuple[str, str], ...]:
    blocks: list[tuple[str, str]] = []
    current_id: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        matched = _FINDING_START_PATTERN.match(line)
        if matched is not None:
            if current_id is not None:
                blocks.append((current_id, "\n".join(current_lines).strip()))
            current_id = matched.group(1).upper()
            current_lines = [line]
            continue
        if current_id is not None:
            current_lines.append(line)
    if current_id is not None:
        blocks.append((current_id, "\n".join(current_lines).strip()))
    return tuple(blocks)


def _extract_labeled_value(block: str, label: str, allowed: set[str] | None = None) -> str | None:
    matched = re.search(rf"{label}\s*[:\-]\s*`?([A-Za-z0-9_-]+)`?", block, flags=re.IGNORECASE)
    if not matched:
        return None
    value = matched.group(1).lower()
    if allowed is not None and value not in allowed:
        return None
    return value


def _extract_evidence(block: str) -> tuple[str, ...]:
    values: list[str] = []
    for line in block.splitlines():
        if "evidence" in line.lower():
            values.append(_normalize_line(line))
    values.extend(_extract_backtick_paths(tuple(block.splitlines())))
    return _unique(values)


def parse_review_report_text(text: str, warnings: tuple[str, ...] = ()) -> ReviewFindingsView:
    local_warnings = list(warnings)
    findings: list[ReviewFindingView] = []
    for finding_id, block in _finding_blocks(text):
        first_line = _normalize_line(block.splitlines()[0] if block.splitlines() else finding_id)
        findings.append(
            ReviewFindingView(
                finding_id=finding_id,
                severity=_extract_labeled_value(
                    block,
                    "severity",
                    {"critical", "high", "medium", "low", "info"},
                ),
                disposition=_extract_labeled_value(
                    block,
                    "disposition",
                    {"must-fix", "follow-up", "accepted-risk", "invalid"},
                ),
                summary=first_line,
                evidence=_extract_evidence(block),
                related_paths=_extract_backtick_paths(tuple(block.splitlines())),
            )
        )
    if not findings and "no review findings" not in text.lower():
        local_warnings.append("No structured review findings were detected.")

    required_changes = _extract_list_items(
        _section_lines(text, ("required changes", "must fix", "summary of required changes"))
    )
    return ReviewFindingsView(
        approval_status=_approval_status(text),
        findings=tuple(findings),
        required_changes=required_changes,
        warnings=tuple(local_warnings),
    )


def resolve_review_findings(*, workspace_root: Path, work_item: str) -> ReviewFindingsView:
    path = workspace_stage_root(root=workspace_root, work_item=work_item, stage="review") / (
        "review-report.md"
    )
    text, warnings = _read_bounded_markdown(path)
    return parse_review_report_text(text, warnings=tuple(warnings))


def _qa_verdict(text: str) -> str | None:
    matched = re.search(
        r"(?:qa\s+verdict|quality\s+verdict)\s*[:\-]\s*`?([a-z-]+)`?",
        text,
        flags=re.IGNORECASE,
    )
    if matched:
        value = matched.group(1).lower()
        if value in {"ready", "ready-with-risks", "not-ready"}:
            return value
    for value in ("ready-with-risks", "not-ready", "ready"):
        if re.search(rf"\b{re.escape(value)}\b", text, flags=re.IGNORECASE):
            return value
    return None


def _release_recommendation(text: str) -> str | None:
    matched = re.search(
        r"(?:release\s+recommendation|recommendation)\s*[:\-]\s*`?([a-z-]+)`?",
        text,
        flags=re.IGNORECASE,
    )
    return matched.group(1).lower() if matched else None


def parse_qa_report_text(text: str, warnings: tuple[str, ...] = ()) -> QaVerdictView:
    risk_lines = _section_lines(text, ("residual risk", "risks"))
    known_issue_lines = _section_lines(text, ("known issues", "issues"))
    evidence_ids = _unique(
        [match.group(1).upper() for match in _EVIDENCE_ID_PATTERN.finditer(text)]
    )
    local_warnings = list(warnings)
    verdict = _qa_verdict(text)
    if verdict is None:
        local_warnings.append("No QA verdict was detected.")
    return QaVerdictView(
        quality_verdict=verdict,
        release_recommendation=_release_recommendation(text),
        residual_risks=_extract_list_items(risk_lines),
        evidence_ids=evidence_ids,
        known_issues=_extract_list_items(known_issue_lines),
        warnings=tuple(local_warnings),
    )


def resolve_qa_verdict(*, workspace_root: Path, work_item: str) -> QaVerdictView:
    path = workspace_stage_root(root=workspace_root, work_item=work_item, stage="qa") / (
        "qa-report.md"
    )
    text, warnings = _read_bounded_markdown(path)
    return parse_qa_report_text(text, warnings=tuple(warnings))


__all__ = [
    "ImplementationEvidenceView",
    "QaVerdictView",
    "ReviewFindingView",
    "ReviewFindingsView",
    "parse_implementation_report_text",
    "parse_qa_report_text",
    "parse_review_report_text",
    "resolve_implementation_evidence",
    "resolve_qa_verdict",
    "resolve_review_findings",
]

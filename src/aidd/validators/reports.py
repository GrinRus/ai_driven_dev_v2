from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from aidd.validators.models import ValidationFinding
from aidd.validators.protocol import (
    ValidatorReportSection,
    resolve_validator_finding_code,
    validator_report_field,
)


@dataclass(frozen=True, slots=True)
class _RenderedFinding:
    finding: ValidationFinding
    occurrence_count: int


def _classify_bucket(code: str) -> ValidatorReportSection:
    return resolve_validator_finding_code(code, for_write=True).section


def _format_location(finding: ValidationFinding) -> str:
    if finding.location is None:
        return "unknown location"

    path = f"`{finding.location.workspace_relative_path}`"
    if finding.location.line_number is None:
        return path
    return f"{path}:{finding.location.line_number}"


def _collapse_duplicate_findings(
    findings: Iterable[ValidationFinding],
) -> tuple[_RenderedFinding, ...]:
    rendered: list[_RenderedFinding] = []
    index_by_finding: dict[ValidationFinding, int] = {}
    for finding in findings:
        existing_index = index_by_finding.get(finding)
        if existing_index is None:
            index_by_finding[finding] = len(rendered)
            rendered.append(_RenderedFinding(finding=finding, occurrence_count=1))
            continue
        existing = rendered[existing_index]
        rendered[existing_index] = _RenderedFinding(
            finding=existing.finding,
            occurrence_count=existing.occurrence_count + 1,
        )
    return tuple(rendered)


def render_validator_report(findings: Iterable[ValidationFinding]) -> str:
    rendered_findings = _collapse_duplicate_findings(findings)
    findings_list = [rendered.finding for rendered in rendered_findings]
    occurrence_count = sum(rendered.occurrence_count for rendered in rendered_findings)
    finding_sections = (
        ValidatorReportSection.STRUCTURAL,
        ValidatorReportSection.SEMANTIC,
        ValidatorReportSection.CROSS_DOCUMENT,
    )
    buckets: dict[ValidatorReportSection, list[_RenderedFinding]] = {
        section: [] for section in finding_sections
    }
    for rendered in rendered_findings:
        buckets[_classify_bucket(rendered.finding.code)].append(rendered)

    affected_documents = sorted(
        {
            finding.location.workspace_relative_path
            for finding in findings_list
            if finding.location is not None
        }
    )
    dominant_categories = Counter(_classify_bucket(finding.code) for finding in findings_list)
    dominant_labels = (
        ", ".join(category.lower() for category, _ in dominant_categories.most_common())
        if dominant_categories
        else "none"
    )

    blocking = any(finding.severity in {"critical", "high"} for finding in findings_list)
    verdict = "pass" if not findings_list else "fail"
    repair_required = "no" if verdict == "pass" else "yes"

    lines = [
        "# Validator Report",
        "",
        "## Summary",
        "",
        f"- {validator_report_field('total_issues').label}: {len(findings_list)}",
        (
            f"- {validator_report_field('blocking_issues').label}: "
            f"{'yes' if blocking else 'no'}"
        ),
        (
            f"- {validator_report_field('affected_documents').label}: "
            + ", ".join(f"`{path}`" for path in affected_documents)
            if affected_documents
            else f"- {validator_report_field('affected_documents').label}: none"
        ),
        (
            f"- {validator_report_field('dominant_failure_categories').label}: "
            f"{dominant_labels}"
        ),
    ]
    if occurrence_count != len(findings_list):
        lines.append(
            f"- {validator_report_field('finding_occurrences').label}: {occurrence_count}"
        )
    lines.append("")

    for section in finding_sections:
        lines.extend([f"## {section.value}", ""])
        bucket_findings = buckets[section]
        if not bucket_findings:
            lines.extend(["- none", ""])
            continue
        for rendered in bucket_findings:
            finding = rendered.finding
            repeat_note = (
                f" (repeated {rendered.occurrence_count} times)"
                if rendered.occurrence_count > 1
                else ""
            )
            lines.append(
                f"- `{finding.code}` (`{finding.severity}`) in {_format_location(finding)}: "
                f"{finding.message}{repeat_note}"
            )
        lines.append("")

    lines.extend(
        [
            "## Result",
            "",
            f"- {validator_report_field('verdict').label}: `{verdict}`",
            (
                f"- {validator_report_field('repair_required').label}: "
                f"{repair_required}"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_report(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def write_validator_report(path: Path, findings: Iterable[ValidationFinding]) -> None:
    write_report(path=path, text=render_validator_report(findings))

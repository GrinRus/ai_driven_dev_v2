from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from aidd.validators.models import ValidationFinding


def _classify_bucket(code: str) -> str:
    normalized = code.strip().upper()
    if normalized.startswith("STRUCT-"):
        return "Structural checks"
    if normalized.startswith("SEM-"):
        return "Semantic checks"
    if normalized.startswith("CROSS-"):
        return "Cross-document checks"
    return "Structural checks"


def _format_location(finding: ValidationFinding) -> str:
    if finding.location is None:
        return "unknown location"

    path = f"`{finding.location.workspace_relative_path}`"
    if finding.location.line_number is None:
        return path
    return f"{path}:{finding.location.line_number}"


def render_validator_report(findings: Iterable[ValidationFinding]) -> str:
    findings_list = list(findings)
    buckets: dict[str, list[ValidationFinding]] = {
        "Structural checks": [],
        "Semantic checks": [],
        "Cross-document checks": [],
    }
    for finding in findings_list:
        buckets[_classify_bucket(finding.code)].append(finding)

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
        f"- Total issues: {len(findings_list)}",
        f"- Blocking issues: {'yes' if blocking else 'no'}",
        (
            "- Affected documents: "
            + ", ".join(f"`{path}`" for path in affected_documents)
            if affected_documents
            else "- Affected documents: none"
        ),
        f"- Dominant failure categories: {dominant_labels}",
        "",
    ]

    for heading in ("Structural checks", "Semantic checks", "Cross-document checks"):
        lines.extend([f"## {heading}", ""])
        bucket_findings = buckets[heading]
        if not bucket_findings:
            lines.extend(["- none", ""])
            continue
        for finding in bucket_findings:
            lines.append(
                f"- `{finding.code}` (`{finding.severity}`) in {_format_location(finding)}: "
                f"{finding.message}"
            )
        lines.append("")

    lines.extend(
        [
            "## Result",
            "",
            f"- Verdict: `{verdict}`",
            f"- Repair required for progression: {repair_required}",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def write_validator_report(path: Path, findings: Iterable[ValidationFinding]) -> None:
    write_report(path=path, text=render_validator_report(findings))

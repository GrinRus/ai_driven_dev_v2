from __future__ import annotations

import re
from pathlib import Path

from aidd.validators.cross_document_rules.context import (
    CrossDocumentContext,
    level_two_section_text,
    workspace_relative,
)
from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic_rules.common import (
    IMPLEMENT_FILE_ENTRY_PATTERN,
    REVIEW_FINDING_ID_PATTERN,
    extract_review_finding_blocks,
)

REVIEW_IMPLEMENT_FINDING_CODE = "CROSS-REVIEW-IMPLEMENT-FINDING"
REVIEW_IMPLEMENT_EVIDENCE_CODE = "CROSS-REVIEW-IMPLEMENT-EVIDENCE"
REVIEW_IMPLEMENT_PATH_CODE = "CROSS-REVIEW-IMPLEMENT-PATH"

_EVIDENCE_ID_PATTERN = re.compile(r"\bEV-\d+\b", re.IGNORECASE)
_BACKTICKED_REFERENCE_PATTERN = re.compile(r"`([^`]+)`")
_ARTIFACT_SUFFIXES = frozenset({".md", ".json", ".jsonl", ".log", ".txt"})


def validate_review_implementation(
    context: CrossDocumentContext,
) -> tuple[ValidationFinding, ...]:
    if (
        context.stage != "review"
        or context.review_text is None
        or context.implementation_text is None
    ):
        return ()
    review_relative = workspace_relative(context.review_path, context.workspace_root)
    findings_section = level_two_section_text(context.review_text, "Findings")
    finding_blocks = extract_review_finding_blocks(findings_section)
    declared: dict[str, int] = {}
    findings: list[ValidationFinding] = []
    for block in finding_blocks:
        match = REVIEW_FINDING_ID_PATTERN.search(block)
        if match is not None:
            finding_id = match.group(0).strip("`").upper()
            declared[finding_id] = declared.get(finding_id, 0) + 1
    for finding_id, count in declared.items():
        if count != 1:
            findings.append(
                ValidationFinding(
                    REVIEW_IMPLEMENT_FINDING_CODE,
                    f"Review finding `{finding_id}` must be declared exactly once.",
                    "high",
                    ValidationIssueLocation(review_relative),
                )
            )
    review_without_findings = re.sub(
        r"^##\s+Findings\s*$.*?(?=^##\s+|\Z)",
        "",
        context.review_text,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    for match in REVIEW_FINDING_ID_PATTERN.finditer(review_without_findings):
        finding_id = match.group(0).strip("`").upper()
        if declared.get(finding_id) != 1:
            findings.append(
                ValidationFinding(
                    REVIEW_IMPLEMENT_FINDING_CODE,
                    f"Review references undeclared finding `{finding_id}`.",
                    "high",
                    ValidationIssueLocation(review_relative),
                )
            )

    touched_paths = {
        match.group(0).strip("`").strip().strip("/")
        for match in IMPLEMENT_FILE_ENTRY_PATTERN.finditer(
            level_two_section_text(context.implementation_text, "Touched files")
        )
    }
    available_artifacts = {
        path.name for path in context.implementation_output_root.iterdir() if path.is_file()
    }
    available_evidence_ids = {
        match.group(0).upper()
        for match in _EVIDENCE_ID_PATTERN.finditer(context.implementation_text)
    }
    for block in finding_blocks:
        evidence_lines = "\n".join(
            line for line in block.splitlines() if re.search(r"\bevidence\s*:", line, re.I)
        )
        for evidence_match in _EVIDENCE_ID_PATTERN.finditer(evidence_lines):
            evidence_id = evidence_match.group(0).upper()
            if evidence_id not in available_evidence_ids:
                findings.append(
                    ValidationFinding(
                        REVIEW_IMPLEMENT_EVIDENCE_CODE,
                        f"Review references unknown implementation evidence `{evidence_id}`.",
                        "high",
                        ValidationIssueLocation(review_relative),
                    )
                )
        for value in _BACKTICKED_REFERENCE_PATTERN.findall(evidence_lines):
            reference = value.strip().removeprefix("./").rstrip("/")
            if not reference:
                continue
            suffix = Path(reference).suffix.lower()
            if "/" not in reference and suffix in _ARTIFACT_SUFFIXES:
                if reference not in available_artifacts:
                    findings.append(
                        ValidationFinding(
                            REVIEW_IMPLEMENT_EVIDENCE_CODE,
                            f"Review references missing implementation artifact `{reference}`.",
                            "high",
                            ValidationIssueLocation(review_relative),
                        )
                    )
                continue
            if "/" not in reference and not suffix:
                continue
            if reference not in touched_paths:
                findings.append(
                    ValidationFinding(
                        REVIEW_IMPLEMENT_PATH_CODE,
                        (
                            f"Review references changed path `{reference}` not declared "
                            "by implementation."
                        ),
                        "high",
                        ValidationIssueLocation(review_relative),
                    )
                )
    return tuple(findings)

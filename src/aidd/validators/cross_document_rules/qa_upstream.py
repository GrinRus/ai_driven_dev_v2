from __future__ import annotations

import re

from aidd.validators.cross_document_rules.context import (
    CrossDocumentContext,
    level_two_section_text,
    workspace_relative,
)
from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic_rules.common import (
    REVIEW_FINDING_ID_PATTERN,
    extract_qa_release_recommendation,
    extract_qa_verdict,
    extract_review_finding_blocks,
    extract_risk_blocks,
    is_empty_risk_entry,
    is_risk_metadata_entry,
)

QA_REVIEW_RISK_CODE = "CROSS-QA-REVIEW-RISK"
QA_UPSTREAM_EVIDENCE_CODE = "CROSS-QA-UPSTREAM-EVIDENCE"
QA_UPSTREAM_VERDICT_CODE = "CROSS-QA-UPSTREAM-VERDICT"

_EVIDENCE_ID_PATTERN = re.compile(r"\bEV-\d+\b", re.IGNORECASE)
_BACKTICKED_REFERENCE_PATTERN = re.compile(r"`([^`]+)`")
_REVIEW_ACCEPTED_RISK_PATTERN = re.compile(r"\bAR-[1-9]\d*\b", re.IGNORECASE)
_QA_EVIDENCE_ENTRY_PATTERN = re.compile(r"^\s*-\s+", re.MULTILINE)


def validate_qa_upstream(context: CrossDocumentContext) -> tuple[ValidationFinding, ...]:
    if (
        context.stage != "qa"
        or context.qa_text is None
        or context.upstream_review_text is None
        or context.implementation_text is None
    ):
        return ()
    qa_relative = workspace_relative(context.qa_path, context.workspace_root)
    available_ids = {
        match.group(0).strip("`").upper()
        for pattern, text in (
            (REVIEW_FINDING_ID_PATTERN, context.upstream_review_text),
            (_REVIEW_ACCEPTED_RISK_PATTERN, context.upstream_review_text),
            (_EVIDENCE_ID_PATTERN, context.upstream_review_text),
            (_EVIDENCE_ID_PATTERN, context.implementation_text),
        )
        for match in pattern.finditer(text)
    }
    available_paths = {
        workspace_relative(path, context.workspace_root)
        for root in (context.upstream_review_path.parent, context.implementation_output_root)
        if root.is_dir()
        for path in root.iterdir()
        if path.is_file()
    }

    def resolved_reference(text: str) -> bool:
        if any(
            match.group(0).upper() in available_ids
            for match in _EVIDENCE_ID_PATTERN.finditer(text)
        ):
            return True
        if any(
            match.group(0).strip("`").upper() in available_ids
            for pattern in (REVIEW_FINDING_ID_PATTERN, _REVIEW_ACCEPTED_RISK_PATTERN)
            for match in pattern.finditer(text)
        ):
            return True
        return any(
            value.strip().removeprefix("./").rstrip("/") in available_paths
            for value in _BACKTICKED_REFERENCE_PATTERN.findall(text)
        )

    findings: list[ValidationFinding] = []
    risk_section = level_two_section_text(
        context.qa_text, "Residual risks"
    ) or level_two_section_text(context.qa_text, "Known issues")
    risk_entries = tuple(
        item
        for item in extract_risk_blocks(risk_section)
        if not is_empty_risk_entry(item) and not is_risk_metadata_entry(item)
    )
    for risk in risk_entries:
        if not resolved_reference(risk):
            findings.append(
                ValidationFinding(
                    QA_REVIEW_RISK_CODE,
                    (
                        "Each QA residual risk must cite exact upstream review or "
                        "implementation evidence."
                    ),
                    "high",
                    ValidationIssueLocation(qa_relative),
                )
            )
    evidence_sections = "\n".join(
        level_two_section_text(context.qa_text, heading)
        for heading in ("Evidence references", "Evidence", "Verification summary")
    )
    for entry in re.split(r"(?=^\s*-\s+)", evidence_sections, flags=re.MULTILINE):
        if _QA_EVIDENCE_ENTRY_PATTERN.match(entry) is not None and not resolved_reference(entry):
            findings.append(
                ValidationFinding(
                    QA_UPSTREAM_EVIDENCE_CODE,
                    (
                        "QA evidence entry does not resolve to exact upstream evidence or "
                        "an artifact path."
                    ),
                    "high",
                    ValidationIssueLocation(qa_relative),
                )
            )
    status_match = re.search(
        r"Review status\s*:\s*`?(approved-with-conditions|approved|rejected)`?",
        context.upstream_review_text,
        re.IGNORECASE,
    )
    review_rejected = status_match is not None and status_match.group(1).lower() == "rejected"
    unresolved_must_fix = any(
        "must-fix" in block.casefold()
        for block in extract_review_finding_blocks(
            level_two_section_text(context.upstream_review_text, "Findings")
        )
    )
    verdict = extract_qa_verdict(context.qa_text, prefer_labeled=True)
    recommendation = extract_qa_release_recommendation(context.qa_text)
    if (review_rejected or unresolved_must_fix) and (
        verdict != "not-ready" or recommendation != "hold"
    ):
        findings.append(
            ValidationFinding(
                QA_UPSTREAM_VERDICT_CODE,
                (
                    "Rejected review or unresolved must-fix evidence requires "
                    "`QA verdict: not-ready` and release recommendation `hold`."
                ),
                "critical",
                ValidationIssueLocation(qa_relative),
            )
        )
    return tuple(findings)

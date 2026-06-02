from __future__ import annotations

import re

from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    IMPLEMENT_FILE_ENTRY_PATTERN,
    INCOMPLETE_SECTION_CODE,
    REVIEW_ACCEPTANCE_CRITERIA_PATTERN,
    REVIEW_FINDING_ID_PATTERN,
    REVIEW_SPEC_RATIONALE_PATTERN,
    UNSUPPORTED_CLAIM_CODE,
    SemanticDocumentContext,
    SemanticRule,
    SemanticSection,
    extract_bullet_items,
    extract_review_disposition,
    extract_review_finding_blocks,
    extract_review_spec_decision,
    has_explicit_severity,
    validate_placeholder_sections,
)

NO_REVIEW_FINDINGS_PATTERN = re.compile(
    r"\b(?:"
    r"no\s+(?:material\s+)?(?:review\s+)?(?:findings?|issues?|defects?)"
    r"(?:\s+(?:were\s+)?(?:identified|found|observed))?|"
    r"findings?\s*:\s*none"
    r")\b",
    flags=re.IGNORECASE,
)


def _review_sections(
    context: SemanticDocumentContext,
) -> tuple[SemanticSection, SemanticSection, SemanticSection]:
    findings_section = context.section_by_candidates(candidates=("Findings",))
    approval = context.section_by_candidates(candidates=("Approval status", "Verdict"))
    required_changes = context.section_by_candidates(
        candidates=("Required changes", "Required follow-up"),
    )
    return findings_section, approval, required_changes


def _validate_finding_entry(
    *,
    context: SemanticDocumentContext,
    findings_section: SemanticSection,
    finding_item: str,
) -> tuple[int, tuple[ValidationFinding, ...]]:
    findings: list[ValidationFinding] = []
    if REVIEW_FINDING_ID_PATTERN.search(finding_item) is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Each finding must include a stable id "
                    "(for example `RV-1` or `REV-001`)."
                ),
                severity="medium",
                location=findings_section.location,
            )
        )

    if not has_explicit_severity(finding_item):
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Each finding must include explicit severity "
                    "(critical/high/medium/low/info/none)."
                ),
                severity="medium",
                location=findings_section.location,
            )
        )

    review_disposition = extract_review_disposition(finding_item)
    if review_disposition is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Each finding must include explicit disposition "
                    "(`must-fix`, `follow-up`, `accepted-risk`, or `invalid`)."
                ),
                severity="medium",
                location=findings_section.location,
            )
        )

    if REVIEW_SPEC_RATIONALE_PATTERN.search(finding_item) is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Each finding must include rationale "
                    "(for example `Rationale:` or `because ...`)."
                ),
                severity="medium",
                location=findings_section.location,
            )
        )

    has_implementation_evidence = IMPLEMENT_FILE_ENTRY_PATTERN.search(finding_item) is not None
    has_acceptance_reference = (
        REVIEW_ACCEPTANCE_CRITERIA_PATTERN.search(finding_item) is not None
    )
    if not has_implementation_evidence and not has_acceptance_reference:
        findings.append(
            context.finding(
                code=UNSUPPORTED_CLAIM_CODE,
                message=(
                    "Finding is missing evidence reference to implementation output "
                    "or acceptance criteria."
                ),
                severity="high",
                location=findings_section.location,
            )
        )

    unresolved_must_fix_count = 1 if review_disposition == "must-fix" else 0
    return unresolved_must_fix_count, tuple(findings)


def _declares_no_review_findings(text: str) -> bool:
    normalized = text.strip().strip("`").strip().rstrip(".").strip()
    normalized = re.sub(r"^[-*]\s+", "", normalized).strip()
    if not normalized:
        return False
    if normalized.lower() == "none":
        return True
    return NO_REVIEW_FINDINGS_PATTERN.search(normalized) is not None


def _contains_no_review_findings_declaration(text: str) -> bool:
    return any(_declares_no_review_findings(line) for line in text.splitlines())


def _validate_findings_section(
    *,
    context: SemanticDocumentContext,
    findings_section: SemanticSection,
) -> tuple[int, tuple[ValidationFinding, ...]]:
    finding_items = extract_review_finding_blocks(findings_section.content)
    if _contains_no_review_findings_declaration(
        findings_section.content
    ) and REVIEW_FINDING_ID_PATTERN.search(findings_section.content) is None:
        return 0, tuple()
    if _declares_no_review_findings(findings_section.content) and (
        not finding_items
        or all(_declares_no_review_findings(finding_item) for finding_item in finding_items)
    ):
        return 0, tuple()

    if not finding_items:
        return 0, (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Findings` must include finding entries with stable ids, "
                    "severity, disposition, and rationale."
                ),
                severity="medium",
                location=findings_section.location,
            ),
        )

    findings: list[ValidationFinding] = []
    unresolved_must_fix_count = 0
    for finding_item in finding_items:
        must_fix_count, item_findings = _validate_finding_entry(
            context=context,
            findings_section=findings_section,
            finding_item=finding_item,
        )
        unresolved_must_fix_count += must_fix_count
        findings.extend(item_findings)
    return unresolved_must_fix_count, tuple(findings)


def _validate_approval_status(
    *,
    context: SemanticDocumentContext,
    approval: SemanticSection,
    unresolved_must_fix_count: int,
) -> tuple[str | None, tuple[ValidationFinding, ...]]:
    approval_status = extract_review_spec_decision(approval.content)
    if approval_status is None:
        return None, (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Approval status` must declare one explicit state: "
                    "`approved`, `approved-with-conditions`, or `rejected`."
                ),
                severity="medium",
                location=approval.location,
            ),
        )
    if approval_status == "approved" and unresolved_must_fix_count > 0:
        return approval_status, (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Approval status cannot be `approved` while unresolved "
                    "`must-fix` findings remain."
                ),
                severity="high",
                location=approval.location,
            ),
        )
    return approval_status, tuple()


def _validate_required_changes(
    *,
    context: SemanticDocumentContext,
    required_changes: SemanticSection,
    approval_status: str | None,
) -> tuple[ValidationFinding, ...]:
    required_changes_items = extract_bullet_items(required_changes.content)
    has_required_change_entries = any(item.lower() != "none" for item in required_changes_items)
    if (
        approval_status in {"approved-with-conditions", "rejected"}
        and not has_required_change_entries
    ):
        return (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message="Non-approved outcomes must include concrete required-change entries.",
                severity="medium",
                location=required_changes.location,
            ),
        )
    return tuple()


def validate_review_report(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings_section, approval, required_changes = _review_sections(context)
    unresolved_must_fix_count, finding_findings = _validate_findings_section(
        context=context,
        findings_section=findings_section,
    )
    approval_status, approval_findings = _validate_approval_status(
        context=context,
        approval=approval,
        unresolved_must_fix_count=unresolved_must_fix_count,
    )

    findings: list[ValidationFinding] = []
    findings.extend(finding_findings)
    findings.extend(approval_findings)
    findings.extend(
        _validate_required_changes(
            context=context,
            required_changes=required_changes,
            approval_status=approval_status,
        )
    )
    findings.extend(validate_placeholder_sections(context))
    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="review",
        document_name="review-report.md",
        validate=validate_review_report,
    ),
)

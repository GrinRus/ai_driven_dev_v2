from __future__ import annotations

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
    extract_bullet_items,
    extract_review_disposition,
    extract_review_finding_blocks,
    extract_review_spec_decision,
    has_explicit_severity,
    validate_placeholder_sections,
)


def validate_review_report(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    findings_section = context.section_by_candidates(candidates=("Findings",))
    approval = context.section_by_candidates(candidates=("Approval status", "Verdict"))
    required_changes = context.section_by_candidates(
        candidates=("Required changes", "Required follow-up"),
    )

    finding_items = extract_review_finding_blocks(findings_section.content)
    if not finding_items:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Findings` must include finding entries with stable ids, "
                    "severity, disposition, and rationale."
                ),
                severity="medium",
                location=findings_section.location,
            )
        )

    unresolved_must_fix_count = 0
    for finding_item in finding_items:
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

        if review_disposition == "must-fix":
            unresolved_must_fix_count += 1

    approval_status = extract_review_spec_decision(approval.content)
    if approval_status is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Approval status` must declare one explicit state: "
                    "`approved`, `approved-with-conditions`, or `rejected`."
                ),
                severity="medium",
                location=approval.location,
            )
        )
    elif approval_status == "approved" and unresolved_must_fix_count > 0:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Approval status cannot be `approved` while unresolved "
                    "`must-fix` findings remain."
                ),
                severity="high",
                location=approval.location,
            )
        )

    required_changes_items = extract_bullet_items(required_changes.content)
    has_required_change_entries = any(item.lower() != "none" for item in required_changes_items)
    if (
        approval_status in {"approved-with-conditions", "rejected"}
        and not has_required_change_entries
    ):
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message="Non-approved outcomes must include concrete required-change entries.",
                severity="medium",
                location=required_changes.location,
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

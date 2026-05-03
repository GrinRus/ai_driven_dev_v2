from __future__ import annotations

import re
from dataclasses import dataclass

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic_rules.common import (
    INCOMPLETE_SECTION_CODE,
    REVIEW_SPEC_NO_ISSUES_PATTERN,
    REVIEW_SPEC_RATIONALE_PATTERN,
    SemanticDocumentContext,
    SemanticRule,
    extract_markdown_list_items,
    extract_review_spec_decision,
    extract_review_spec_issue_blocks,
    extract_review_spec_readiness_state,
    normalized_heading,
    review_spec_issue_has_explicit_severity,
    validate_placeholder_sections,
)


@dataclass(frozen=True, slots=True)
class ReviewSpecState:
    readiness_state: str | None
    decision: str | None
    decision_location: ValidationIssueLocation | None


def _review_spec_state(context: SemanticDocumentContext) -> ReviewSpecState:
    readiness = context.section_by_candidates(candidates=("Readiness state",))
    decision = context.section_by_candidates(candidates=("Decision",))
    return ReviewSpecState(
        readiness_state=extract_review_spec_readiness_state(readiness.content),
        decision=extract_review_spec_decision(decision.content),
        decision_location=decision.location if decision.content else None,
    )


def validate_review_spec_report(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))
    review_state = _review_spec_state(context)

    for section in context.iter_required_sections():
        normalized_section = normalized_heading(section.name)
        compact_content = re.sub(r"\s+", " ", section.content).strip()

        if normalized_section == "issue list":
            issue_blocks = extract_review_spec_issue_blocks(section.content)
            if not issue_blocks and REVIEW_SPEC_NO_ISSUES_PATTERN.search(compact_content):
                continue

            if not issue_blocks:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Issue list` must use bullet items with "
                            "severity and rationale."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            else:
                if any(
                    not review_spec_issue_has_explicit_severity(item)
                    for item in issue_blocks
                ):
                    findings.append(
                        context.finding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Each `Issue list` item must include explicit severity "
                                "(critical/high/medium/low/info/none)."
                            ),
                            severity="medium",
                            location=section.location,
                        )
                    )
                if any(
                    REVIEW_SPEC_RATIONALE_PATTERN.search(item) is None
                    for item in issue_blocks
                ):
                    findings.append(
                        context.finding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Each `Issue list` item must include rationale "
                                "(for example `because ...`)."
                            ),
                            severity="medium",
                            location=section.location,
                        )
                    )

        if normalized_section == "recommendation summary":
            recommendation_items = extract_markdown_list_items(section.content)
            if not recommendation_items:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Recommendation summary` must use "
                            "prioritized Markdown list items."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            elif compact_content.lower() in {"none", "- none"}:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Recommendation summary` cannot be `none`; "
                            "include actionable remediation steps."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

        if normalized_section == "readiness state" and review_state.readiness_state is None:
            findings.append(
                context.finding(
                    code=INCOMPLETE_SECTION_CODE,
                    message=(
                        "Section `Readiness state` must declare one explicit state: "
                        "`ready`, `ready-with-conditions`, or `not-ready`."
                    ),
                    severity="medium",
                    location=section.location,
                )
            )

        if normalized_section == "decision" and review_state.decision is None:
            findings.append(
                context.finding(
                    code=INCOMPLETE_SECTION_CODE,
                    message=(
                        "Section `Decision` must declare one explicit sign-off status: "
                        "`approved`, `approved-with-conditions`, or `rejected`."
                    ),
                    severity="medium",
                    location=section.location,
                )
            )

    if review_state.readiness_state is not None and review_state.decision is not None:
        expected_decision_by_state = {
            "ready": "approved",
            "ready-with-conditions": "approved-with-conditions",
            "not-ready": "rejected",
        }
        expected_decision = expected_decision_by_state[review_state.readiness_state]
        if review_state.decision != expected_decision:
            findings.append(
                context.finding(
                    code=INCOMPLETE_SECTION_CODE,
                    message=(
                        "Sections `Readiness state` and `Decision` are inconsistent: "
                        f"`{review_state.readiness_state}` expects `{expected_decision}`."
                    ),
                    severity="high",
                    location=review_state.decision_location or context.location(),
                )
            )

    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="review-spec",
        document_name="review-spec-report.md",
        validate=validate_review_spec_report,
    ),
)

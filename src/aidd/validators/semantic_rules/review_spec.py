from __future__ import annotations

import re
from dataclasses import dataclass

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic_rules.common import (
    IMPLEMENT_COMMAND_PATTERN,
    IMPLEMENT_FILE_ENTRY_PATTERN,
    INCOMPLETE_SECTION_CODE,
    MISSING_EVIDENCE_REF_CODE,
    REVIEW_SPEC_RATIONALE_PATTERN,
    UNSUPPORTED_CLAIM_CODE,
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

_SEVERITY_VALUES = ("critical", "high", "medium", "low", "info", "none")
_REVIEW_SPEC_SEVERITY_VALUE_PATTERN = re.compile(
    r"\bseverity\s*:?\s*`?(critical|high|medium|low|info|none)`?\b",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_INLINE_SEVERITY_VALUE_PATTERN = re.compile(
    r"(?:\(|\[|\s-\s)`?(critical|high|medium|low|info|none)`?(?:\)|\]|\s-)",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_EVIDENCE_LABEL_PATTERN = re.compile(
    r"\b(?:\*\*)?Evidence(?:\*\*)?\s*:",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_RECONCILIATION_LABEL_PATTERN = re.compile(
    r"\b(?:\*\*)?Reconciliation(?:\*\*)?\s*:",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_DIRECT_EVIDENCE_PATTERN = re.compile(
    r"("
    r"\b(?:research-notes|plan|validator-report|stage-result|repository-state|"
    r"user-request|intake)\.md\b|"
    r"\b(?:context|workitems)/[^\s`]+\.md\b|"
    r"\b(?:S|F|M|AC|EV|RV)-?\d+\b|"
    r"\[(?:S|F|M|AC|EV|RV)-?\d+\]"
    r")",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_SOURCE_INSPECTION_PATTERN = re.compile(
    r"\bsource\s+inspection\s+(?:shows?|found|indicates?|confirms?)\b",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_CONTRADICTION_PATTERN = re.compile(
    r"\b("
    r"contradict(?:s|ed|ing|ion|ory)?|"
    r"conflict(?:s|ed|ing)?|"
    r"inconsistent|"
    r"mismatch(?:es|ed)?|"
    r"diverge(?:s|d|nt|nce)?|"
    r"disagree(?:s|d)?"
    r")\b",
    flags=re.IGNORECASE,
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


def _review_spec_issue_severity(issue_block: str) -> str | None:
    severity_match = _REVIEW_SPEC_SEVERITY_VALUE_PATTERN.search(issue_block)
    if severity_match is not None:
        return severity_match.group(1).lower()

    inline_match = _REVIEW_SPEC_INLINE_SEVERITY_VALUE_PATTERN.search(issue_block)
    if inline_match is not None:
        return inline_match.group(1).lower()

    lowered = issue_block.lower()
    for severity in _SEVERITY_VALUES:
        if f"`{severity}`" in lowered:
            return severity
    return None


def _review_spec_issue_has_evidence_label(issue_block: str) -> bool:
    return _REVIEW_SPEC_EVIDENCE_LABEL_PATTERN.search(issue_block) is not None


def _review_spec_issue_evidence_texts(issue_block: str) -> tuple[str, ...]:
    evidence_texts: list[str] = []
    for line in issue_block.splitlines():
        match = _REVIEW_SPEC_EVIDENCE_LABEL_PATTERN.search(line)
        if match is None:
            continue
        evidence_text = line[match.end() :].strip()
        evidence_text = re.split(
            r"\b(?:\*\*)?(?:Rationale|Reconciliation|Severity|Observation|Section)"
            r"(?:\*\*)?\s*:",
            evidence_text,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()
        if evidence_text:
            evidence_texts.append(evidence_text)
    return tuple(evidence_texts)


def _review_spec_issue_has_reconciliation(issue_block: str) -> bool:
    return _REVIEW_SPEC_RECONCILIATION_LABEL_PATTERN.search(issue_block) is not None


def _review_spec_issue_has_direct_evidence(issue_block: str) -> bool:
    evidence_text = "\n".join(_review_spec_issue_evidence_texts(issue_block))
    if not evidence_text:
        return False
    return (
        IMPLEMENT_FILE_ENTRY_PATTERN.search(evidence_text) is not None
        or IMPLEMENT_COMMAND_PATTERN.search(evidence_text) is not None
        or _REVIEW_SPEC_DIRECT_EVIDENCE_PATTERN.search(evidence_text) is not None
    )


def _validate_issue_evidence(
    *,
    context: SemanticDocumentContext,
    issue_blocks: tuple[str, ...],
    location: ValidationIssueLocation,
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []

    if any(not _review_spec_issue_has_evidence_label(item) for item in issue_blocks):
        findings.append(
            context.finding(
                code=MISSING_EVIDENCE_REF_CODE,
                message=(
                    "Each `Issue list` item must include `Evidence:` naming a concrete "
                    "artifact, source id, target file path, or check result."
                ),
                severity="medium",
                location=location,
            )
        )

    if any(
        _review_spec_issue_severity(item) in {"critical", "high"}
        and not _review_spec_issue_has_direct_evidence(item)
        for item in issue_blocks
    ):
        findings.append(
            context.finding(
                code=UNSUPPORTED_CLAIM_CODE,
                message=(
                    "`critical` and `high` review-spec issues must cite direct durable "
                    "evidence, such as an upstream artifact path, source id, target file "
                    "path, or command/check result."
                ),
                severity="high",
                location=location,
            )
        )

    if any(
        _REVIEW_SPEC_SOURCE_INSPECTION_PATTERN.search(item) is not None
        and not _review_spec_issue_has_direct_evidence(item)
        for item in issue_blocks
    ):
        findings.append(
            context.finding(
                code=UNSUPPORTED_CLAIM_CODE,
                message=(
                    "Review-spec issues must not claim `source inspection shows` without "
                    "naming the concrete inspected artifact or check result."
                ),
                severity="high",
                location=location,
            )
        )

    if any(
        _REVIEW_SPEC_CONTRADICTION_PATTERN.search(item) is not None
        and (
            _review_spec_issue_severity(item) in {"critical", "high"}
            or _REVIEW_SPEC_SOURCE_INSPECTION_PATTERN.search(item) is not None
        )
        and (
            not _review_spec_issue_has_evidence_label(item)
            or not _review_spec_issue_has_reconciliation(item)
        )
        for item in issue_blocks
    ):
        findings.append(
            context.finding(
                code=UNSUPPORTED_CLAIM_CODE,
                message=(
                    "High-severity or source-inspection review-spec contradiction "
                    "claims must include `Evidence:` and `Reconciliation:` explaining "
                    "how the issue relates to upstream research or plan evidence."
                ),
                severity="high",
                location=location,
            )
        )

    return tuple(findings)


def validate_review_spec_report(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))
    review_state = _review_spec_state(context)

    for section in context.iter_required_sections():
        normalized_section = normalized_heading(section.name)
        compact_content = re.sub(r"\s+", " ", section.content).strip()

        if normalized_section == "issue list":
            issue_blocks = extract_review_spec_issue_blocks(section.content)

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
                findings.extend(
                    _validate_issue_evidence(
                        context=context,
                        issue_blocks=issue_blocks,
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

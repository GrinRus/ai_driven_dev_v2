from __future__ import annotations

from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    IMPLEMENT_FILE_ENTRY_PATTERN,
    INCOMPLETE_SECTION_CODE,
    MISSING_EVIDENCE_REF_CODE,
    QA_EVIDENCE_ID_PATTERN,
    QA_OWNER_PATTERN,
    QA_RISK_SEVERITY_PATTERN,
    RISK_MITIGATION_PATTERN,
    RISK_UNDERREPORT_CODE,
    UNSUPPORTED_VERDICT_CODE,
    SemanticDocumentContext,
    SemanticRule,
    extract_bullet_items,
    extract_qa_release_recommendation,
    extract_qa_verdict,
    extract_risk_blocks,
    is_empty_risk_entry,
    is_risk_metadata_entry,
    validate_placeholder_sections,
)


def validate_qa_report(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    verdict = context.section_by_candidates(candidates=("Quality verdict", "Readiness"))
    risks = context.section_by_candidates(candidates=("Residual risks", "Known issues"))
    recommendation = context.section_by_candidates(candidates=("Release recommendation",))
    evidence = context.section_by_candidates(candidates=("Evidence references", "Evidence"))

    qa_verdict = extract_qa_verdict(verdict.content)
    if qa_verdict is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Quality verdict` must declare one explicit state: "
                    "`ready`, `ready-with-risks`, or `not-ready`."
                ),
                severity="medium",
                location=verdict.location,
            )
        )

    qa_recommendation = extract_qa_release_recommendation(recommendation.content)
    if qa_recommendation is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Release recommendation` must declare one explicit state: "
                    "`proceed`, `proceed-with-conditions`, or `hold`."
                ),
                severity="medium",
                location=recommendation.location,
            )
        )

    risk_items = extract_risk_blocks(risks.content)
    risk_entry_items = tuple(
        item
        for item in risk_items
        if not is_empty_risk_entry(item) and not is_risk_metadata_entry(item)
    )
    has_residual_risk_entries = bool(risk_entry_items)
    if qa_verdict == "ready-with-risks" and not has_residual_risk_entries:
        findings.append(
            context.finding(
                code=RISK_UNDERREPORT_CODE,
                message=(
                    "Verdict `ready-with-risks` requires explicit residual risk entries "
                    "with mitigation/ownership notes."
                ),
                severity="high",
                location=risks.location,
            )
        )
    if qa_recommendation == "proceed-with-conditions" and not has_residual_risk_entries:
        findings.append(
            context.finding(
                code=RISK_UNDERREPORT_CODE,
                message=(
                    "Recommendation `proceed-with-conditions` requires explicit residual "
                    "risk entries."
                ),
                severity="high",
                location=risks.location,
            )
        )

    for risk_item in risk_entry_items:
        if QA_RISK_SEVERITY_PATTERN.search(risk_item) is None:
            findings.append(
                context.finding(
                    code=RISK_UNDERREPORT_CODE,
                    message=(
                        "Each residual risk item must include explicit severity "
                        "(critical/high/medium/low)."
                    ),
                    severity="medium",
                    location=risks.location,
                )
            )
            break

    has_mitigation_or_owner_note = (
        RISK_MITIGATION_PATTERN.search(risks.content) is not None
        or QA_OWNER_PATTERN.search(risks.content) is not None
    )
    if has_residual_risk_entries and not has_mitigation_or_owner_note:
        findings.append(
            context.finding(
                code=RISK_UNDERREPORT_CODE,
                message=(
                    "Residual risk summary must include mitigation and/or ownership "
                    "notes."
                ),
                severity="medium",
                location=risks.location,
            )
        )

    evidence_items = extract_bullet_items(evidence.content)
    has_evidence_entries = any(
        item.lower() not in {"none", "none recorded"} for item in evidence_items
    )
    if not has_evidence_entries:
        findings.append(
            context.finding(
                code=MISSING_EVIDENCE_REF_CODE,
                message=(
                    "Material QA claims and release recommendation must reference "
                    "verification artifacts or execution outputs."
                ),
                severity="high",
                location=evidence.location,
            )
        )
    else:
        for evidence_item in (
            item for item in evidence_items if item.lower() not in {"none", "none recorded"}
        ):
            has_artifact_path_reference = (
                IMPLEMENT_FILE_ENTRY_PATTERN.search(evidence_item) is not None
            )
            has_evidence_id = QA_EVIDENCE_ID_PATTERN.search(evidence_item) is not None
            if not has_artifact_path_reference and not has_evidence_id:
                findings.append(
                    context.finding(
                        code=MISSING_EVIDENCE_REF_CODE,
                        message=(
                            "Evidence entries must include stable evidence id "
                            "(for example `EV-1`) and/or artifact path in backticks."
                        ),
                        severity="medium",
                        location=evidence.location,
                    )
                )
                break

    if qa_verdict is not None and qa_recommendation is not None:
        if qa_verdict == "not-ready" and qa_recommendation != "hold":
            findings.append(
                context.finding(
                    code=UNSUPPORTED_VERDICT_CODE,
                    message=(
                        "Verdict `not-ready` must align with release recommendation "
                        "`hold`."
                    ),
                    severity="high",
                    location=recommendation.location,
                )
            )

        if qa_verdict in {"ready", "ready-with-risks"} and qa_recommendation == "hold":
            findings.append(
                context.finding(
                    code=UNSUPPORTED_VERDICT_CODE,
                    message=(
                        "Verdicts `ready` or `ready-with-risks` cannot pair with "
                        "release recommendation `hold`."
                    ),
                    severity="high",
                    location=recommendation.location,
                )
            )

        if qa_verdict in {"ready", "ready-with-risks"} and not has_evidence_entries:
            findings.append(
                context.finding(
                    code=UNSUPPORTED_VERDICT_CODE,
                    message=(
                        "Ready/proceed-style outcomes are unsupported without concrete "
                        "verification evidence references."
                    ),
                    severity="high",
                    location=verdict.location,
                )
            )

    findings.extend(validate_placeholder_sections(context))
    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="qa",
        document_name="qa-report.md",
        validate=validate_qa_report,
    ),
)

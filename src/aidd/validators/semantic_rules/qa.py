from __future__ import annotations

import re
from pathlib import Path

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
    SemanticSection,
    extract_bullet_items,
    extract_qa_release_recommendation,
    extract_qa_verdict,
    extract_risk_blocks,
    extract_top_level_bullet_blocks,
    is_empty_risk_entry,
    is_risk_metadata_entry,
    validate_placeholder_sections,
)

AC_ID_PATTERN = re.compile(r"\bAC-\d+\b", flags=re.IGNORECASE)


def _qa_sections(
    context: SemanticDocumentContext,
) -> tuple[SemanticSection, SemanticSection, SemanticSection, SemanticSection]:
    verdict = context.section_by_candidates(candidates=("Quality verdict", "Readiness"))
    risks = context.section_by_candidates(candidates=("Residual risks", "Known issues"))
    recommendation = context.section_by_candidates(candidates=("Release recommendation",))
    evidence = context.section_by_candidates(candidates=("Evidence references", "Evidence"))
    return verdict, risks, recommendation, evidence


def _validate_quality_verdict(
    *,
    context: SemanticDocumentContext,
    verdict: SemanticSection,
) -> tuple[str | None, tuple[ValidationFinding, ...]]:
    qa_verdict = extract_qa_verdict(verdict.content)
    if qa_verdict is not None:
        return qa_verdict, tuple()
    return None, (
        context.finding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Quality verdict` must declare one explicit state: "
                "`ready`, `ready-with-risks`, or `not-ready`."
            ),
            severity="medium",
            location=verdict.location,
        ),
    )


def _validate_release_recommendation(
    *,
    context: SemanticDocumentContext,
    recommendation: SemanticSection,
) -> tuple[str | None, tuple[ValidationFinding, ...]]:
    qa_recommendation = extract_qa_release_recommendation(recommendation.content)
    if qa_recommendation is not None:
        return qa_recommendation, tuple()
    return None, (
        context.finding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Release recommendation` must declare one explicit state: "
                "`proceed`, `proceed-with-conditions`, or `hold`."
            ),
            severity="medium",
            location=recommendation.location,
        ),
    )


def _risk_entry_items(risks: SemanticSection) -> tuple[str, ...]:
    risk_items = extract_risk_blocks(risks.content)
    return tuple(
        item
        for item in risk_items
        if not is_empty_risk_entry(item) and not is_risk_metadata_entry(item)
    )


def _validate_residual_risks(
    *,
    context: SemanticDocumentContext,
    risks: SemanticSection,
    qa_verdict: str | None,
    qa_recommendation: str | None,
    risk_entry_items: tuple[str, ...],
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
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
        if QA_RISK_SEVERITY_PATTERN.search(risk_item) is not None:
            continue
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
    return tuple(findings)


def _evidence_entries(evidence: SemanticSection) -> tuple[str, ...]:
    return tuple(
        item
        for item in extract_bullet_items(evidence.content)
        if item.lower() not in {"none", "none recorded"}
    )


def _validate_evidence_references(
    *,
    context: SemanticDocumentContext,
    evidence: SemanticSection,
    evidence_entries: tuple[str, ...],
) -> tuple[ValidationFinding, ...]:
    if not evidence_entries:
        return (
            context.finding(
                code=MISSING_EVIDENCE_REF_CODE,
                message=(
                    "Material QA claims and release recommendation must reference "
                    "verification artifacts or execution outputs."
                ),
                severity="high",
                location=evidence.location,
            ),
        )

    for evidence_item in evidence_entries:
        has_artifact_path_reference = (
            IMPLEMENT_FILE_ENTRY_PATTERN.search(evidence_item) is not None
        )
        has_evidence_id = QA_EVIDENCE_ID_PATTERN.search(evidence_item) is not None
        if has_artifact_path_reference or has_evidence_id:
            continue
        return (
            context.finding(
                code=MISSING_EVIDENCE_REF_CODE,
                message=(
                    "Evidence entries must include stable evidence id "
                    "(for example `EV-1`) and/or artifact path in backticks."
                ),
                severity="medium",
                location=evidence.location,
            ),
        )
    return tuple()


def _validate_verdict_recommendation_alignment(
    *,
    context: SemanticDocumentContext,
    verdict: SemanticSection,
    recommendation: SemanticSection,
    qa_verdict: str | None,
    qa_recommendation: str | None,
    has_evidence_entries: bool,
) -> tuple[ValidationFinding, ...]:
    if qa_verdict is None or qa_recommendation is None:
        return tuple()

    findings: list[ValidationFinding] = []
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
    return tuple(findings)


def _work_item_root_from_output_path(output_path: Path) -> Path | None:
    parts = output_path.parts
    for index, part in enumerate(parts):
        if part == "workitems" and index + 1 < len(parts):
            return Path(*parts[: index + 2])
    return None


def _acceptance_criteria_ids(context: SemanticDocumentContext) -> tuple[str, ...]:
    work_item_root = _work_item_root_from_output_path(context.output_path)
    if work_item_root is None:
        return tuple()

    criteria_path = work_item_root / "context" / "acceptance-criteria.md"
    if not criteria_path.exists():
        return tuple()

    criteria_text = criteria_path.read_text(encoding="utf-8", errors="replace")
    ids: list[str] = []
    seen: set[str] = set()
    for match in AC_ID_PATTERN.finditer(criteria_text):
        criterion_id = match.group(0).upper()
        if criterion_id in seen:
            continue
        ids.append(criterion_id)
        seen.add(criterion_id)
    return tuple(ids)


def _acceptance_bullet_for(
    *,
    criterion_id: str,
    coverage_items: tuple[str, ...],
) -> tuple[str | None, bool]:
    bundled_candidate = False
    for item in coverage_items:
        ids_in_item = {match.group(0).upper() for match in AC_ID_PATTERN.finditer(item)}
        if criterion_id not in ids_in_item:
            continue
        if ids_in_item == {criterion_id}:
            return item, False
        bundled_candidate = True
    return None, bundled_candidate


def _validate_acceptance_coverage(
    *,
    context: SemanticDocumentContext,
) -> tuple[ValidationFinding, ...]:
    criteria_ids = _acceptance_criteria_ids(context)
    if not criteria_ids:
        return tuple()

    coverage_items = extract_top_level_bullet_blocks("\n".join(context.markdown_lines))
    findings: list[ValidationFinding] = []
    for criterion_id in criteria_ids:
        coverage_item, bundled_candidate = _acceptance_bullet_for(
            criterion_id=criterion_id,
            coverage_items=coverage_items,
        )
        if coverage_item is None:
            if bundled_candidate:
                message = (
                    "Acceptance coverage must use a separate top-level bullet for "
                    f"`{criterion_id}` instead of bundling multiple `AC-N` ids."
                )
            else:
                message = (
                    "QA report must include an acceptance coverage bullet for "
                    f"`{criterion_id}` from `context/acceptance-criteria.md`."
                )
            findings.append(
                context.finding(
                    code=INCOMPLETE_SECTION_CODE,
                    message=message,
                    severity="high",
                    location=context.location(),
                )
            )
            continue

        has_same_bullet_evidence = (
            QA_EVIDENCE_ID_PATTERN.search(coverage_item) is not None
            or IMPLEMENT_FILE_ENTRY_PATTERN.search(coverage_item) is not None
        )
        if not has_same_bullet_evidence:
            findings.append(
                context.finding(
                    code=MISSING_EVIDENCE_REF_CODE,
                    message=(
                        "Acceptance coverage bullet for "
                        f"`{criterion_id}` must cite same-bullet evidence "
                        "using an `EV-N` id and/or backticked artifact path."
                    ),
                    severity="high",
                    location=context.location(),
                )
            )
    return tuple(findings)


def validate_qa_report(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    verdict, risks, recommendation, evidence = _qa_sections(context)
    qa_verdict, verdict_findings = _validate_quality_verdict(
        context=context,
        verdict=verdict,
    )
    qa_recommendation, recommendation_findings = _validate_release_recommendation(
        context=context,
        recommendation=recommendation,
    )
    risk_entries = _risk_entry_items(risks)
    evidence_entries = _evidence_entries(evidence)

    findings: list[ValidationFinding] = []
    findings.extend(verdict_findings)
    findings.extend(recommendation_findings)
    findings.extend(
        _validate_residual_risks(
            context=context,
            risks=risks,
            qa_verdict=qa_verdict,
            qa_recommendation=qa_recommendation,
            risk_entry_items=risk_entries,
        )
    )
    findings.extend(
        _validate_evidence_references(
            context=context,
            evidence=evidence,
            evidence_entries=evidence_entries,
        )
    )
    findings.extend(
        _validate_verdict_recommendation_alignment(
            context=context,
            verdict=verdict,
            recommendation=recommendation,
            qa_verdict=qa_verdict,
            qa_recommendation=qa_recommendation,
            has_evidence_entries=bool(evidence_entries),
        )
    )
    findings.extend(_validate_acceptance_coverage(context=context))
    findings.extend(validate_placeholder_sections(context))
    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="qa",
        document_name="qa-report.md",
        validate=validate_qa_report,
    ),
)

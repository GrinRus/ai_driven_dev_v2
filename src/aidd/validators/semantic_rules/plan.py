from __future__ import annotations

import re

from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    INCOMPLETE_SECTION_CODE,
    RISK_MITIGATION_PATTERN,
    SemanticDocumentContext,
    SemanticRule,
    extract_bullet_items,
    extract_milestone_ids,
    extract_risk_blocks,
    normalized_heading,
    validate_placeholder_sections,
)


def _plan_milestone_ids(context: SemanticDocumentContext) -> set[str]:
    milestones = context.section_by_candidates(candidates=("Milestones",))
    if not milestones.content:
        return set()
    return extract_milestone_ids(milestones.content)


def validate_plan(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))
    plan_milestone_ids = _plan_milestone_ids(context)

    for section in context.iter_required_sections():
        normalized_section = normalized_heading(section.name)
        compact_content = re.sub(r"\s+", " ", section.content).strip()
        bullet_items = extract_bullet_items(section.content)

        if normalized_section == "milestones":
            if not bullet_items:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Milestones` must use bullet items "
                            "with stable milestone ids (for example `M1`)."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            elif not plan_milestone_ids:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Milestones` must declare stable milestone ids "
                            "(for example `M1`, `M2`) for sequencing and "
                            "verification mapping."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

        if normalized_section == "dependencies":
            if not bullet_items:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Dependencies` must use bullet items "
                            "so ordering constraints are explicit."
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
                            "Section `Dependencies` cannot be `none`; list explicit "
                            "upstream or sequencing constraints."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

        if normalized_section == "risks":
            risk_blocks = extract_risk_blocks(section.content)
            if not risk_blocks:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Risks` must use bullet items with "
                            "concrete mitigation direction."
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
                            "Section `Risks` cannot be `none`; include concrete delivery "
                            "risks with mitigation intent."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            elif any(RISK_MITIGATION_PATTERN.search(item) is None for item in risk_blocks):
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Each `Risks` item must include mitigation direction "
                            "(for example `mitigation:`)."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

        if normalized_section == "verification notes":
            if not bullet_items:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Required section `Verification notes` must use bullet "
                            "items mapped to milestone ids."
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
                            "Section `Verification notes` cannot be `none`; map checks "
                            "to milestone ids (for example `M1`)."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            else:
                referenced_milestone_ids = extract_milestone_ids(section.content)
                if not referenced_milestone_ids:
                    findings.append(
                        context.finding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Section `Verification notes` must reference milestone ids "
                                "(for example `M1`) to keep checks tied to "
                                "planned increments."
                            ),
                            severity="medium",
                            location=section.location,
                        )
                    )
                else:
                    unknown_milestone_ids = sorted(
                        referenced_milestone_ids - plan_milestone_ids
                    )
                    if unknown_milestone_ids:
                        unknown_ids_text = ", ".join(unknown_milestone_ids)
                        findings.append(
                            context.finding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Verification notes` references "
                                    f"unknown milestone ids: {unknown_ids_text}."
                                ),
                                severity="medium",
                                location=section.location,
                            )
                        )

    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="plan",
        document_name="plan.md",
        validate=validate_plan,
    ),
)

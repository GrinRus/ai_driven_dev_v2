from __future__ import annotations

import re

from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    INCOMPLETE_SECTION_CODE,
    MISSING_EVIDENCE_LINK_CODE,
    SemanticDocumentContext,
    SemanticRule,
    extract_citation_ids,
    normalized_heading,
    validate_placeholder_sections,
)


def _research_source_ids(context: SemanticDocumentContext) -> set[str]:
    sources = context.section_by_candidates(candidates=("Sources",))
    if not sources.content:
        return set()
    return extract_citation_ids(sources.content)


def validate_research_notes(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))
    research_source_ids = _research_source_ids(context)

    for section in context.iter_required_sections():
        normalized_section = normalized_heading(section.name)
        compact_content = re.sub(r"\s+", " ", section.content).strip()

        if normalized_section == "sources" and not research_source_ids:
            findings.append(
                context.finding(
                    code=INCOMPLETE_SECTION_CODE,
                    message=(
                        "Required section `Sources` must declare citation ids "
                        "(for example `[S1]`) for downstream evidence linking."
                    ),
                    severity="medium",
                    location=section.location,
                )
            )

        if normalized_section in {"findings", "evidence trace"}:
            if compact_content.lower() in {"none", "- none"}:
                continue
            referenced_ids = extract_citation_ids(section.content)
            if not referenced_ids:
                findings.append(
                    context.finding(
                        code=MISSING_EVIDENCE_LINK_CODE,
                        message=(
                            f"Section `{section.name}` must reference citation ids from "
                            "`Sources` for material research claims."
                        ),
                        severity="high",
                        location=section.location,
                    )
                )
                continue

            unknown_ids = sorted(referenced_ids - research_source_ids)
            if unknown_ids:
                findings.append(
                    context.finding(
                        code=MISSING_EVIDENCE_LINK_CODE,
                        message=(
                            f"Section `{section.name}` references unknown citation ids: "
                            f"{', '.join(f'[{item}]' for item in unknown_ids)}."
                        ),
                        severity="high",
                        location=section.location,
                    )
                )

    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="research",
        document_name="research-notes.md",
        validate=validate_research_notes,
    ),
)

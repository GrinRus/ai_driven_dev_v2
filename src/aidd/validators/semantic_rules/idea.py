from __future__ import annotations

import re

from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    INCOMPLETE_SECTION_CODE,
    UNSUPPORTED_CLAIM_CODE,
    UNSUPPORTED_CLAIM_PATTERN,
    SemanticDocumentContext,
    SemanticRule,
    has_bullet_items,
    normalized_heading,
    validate_placeholder_sections,
)


def validate_idea_brief(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))

    for section in context.iter_required_sections():
        normalized_section = normalized_heading(section.name)
        compact_content = re.sub(r"\s+", " ", section.content).strip()

        if normalized_section in {"problem statement", "desired outcome"}:
            if compact_content.lower() in {"none", "- none"} or len(compact_content) < 20:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            f"Required section `{section.name}` is too brief to establish "
                            "a reviewable semantic baseline."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

            if UNSUPPORTED_CLAIM_PATTERN.search(compact_content):
                findings.append(
                    context.finding(
                        code=UNSUPPORTED_CLAIM_CODE,
                        message=(
                            f"Section `{section.name}` includes unsupported absolute claims "
                            "without evidence grounding."
                        ),
                        severity="high",
                        location=section.location,
                    )
                )

        if normalized_section in {"constraints", "open questions"}:
            if not has_bullet_items(section.content):
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            f"Required section `{section.name}` must use bullet items "
                            "(or `- none`) so downstream stages can parse "
                            "constraints and open questions deterministically."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="idea",
        document_name="idea-brief.md",
        validate=validate_idea_brief,
    ),
)

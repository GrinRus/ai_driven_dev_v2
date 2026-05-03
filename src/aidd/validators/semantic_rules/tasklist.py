from __future__ import annotations

import re

from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    INCOMPLETE_SECTION_CODE,
    SemanticDocumentContext,
    SemanticRule,
    extract_bullet_items,
    extract_tasklist_task_ids,
    normalized_heading,
    validate_placeholder_sections,
)


def _tasklist_task_ids(context: SemanticDocumentContext) -> set[str]:
    ordered_tasks = context.section_by_candidates(candidates=("Ordered tasks",))
    if not ordered_tasks.content:
        return set()
    return extract_tasklist_task_ids(ordered_tasks.content)


def validate_tasklist(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))
    tasklist_task_ids = _tasklist_task_ids(context)

    for section in context.iter_required_sections():
        normalized_section = normalized_heading(section.name)
        compact_content = re.sub(r"\s+", " ", section.content).strip()
        bullet_items = extract_bullet_items(section.content)

        if normalized_section == "task summary":
            if compact_content.lower() in {"none", "- none"} or len(compact_content) < 30:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Task summary` is too brief to explain decomposition "
                            "scope and sequencing intent."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )

        if normalized_section == "ordered tasks":
            if not tasklist_task_ids:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Ordered tasks` must declare stable task ids "
                            "(for example `TL-1`) in executable order."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            elif not bullet_items and "###" not in section.content:
                findings.append(
                    context.finding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Ordered tasks` must enumerate task entries as bullet "
                            "items or task subheadings with ids."
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
                            "Section `Dependencies` must use bullet items with explicit "
                            "task dependency notes."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            else:
                referenced_task_ids = extract_tasklist_task_ids(section.content)
                if (
                    tasklist_task_ids
                    and not referenced_task_ids
                    and compact_content.lower() not in {"none", "- none"}
                ):
                    findings.append(
                        context.finding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Section `Dependencies` must reference task ids or "
                                "explicitly mark entries as `none`."
                            ),
                            severity="medium",
                            location=section.location,
                        )
                    )
                else:
                    unknown_task_ids = sorted(referenced_task_ids - tasklist_task_ids)
                    if unknown_task_ids:
                        unknown_ids_text = ", ".join(unknown_task_ids)
                        findings.append(
                            context.finding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Dependencies` references unknown task ids: "
                                    f"{unknown_ids_text}."
                                ),
                                severity="medium",
                                location=section.location,
                            )
                        )

                    missing_dependency_entries = sorted(
                        tasklist_task_ids - referenced_task_ids
                    )
                    if missing_dependency_entries and compact_content.lower() not in {
                        "none",
                        "- none",
                    }:
                        missing_ids_text = ", ".join(missing_dependency_entries)
                        findings.append(
                            context.finding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Dependencies` must include explicit entries "
                                    f"for each task id. Missing: {missing_ids_text}."
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
                            "Section `Verification notes` must use bullet items mapped "
                            "to task ids."
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
                            "Section `Verification notes` cannot be `none`; include at "
                            "least one concrete check per task."
                        ),
                        severity="medium",
                        location=section.location,
                    )
                )
            else:
                referenced_task_ids = extract_tasklist_task_ids(section.content)
                if tasklist_task_ids and not referenced_task_ids:
                    findings.append(
                        context.finding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Section `Verification notes` must reference task ids "
                                "so checks map to task decomposition."
                            ),
                            severity="medium",
                            location=section.location,
                        )
                    )
                else:
                    unknown_task_ids = sorted(referenced_task_ids - tasklist_task_ids)
                    if unknown_task_ids:
                        unknown_ids_text = ", ".join(unknown_task_ids)
                        findings.append(
                            context.finding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Verification notes` references unknown task "
                                    f"ids: {unknown_ids_text}."
                                ),
                                severity="medium",
                                location=section.location,
                            )
                        )

                    missing_verification_entries = sorted(
                        tasklist_task_ids - referenced_task_ids
                    )
                    if missing_verification_entries:
                        missing_ids_text = ", ".join(missing_verification_entries)
                        findings.append(
                            context.finding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Verification notes` must include at least one "
                                    f"check per task id. Missing: {missing_ids_text}."
                                ),
                                severity="medium",
                                location=section.location,
                            )
                        )

    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="tasklist",
        document_name="tasklist.md",
        validate=validate_tasklist,
    ),
)

from __future__ import annotations

import re
from collections.abc import Callable

from aidd.core.task_plan import TaskPlanParseError, parse_task_plan
from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    INCOMPLETE_SECTION_CODE,
    SemanticDocumentContext,
    SemanticRule,
    SemanticSection,
    extract_bullet_items,
    extract_tasklist_task_ids,
    validate_placeholder_sections,
)


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _tasklist_task_ids(context: SemanticDocumentContext) -> set[str]:
    ordered_tasks = context.section_by_candidates(candidates=("Ordered tasks",))
    if not ordered_tasks.content:
        return set()
    return extract_tasklist_task_ids(ordered_tasks.content)


def _validate_task_summary(
    context: SemanticDocumentContext,
    section: SemanticSection,
    tasklist_task_ids: set[str],
) -> tuple[ValidationFinding, ...]:
    del tasklist_task_ids
    compact_content = _compact_text(section.content)
    if compact_content.lower() not in {"none", "- none"} and len(compact_content) >= 30:
        return tuple()
    return (
        context.finding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Task summary` is too brief to explain decomposition "
                "scope and sequencing intent."
            ),
            severity="medium",
            location=section.location,
        ),
    )


def _validate_ordered_tasks(
    context: SemanticDocumentContext,
    section: SemanticSection,
    tasklist_task_ids: set[str],
) -> tuple[ValidationFinding, ...]:
    bullet_items = extract_bullet_items(section.content)
    if not tasklist_task_ids:
        return (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Ordered tasks` must declare stable task ids "
                    "(for example `TL-1`) in executable order."
                ),
                severity="medium",
                location=section.location,
            ),
        )
    if bullet_items or "###" in section.content:
        return tuple()
    return (
        context.finding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Ordered tasks` must enumerate task entries as bullet "
                "items or task subheadings with ids."
            ),
            severity="medium",
            location=section.location,
        ),
    )


def _unknown_task_id_findings(
    *,
    context: SemanticDocumentContext,
    section: SemanticSection,
    referenced_task_ids: set[str],
    tasklist_task_ids: set[str],
    section_name: str,
) -> list[ValidationFinding]:
    unknown_task_ids = sorted(referenced_task_ids - tasklist_task_ids)
    if not unknown_task_ids:
        return []
    unknown_ids_text = ", ".join(unknown_task_ids)
    return [
        context.finding(
            code=INCOMPLETE_SECTION_CODE,
            message=f"Section `{section_name}` references unknown task ids: {unknown_ids_text}.",
            severity="medium",
            location=section.location,
        )
    ]


def _validate_dependencies(
    context: SemanticDocumentContext,
    section: SemanticSection,
    tasklist_task_ids: set[str],
) -> tuple[ValidationFinding, ...]:
    compact_content = _compact_text(section.content)
    bullet_items = extract_bullet_items(section.content)
    if not bullet_items:
        return (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Dependencies` must use bullet items with explicit "
                    "task dependency notes."
                ),
                severity="medium",
                location=section.location,
            ),
        )

    referenced_task_ids = extract_tasklist_task_ids(section.content)
    if (
        tasklist_task_ids
        and not referenced_task_ids
        and compact_content.lower()
        not in {
            "none",
            "- none",
        }
    ):
        return (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Dependencies` must reference task ids or "
                    "explicitly mark entries as `none`."
                ),
                severity="medium",
                location=section.location,
            ),
        )

    findings = _unknown_task_id_findings(
        context=context,
        section=section,
        referenced_task_ids=referenced_task_ids,
        tasklist_task_ids=tasklist_task_ids,
        section_name="Dependencies",
    )
    missing_dependency_entries = sorted(tasklist_task_ids - referenced_task_ids)
    if missing_dependency_entries and compact_content.lower() not in {"none", "- none"}:
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
    return tuple(findings)


def _validate_verification_notes(
    context: SemanticDocumentContext,
    section: SemanticSection,
    tasklist_task_ids: set[str],
) -> tuple[ValidationFinding, ...]:
    compact_content = _compact_text(section.content)
    bullet_items = extract_bullet_items(section.content)
    if not bullet_items:
        return (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=("Section `Verification notes` must use bullet items mapped to task ids."),
                severity="medium",
                location=section.location,
            ),
        )
    if compact_content.lower() in {"none", "- none"}:
        return (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Verification notes` cannot be `none`; include at "
                    "least one concrete check per task."
                ),
                severity="medium",
                location=section.location,
            ),
        )

    referenced_task_ids = extract_tasklist_task_ids(section.content)
    if tasklist_task_ids and not referenced_task_ids:
        return (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Verification notes` must reference task ids "
                    "so checks map to task decomposition."
                ),
                severity="medium",
                location=section.location,
            ),
        )

    findings = _unknown_task_id_findings(
        context=context,
        section=section,
        referenced_task_ids=referenced_task_ids,
        tasklist_task_ids=tasklist_task_ids,
        section_name="Verification notes",
    )
    missing_verification_entries = sorted(tasklist_task_ids - referenced_task_ids)
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


_SECTION_RULES: dict[
    str,
    Callable[
        [SemanticDocumentContext, SemanticSection, set[str]],
        tuple[ValidationFinding, ...],
    ],
] = {
    "task summary": _validate_task_summary,
    "ordered tasks": _validate_ordered_tasks,
    "dependencies": _validate_dependencies,
    "verification notes": _validate_verification_notes,
}


def validate_tasklist(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))
    summary = context.section_by_candidates(candidates=("Task summary",))
    findings.extend(_validate_task_summary(context, summary, set()))
    try:
        parse_task_plan("\n".join(context.markdown_lines))
    except TaskPlanParseError as exc:
        ordered_tasks = context.section_by_candidates(candidates=("Ordered tasks",))
        findings.extend(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=issue,
                severity="medium",
                location=ordered_tasks.location,
            )
            for issue in exc.issues
        )

    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="tasklist",
        document_name="tasklist.md",
        validate=validate_tasklist,
    ),
)

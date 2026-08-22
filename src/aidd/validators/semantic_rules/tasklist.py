from __future__ import annotations

import re
from collections.abc import Callable

from aidd.core.task_plan import (
    TaskPlanParseError,
    TaskPlanParseIssue,
    parse_task_plan,
)
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


def _task_plan_issue_signature(issue: TaskPlanParseIssue) -> tuple[object, ...]:
    """Return a stable signature for one shared card-grammar failure.

    The parser keeps one located issue per card so callers that need card-level evidence do
    not lose source identity.  The semantic validator has a different responsibility: it
    should give the runtime one repair target when the same card grammar is broken repeatedly.
    Normalize only the owning task id here.  Other ids remain in the signature because an
    unknown dependency or a duplicate mapping can be an independent failure for each entry.
    """

    message = issue.message
    if issue.task_id:
        message = message.replace(f"`{issue.task_id}`", "`<task-id>`")
    return (
        str(issue.kind),
        issue.field,
        issue.missing_fields,
        message,
    )


def _collapse_task_plan_issues(
    issues: tuple[TaskPlanParseIssue, ...],
) -> tuple[tuple[TaskPlanParseIssue, ...], ...]:
    """Collapse repeated root causes while retaining the first exact source line.

    ``TaskPlanParseError`` deliberately retains related derivative issues (for example a
    missing scope path after an unsafe scope path).  They are useful to parser callers but do
    not deserve separate semantic repair messages.  Independent root issues stay separate,
    while repeated card issues share one group and therefore one repair finding.
    """

    groups: list[list[TaskPlanParseIssue]] = []
    by_signature: dict[tuple[object, ...], int] = {}
    for issue in issues:
        if issue.relation.value == "related":
            continue
        signature = _task_plan_issue_signature(issue)
        index = by_signature.get(signature)
        if index is None:
            by_signature[signature] = len(groups)
            groups.append([issue])
        else:
            groups[index].append(issue)
    return tuple(tuple(group) for group in groups)


def _render_task_plan_issue_group(group: tuple[TaskPlanParseIssue, ...]) -> str:
    first = group[0]
    if len(group) == 1:
        return first.message

    task_ids = tuple(dict.fromkeys(issue.task_id for issue in group if issue.task_id))
    missing_fields = tuple(
        dict.fromkeys(
            field
            for issue in group
            for field in issue.missing_fields
            if field
        )
    )
    if task_ids:
        ids_text = ", ".join(f"`{task_id}`" for task_id in task_ids)
        fields_text = (
            f"missing required field(s) {', '.join(f'`{field}`' for field in missing_fields)}"
            if missing_fields
            else "missing required card grammar"
        )
        return (
            "Task-card grammar has one shared root issue for task ids "
            f"{ids_text}: {fields_text}. "
            "Repair the affected cards using the canonical rich-task card shape; "
            "unrelated valid cards do not need changes."
        )

    return (
        f"Tasklist grammar has {len(group)} repeated `{first.kind}` issues. "
        "Repair the first offending line and preserve unrelated valid sections."
    )


def validate_tasklist(context: SemanticDocumentContext) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))
    summary = context.section_by_candidates(candidates=("Task summary",))
    findings.extend(_validate_task_summary(context, summary, set()))
    try:
        parse_task_plan("\n".join(context.markdown_lines))
    except TaskPlanParseError as exc:
        ordered_tasks = context.section_by_candidates(candidates=("Ordered tasks",))
        for issue_group in _collapse_task_plan_issues(exc.issues):
            first_issue = issue_group[0]
            findings.append(
                context.finding(
                    code=INCOMPLETE_SECTION_CODE,
                    message=_render_task_plan_issue_group(issue_group),
                    severity="medium",
                    location=(
                        context.location(line_number=first_issue.line_number)
                        if first_issue.line_number is not None
                        else ordered_tasks.location
                    ),
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

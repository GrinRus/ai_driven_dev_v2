from __future__ import annotations

import re

from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    IMPLEMENT_ARTIFACT_REFERENCE_PATTERN,
    IMPLEMENT_COMPLETION_CLAIM_PATTERN,
    IMPLEMENT_FILE_ENTRY_PATTERN,
    IMPLEMENT_NOOP_JUSTIFICATION_PATTERN,
    IMPLEMENT_RESULT_PATTERN,
    INCOMPLETE_EXECUTION_SUMMARY_CODE,
    INCOMPLETE_SECTION_CODE,
    MISSING_DIFF_EVIDENCE_CODE,
    UNVERIFIABLE_CHECK_CLAIM_CODE,
    SemanticDocumentContext,
    SemanticRule,
    SemanticSection,
    extract_implementation_verification_blocks,
    extract_tasklist_task_ids,
    extract_top_level_bullet_blocks,
    has_implementation_command_evidence,
    is_deferred_implementation_verification,
    validate_placeholder_sections,
    validate_setup_ignored_workspace_status_evidence,
)

SELECTED_TASK_ID_PATTERN = re.compile(r"\bTASK-[A-Z0-9][A-Z0-9-]*[A-Z0-9]\b")


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _implementation_sections(
    context: SemanticDocumentContext,
) -> tuple[SemanticSection, SemanticSection, SemanticSection, SemanticSection, SemanticSection]:
    selected_task = context.section_by_candidates(
        candidates=("Selected task", "Selected task id", "Selected task ids", "Summary"),
    )
    summary = context.section_by_candidates(candidates=("Change summary", "Summary"))
    touched_files = context.section_by_candidates(candidates=("Touched files",))
    verification = context.section_by_candidates(
        candidates=("Verification notes", "Verification"),
    )
    follow_up = context.section_by_candidates(
        candidates=("Follow-up notes", "Follow-up", "Risks"),
    )
    if not selected_task.content and summary.content:
        selected_task = summary
    return selected_task, summary, touched_files, verification, follow_up


def _validate_selected_task(
    *,
    context: SemanticDocumentContext,
    selected_task: SemanticSection,
) -> tuple[ValidationFinding, ...]:
    if (
        extract_tasklist_task_ids(selected_task.content)
        or SELECTED_TASK_ID_PATTERN.search(selected_task.content)
    ):
        return tuple()
    return (
        context.finding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Selected task` must include a stable selected task "
                "or tasklist id (for example `TASK-EXAMPLE` or `TL-2`)."
            ),
            severity="medium",
            location=selected_task.location,
        ),
    )


def _validate_change_summary(
    *,
    context: SemanticDocumentContext,
    summary: SemanticSection,
) -> tuple[ValidationFinding, ...]:
    compact_summary_content = _compact_text(summary.content)
    if compact_summary_content.lower() not in {"none", "- none"} and len(
        compact_summary_content
    ) >= 30:
        return tuple()
    return (
        context.finding(
            code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
            message=(
                "Section `Change summary` is too brief to explain task intent, "
                "actual edits, and execution outcome."
            ),
            severity="medium",
            location=summary.location,
        ),
    )


def _validate_real_touched_file_entries(
    *,
    context: SemanticDocumentContext,
    touched_files: SemanticSection,
    touched_file_items: tuple[str, ...],
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    if any(
        IMPLEMENT_FILE_ENTRY_PATTERN.search(item) is None
        for item in touched_file_items
        if item.lower() != "none"
    ):
        findings.append(
            context.finding(
                code=MISSING_DIFF_EVIDENCE_CODE,
                message="Section `Touched files` entries must include file paths in backticks.",
                severity="high",
                location=touched_files.location,
            )
        )

    if any(
        " - " not in item and ":" not in item and "->" not in item
        for item in touched_file_items
        if item.lower() != "none"
    ):
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Each `Touched files` entry must include short change intent "
                    "after the path."
                ),
                severity="medium",
                location=touched_files.location,
            )
        )
    return tuple(findings)


def _validate_noop_touched_file_entries(
    *,
    context: SemanticDocumentContext,
    summary: SemanticSection,
    follow_up: SemanticSection,
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    no_op_context = " ".join((summary.content, follow_up.content))
    if IMPLEMENT_NOOP_JUSTIFICATION_PATTERN.search(no_op_context) is None:
        findings.append(
            context.finding(
                code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
                message=(
                    "No-op output requires explicit evidence-backed justification "
                    "in summary or follow-up notes."
                ),
                severity="medium",
                location=summary.location,
            )
        )

    compact_follow_up_content = _compact_text(follow_up.content)
    if compact_follow_up_content.lower() in {"", "none", "- none"}:
        findings.append(
            context.finding(
                code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
                message=(
                    "No-op output must include an actionable next step in "
                    "`Follow-up notes`."
                ),
                severity="medium",
                location=follow_up.location,
            )
        )

    if IMPLEMENT_COMPLETION_CLAIM_PATTERN.search(_compact_text(summary.content)):
        findings.append(
            context.finding(
                code=MISSING_DIFF_EVIDENCE_CODE,
                message=(
                    "Change summary claims completed implementation but "
                    "touched-files list is empty."
                ),
                severity="high",
                location=summary.location,
            )
        )
    return tuple(findings)


def _validate_touched_files(
    *,
    context: SemanticDocumentContext,
    summary: SemanticSection,
    touched_files: SemanticSection,
    follow_up: SemanticSection,
) -> tuple[ValidationFinding, ...]:
    touched_file_items = extract_top_level_bullet_blocks(touched_files.content)
    if not touched_file_items:
        return (
            context.finding(
                code=MISSING_DIFF_EVIDENCE_CODE,
                message=(
                    "Section `Touched files` must list concrete file entries "
                    "or explicit no-op justification."
                ),
                severity="high",
                location=touched_files.location,
            ),
        )

    has_real_touched_file_entries = any(item.lower() != "none" for item in touched_file_items)
    if has_real_touched_file_entries:
        return _validate_real_touched_file_entries(
            context=context,
            touched_files=touched_files,
            touched_file_items=touched_file_items,
        )
    return _validate_noop_touched_file_entries(
        context=context,
        summary=summary,
        follow_up=follow_up,
    )


def _validate_verification_item(
    *,
    context: SemanticDocumentContext,
    verification: SemanticSection,
    verification_item: str,
) -> tuple[ValidationFinding, ...]:
    normalized_item = verification_item.lower()
    if normalized_item in {"none", "not run"} or is_deferred_implementation_verification(
        verification_item
    ):
        return tuple()

    has_command_reference = has_implementation_command_evidence(verification_item)
    has_result_reference = IMPLEMENT_RESULT_PATTERN.search(verification_item) is not None
    has_artifact_reference = (
        IMPLEMENT_ARTIFACT_REFERENCE_PATTERN.search(verification_item) is not None
    )
    if has_result_reference and not has_command_reference and not has_artifact_reference:
        return (
            context.finding(
                code=UNVERIFIABLE_CHECK_CLAIM_CODE,
                message=(
                    "Verification note includes outcome claim without executable "
                    "command evidence."
                ),
                severity="high",
                location=verification.location,
            ),
        )

    if has_command_reference and not has_result_reference:
        return (
            context.finding(
                code=UNVERIFIABLE_CHECK_CLAIM_CODE,
                message=(
                    "Verification note must include observed command outcome "
                    "(for example `-> pass` or exit code)."
                ),
                severity="medium",
                location=verification.location,
            ),
        )
    return tuple()


def _validate_verification_notes(
    *,
    context: SemanticDocumentContext,
    verification: SemanticSection,
) -> tuple[ValidationFinding, ...]:
    verification_items = extract_implementation_verification_blocks(verification.content)
    if not verification_items:
        return (
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message="Section `Verification notes` must list concrete checks and outcomes.",
                severity="medium",
                location=verification.location,
            ),
        )

    findings: list[ValidationFinding] = []
    for verification_item in verification_items:
        item_findings = _validate_verification_item(
            context=context,
            verification=verification,
            verification_item=verification_item,
        )
        findings.extend(item_findings)
        if item_findings and item_findings[0].severity == "high":
            continue
    findings.extend(
        validate_setup_ignored_workspace_status_evidence(
            context=context,
            evidence_text=verification.content,
            location=verification.location,
            code=UNVERIFIABLE_CHECK_CLAIM_CODE,
            message=(
                "Workspace implementation verification ran test/type/lint/build checks "
                "that can create ignored workspace residue, but `Verification notes` "
                "do not cite `git status --ignored --short --untracked-files=all`."
            ),
        )
    )
    return tuple(findings)


def validate_implementation_report(
    context: SemanticDocumentContext,
) -> tuple[ValidationFinding, ...]:
    selected_task, summary, touched_files, verification, follow_up = _implementation_sections(
        context
    )
    findings: list[ValidationFinding] = []
    findings.extend(_validate_selected_task(context=context, selected_task=selected_task))
    findings.extend(_validate_change_summary(context=context, summary=summary))
    findings.extend(
        _validate_touched_files(
            context=context,
            summary=summary,
            touched_files=touched_files,
            follow_up=follow_up,
        )
    )
    findings.extend(_validate_verification_notes(context=context, verification=verification))
    findings.extend(validate_placeholder_sections(context))
    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="implement",
        document_name="implementation-report.md",
        validate=validate_implementation_report,
    ),
)

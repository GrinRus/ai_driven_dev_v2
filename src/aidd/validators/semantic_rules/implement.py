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
    extract_implementation_verification_blocks,
    extract_tasklist_task_ids,
    extract_top_level_bullet_blocks,
    has_implementation_command_evidence,
    is_deferred_implementation_verification,
    validate_placeholder_sections,
)


def validate_implementation_report(
    context: SemanticDocumentContext,
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
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

    if not extract_tasklist_task_ids(selected_task.content):
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Selected task` must include a stable task id "
                    "(for example `TL-2`)."
                ),
                severity="medium",
                location=selected_task.location,
            )
        )

    compact_summary_content = re.sub(r"\s+", " ", summary.content).strip()
    if compact_summary_content.lower() in {"none", "- none"} or len(compact_summary_content) < 30:
        findings.append(
            context.finding(
                code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
                message=(
                    "Section `Change summary` is too brief to explain task intent, "
                    "actual edits, and execution outcome."
                ),
                severity="medium",
                location=summary.location,
            )
        )

    touched_file_items = extract_top_level_bullet_blocks(touched_files.content)
    if not touched_file_items:
        findings.append(
            context.finding(
                code=MISSING_DIFF_EVIDENCE_CODE,
                message=(
                    "Section `Touched files` must list concrete file entries "
                    "or explicit no-op justification."
                ),
                severity="high",
                location=touched_files.location,
            )
        )

    has_real_touched_file_entries = any(item.lower() != "none" for item in touched_file_items)
    if has_real_touched_file_entries:
        if any(
            IMPLEMENT_FILE_ENTRY_PATTERN.search(item) is None
            for item in touched_file_items
            if item.lower() != "none"
        ):
            findings.append(
                context.finding(
                    code=MISSING_DIFF_EVIDENCE_CODE,
                    message=(
                        "Section `Touched files` entries must include file paths "
                        "in backticks."
                    ),
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
    else:
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

        compact_follow_up_content = re.sub(r"\s+", " ", follow_up.content).strip()
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

        if IMPLEMENT_COMPLETION_CLAIM_PATTERN.search(compact_summary_content):
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

    verification_items = extract_implementation_verification_blocks(verification.content)
    if not verification_items:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message="Section `Verification notes` must list concrete checks and outcomes.",
                severity="medium",
                location=verification.location,
            )
        )
    else:
        for verification_item in verification_items:
            normalized_item = verification_item.lower()
            if (
                normalized_item in {"none", "not run"}
                or is_deferred_implementation_verification(verification_item)
            ):
                continue

            has_command_reference = has_implementation_command_evidence(verification_item)
            has_result_reference = IMPLEMENT_RESULT_PATTERN.search(verification_item) is not None
            has_artifact_reference = (
                IMPLEMENT_ARTIFACT_REFERENCE_PATTERN.search(verification_item) is not None
            )
            if (
                has_result_reference
                and not has_command_reference
                and not has_artifact_reference
            ):
                findings.append(
                    context.finding(
                        code=UNVERIFIABLE_CHECK_CLAIM_CODE,
                        message=(
                            "Verification note includes outcome claim without executable "
                            "command evidence."
                        ),
                        severity="high",
                        location=verification.location,
                    )
                )
                continue

            if has_command_reference and not has_result_reference:
                findings.append(
                    context.finding(
                        code=UNVERIFIABLE_CHECK_CLAIM_CODE,
                        message=(
                            "Verification note must include observed command outcome "
                            "(for example `-> pass` or exit code)."
                        ),
                        severity="medium",
                        location=verification.location,
                    )
                )

    findings.extend(validate_placeholder_sections(context))
    return tuple(findings)


RULES: tuple[SemanticRule, ...] = (
    SemanticRule(
        stage="implement",
        document_name="implementation-report.md",
        validate=validate_implementation_report,
    ),
)

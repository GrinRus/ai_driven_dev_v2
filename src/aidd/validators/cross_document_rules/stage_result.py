from __future__ import annotations

import re

from aidd.validators.cross_document_rules.context import (
    CrossDocumentContext,
    extract_section_lines,
    heading_line_number,
    workspace_relative,
)
from aidd.validators.models import ValidationFinding, ValidationIssueLocation

REPAIR_MENTION_WITHOUT_BRIEF_CODE = "CROSS-REPAIR-MENTION-WITHOUT-BRIEF"
REPAIR_BRIEF_NOT_REFERENCED_CODE = "CROSS-REPAIR-BRIEF-NOT-REFERENCED"
REPAIR_BUDGET_EXHAUSTED_CODE = "CROSS-REPAIR-BUDGET-EXHAUSTED"
PROJECT_SET_EVIDENCE_MISSING_CODE = "CROSS-PROJECT-SET-EVIDENCE-MISSING"

_REPAIR_BUDGET_EXHAUSTED_TOKEN = "repair-budget-exhausted"
_STAGE_STATUS_PATTERN = re.compile(
    r"`?(succeeded|failed|blocked|needs-input)`?", re.IGNORECASE
)
_PROJECT_SET_ROW_PATTERN = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|")
_ATTEMPT_TRIGGER_PATTERN = re.compile(
    r"\bAttempt\s+`?\d+`?\s+\(`?(initial|repair|intervention)`?\)",
    re.IGNORECASE,
)


def _stage_status(stage_result_text: str | None) -> tuple[str | None, int | None]:
    if stage_result_text is None:
        return None, None
    for line_number, line in extract_section_lines(stage_result_text, heading="Status"):
        match = _STAGE_STATUS_PATTERN.search(line)
        if match is not None:
            return match.group(1).lower(), line_number
    return None, None


def _project_set_entries(project_set_text: str) -> tuple[tuple[str, str], ...]:
    return tuple(
        (match.group(1), match.group(2))
        for line in project_set_text.splitlines()
        if (match := _PROJECT_SET_ROW_PATTERN.match(line.strip())) is not None
    )


def _latest_attempt_trigger(stage_result_text: str) -> str | None:
    triggers: list[str] = []
    for _, line in extract_section_lines(stage_result_text, heading="Attempt history"):
        if match := _ATTEMPT_TRIGGER_PATTERN.search(line):
            triggers.append(match.group(1).lower())
    if triggers:
        return triggers[-1]
    if "(`repair`)" in stage_result_text:
        return "repair"
    return None


def _project_set_findings(context: CrossDocumentContext) -> tuple[ValidationFinding, ...]:
    assert context.project_set_text is not None
    assert context.stage_result_text is not None
    project_relative = workspace_relative(context.project_set_path, context.workspace_root)
    result_relative = workspace_relative(context.stage_result_path, context.workspace_root)
    evidence_line = heading_line_number(context.stage_result_text, "Project-set evidence")
    findings: list[ValidationFinding] = []
    if evidence_line is None:
        findings.append(
            ValidationFinding(
                PROJECT_SET_EVIDENCE_MISSING_CODE,
                (
                    "stage-result.md must include `Project-set evidence` when "
                    f"`{project_relative}` exists."
                ),
                "high",
                ValidationIssueLocation(result_relative),
            )
        )
    if f"`{project_relative}`" not in context.stage_result_text:
        findings.append(
            ValidationFinding(
                PROJECT_SET_EVIDENCE_MISSING_CODE,
                (
                    "Project-set evidence must reference the project-set context path "
                    f"`{project_relative}`."
                ),
                "high",
                ValidationIssueLocation(result_relative, evidence_line),
            )
        )
    for project_id, project_root in _project_set_entries(context.project_set_text):
        missing_parts: list[str] = []
        if f"`{project_id}`" not in context.stage_result_text:
            missing_parts.append(f"project id `{project_id}`")
        if f"`{project_root}`" not in context.stage_result_text:
            missing_parts.append(f"project root `{project_root}`")
        if missing_parts:
            findings.append(
                ValidationFinding(
                    PROJECT_SET_EVIDENCE_MISSING_CODE,
                    "Project-set evidence must cite declared "
                    + " and ".join(missing_parts)
                    + ".",
                    "high",
                    ValidationIssueLocation(result_relative, evidence_line),
                )
            )
    return tuple(findings)


def validate_stage_result_links(
    context: CrossDocumentContext,
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    stage_status, stage_status_line = _stage_status(context.stage_result_text)
    if context.stage_result_text is not None:
        result_relative = workspace_relative(context.stage_result_path, context.workspace_root)
        mentions_repair_attempt = _latest_attempt_trigger(context.stage_result_text) == "repair"
        mentions_repair_brief = "repair-brief.md" in context.stage_result_text
        if mentions_repair_attempt and not context.repair_brief_path.exists():
            findings.append(
                ValidationFinding(
                    REPAIR_MENTION_WITHOUT_BRIEF_CODE,
                    "Stage result records a repair attempt but `repair-brief.md` is missing.",
                    "high",
                    ValidationIssueLocation(result_relative),
                )
            )
        if context.repair_brief_path.exists() and not mentions_repair_brief:
            findings.append(
                ValidationFinding(
                    REPAIR_BRIEF_NOT_REFERENCED_CODE,
                    (
                        "`repair-brief.md` exists but stage-result.md does not reference it for "
                        "repair traceability."
                    ),
                    "medium",
                    ValidationIssueLocation(result_relative),
                )
            )
    if (
        context.repair_brief_text is not None
        and _REPAIR_BUDGET_EXHAUSTED_TOKEN in context.repair_brief_text.lower()
        and stage_status != "failed"
    ):
        findings.append(
            ValidationFinding(
                REPAIR_BUDGET_EXHAUSTED_CODE,
                (
                    "`repair-brief.md` declares `repair-budget-exhausted`; "
                    "stage-result.md status must be `failed`."
                ),
                "critical",
                ValidationIssueLocation(
                    workspace_relative(context.stage_result_path, context.workspace_root),
                    stage_status_line,
                ),
            )
        )
    if context.project_set_text is not None and context.stage_result_text is not None:
        findings.extend(_project_set_findings(context))
    return tuple(findings)

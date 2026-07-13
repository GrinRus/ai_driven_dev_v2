from __future__ import annotations

import re

from aidd.core.stage_registry import resolve_expected_output_documents
from aidd.core.stages import next_stage
from aidd.validators.models import ValidationFinding
from aidd.validators.semantic_rules.common import (
    INCOMPLETE_SECTION_CODE,
    SemanticDocumentContext,
    extract_bullet_items,
    validate_placeholder_sections,
)

_STATUS_PATTERN = re.compile(r"\b(succeeded|failed|blocked|needs-input)\b", re.IGNORECASE)
_STAGE_ID_PATTERN = re.compile(r"`?(idea|research|plan|review-spec|tasklist|implement|review|qa)`?")
_ATTEMPT_PATTERN = re.compile(
    r"(?:\bAttempt\s+`?(\d+)`?\b|\battempt-(\d+)\b)",
    re.IGNORECASE,
)


def _immediate_section_body(context: SemanticDocumentContext, heading_name: str) -> str:
    """Return content after a heading only until the next Markdown heading.

    AIDD's repair-history renderer may use ``# Stage`` as the document title while
    runtime-authored documents normally use ``## Stage`` below ``# Stage result``.
    The generic section index follows Markdown nesting, so an H1 section otherwise
    includes every child section and can accidentally pick up the downstream stage
    named in ``Next actions``.
    """

    match = context.first_heading_match(candidates=(heading_name,))
    if match is None:
        return ""
    _, heading = match
    lines = context.markdown_lines
    body: list[str] = []
    for line in lines[heading.line_number :]:
        if re.match(r"^\s{0,3}#{1,6}\s+", line):
            break
        body.append(line)
    return "\n".join(body)


def validate_stage_result(
    context: SemanticDocumentContext,
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = list(validate_placeholder_sections(context))
    stage_section = context.section_by_candidates(candidates=("Stage",))
    stage_body = _immediate_section_body(context, "Stage")
    stage_ids = {match.group(1) for match in _STAGE_ID_PATTERN.finditer(stage_body)}
    if stage_ids != {context.stage}:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Stage` must name exactly the canonical current stage "
                    f"`{context.stage}`."
                ),
                location=stage_section.location,
            )
        )

    history = context.section_by_candidates(candidates=("Attempt history",))
    attempt_numbers = [
        int(match.group(1) or match.group(2))
        for match in _ATTEMPT_PATTERN.finditer(history.content)
    ]
    if (
        not attempt_numbers
        or attempt_numbers[0] <= 0
        or any(
            current <= previous
            for previous, current in zip(attempt_numbers, attempt_numbers[1:], strict=False)
        )
    ):
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message=(
                    "Section `Attempt history` must list positive, unique attempts in "
                    "strictly increasing order."
                ),
                location=history.location,
            )
        )

    status_section = context.section_by_candidates(candidates=("Status",))
    statuses = {
        match.group(1).lower() for match in _STATUS_PATTERN.finditer(status_section.content)
    }
    if len(statuses) != 1:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message="Section `Status` must contain exactly one terminal status.",
                location=status_section.location,
            )
        )
        status = None
    else:
        status = next(iter(statuses))

    if status == "succeeded":
        workitems_index = context.output_path.parts.index("workitems")
        work_item = context.output_path.parts[workitems_index + 1]
        produced_outputs = context.section_by_candidates(candidates=("Produced outputs",))
        expected_names = {
            path.name
            for path in resolve_expected_output_documents(
                stage=context.stage,
                work_item=work_item,
                workspace_root=context.workspace_root,
            )
        }
        missing_names = sorted(
            name for name in expected_names if name not in produced_outputs.content
        )
        if missing_names:
            findings.append(
                context.finding(
                    code=INCOMPLETE_SECTION_CODE,
                    message=(
                        "A succeeded stage-result must list every declared produced output. "
                        "Missing: " + ", ".join(missing_names) + "."
                    ),
                    location=produced_outputs.location,
                )
            )

    blockers = context.section_by_candidates(candidates=("Blockers",))
    blocker_items = extract_bullet_items(blockers.content)
    blockers_are_none = bool(blocker_items) and all(
        item.strip().lower().strip("` .") == "none" for item in blocker_items
    )
    if status == "succeeded" and not blockers_are_none:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message="A succeeded stage-result must declare `- none` in `Blockers`.",
                location=blockers.location,
            )
        )
    if status in {"blocked", "needs-input"} and blockers_are_none:
        findings.append(
            context.finding(
                code=INCOMPLETE_SECTION_CODE,
                message="A blocked stage-result must name at least one concrete blocker.",
                location=blockers.location,
            )
        )

    expected_next = next_stage(context.stage)
    if status == "succeeded" and expected_next is not None:
        actions = context.section_by_candidates(candidates=("Next actions",))
        if (
            re.search(
                rf"(?<![\w-]){re.escape(expected_next)}(?![\w-])",
                actions.content,
            )
            is None
        ):
            findings.append(
                context.finding(
                    code=INCOMPLETE_SECTION_CODE,
                    message=(
                        "A succeeded stage-result must name the immediate canonical next "
                        f"stage `{expected_next}` in `Next actions`."
                    ),
                    location=actions.location,
                )
            )
    return tuple(findings)


__all__ = ["validate_stage_result"]

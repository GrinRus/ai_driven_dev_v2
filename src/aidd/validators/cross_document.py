from __future__ import annotations

import re
from pathlib import Path

from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT, load_stage_manifest
from aidd.validators.models import ValidationFinding, ValidationIssueLocation

ANSWER_WITHOUT_QUESTION_CODE = "CROSS-ANSWER-WITHOUT-QUESTION"
DUPLICATE_QUESTION_ID_CODE = "CROSS-DUPLICATE-QUESTION-ID"
DUPLICATE_ANSWER_ID_CODE = "CROSS-DUPLICATE-ANSWER-ID"
REPAIR_MENTION_WITHOUT_BRIEF_CODE = "CROSS-REPAIR-MENTION-WITHOUT-BRIEF"
REPAIR_BRIEF_NOT_REFERENCED_CODE = "CROSS-REPAIR-BRIEF-NOT-REFERENCED"
BLOCKING_UNANSWERED_CODE = "CROSS-BLOCKING-UNANSWERED"
REPAIR_BUDGET_EXHAUSTED_CODE = "CROSS-REPAIR-BUDGET-EXHAUSTED"

_QUESTION_ID_PATTERN = re.compile(r"`?(Q[\w-]+)`?\s+`?\[(blocking|non-blocking)\]`?")
_ANSWER_ID_PATTERN = re.compile(r"`?(Q[\w-]+)`?\s+`?\[(resolved|partial|deferred)\]`?")
_REPAIR_BUDGET_EXHAUSTED_TOKEN = "repair-budget-exhausted"
_STAGE_STATUS_PATTERN = re.compile(r"`?(succeeded|failed|blocked|needs-input)`?", re.IGNORECASE)


def _stage_root(*, workspace_root: Path, work_item: str, stage: str) -> Path:
    return workspace_root / "workitems" / work_item / "stages" / stage


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _extract_section_lines(markdown_text: str, heading: str) -> list[tuple[int, str]]:
    target = heading.strip().lower()
    in_section = False
    section_lines: list[tuple[int, str]] = []

    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        stripped = line.strip()
        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if heading_match:
            section_title = heading_match.group(2).strip().lower()
            if in_section and section_title != target:
                break
            in_section = section_title == target
            continue

        if in_section:
            section_lines.append((line_number, line))

    return section_lines


def _extract_stage_status(stage_result_text: str) -> tuple[str | None, int | None]:
    for line_number, line in _extract_section_lines(stage_result_text, heading="Status"):
        match = _STAGE_STATUS_PATTERN.search(line)
        if match is None:
            continue
        return match.group(1).lower(), line_number
    return None, None


def _collect_question_ids(
    questions_text: str,
) -> tuple[dict[str, int], tuple[ValidationFinding, ...]]:
    question_ids: dict[str, int] = {}
    findings: list[ValidationFinding] = []
    for line_number, line in enumerate(questions_text.splitlines(), start=1):
        match = _QUESTION_ID_PATTERN.search(line)
        if match is None:
            continue
        question_id = match.group(1)
        if question_id in question_ids:
            findings.append(
                ValidationFinding(
                    code=DUPLICATE_QUESTION_ID_CODE,
                    message=f"Duplicate question id `{question_id}` in questions.md.",
                    severity="high",
                    location=ValidationIssueLocation(
                        workspace_relative_path="questions.md",
                        line_number=line_number,
                    ),
                )
            )
            continue
        question_ids[question_id] = line_number
    return question_ids, tuple(findings)


def _collect_answer_ids(answers_text: str) -> tuple[dict[str, int], tuple[ValidationFinding, ...]]:
    answer_ids: dict[str, int] = {}
    findings: list[ValidationFinding] = []
    for line_number, line in enumerate(answers_text.splitlines(), start=1):
        match = _ANSWER_ID_PATTERN.search(line)
        if match is None:
            continue
        question_id = match.group(1)
        if question_id in answer_ids:
            findings.append(
                ValidationFinding(
                    code=DUPLICATE_ANSWER_ID_CODE,
                    message=f"Duplicate answer id `{question_id}` in answers.md.",
                    severity="high",
                    location=ValidationIssueLocation(
                        workspace_relative_path="answers.md",
                        line_number=line_number,
                    ),
                )
            )
            continue
        answer_ids[question_id] = line_number
    return answer_ids, tuple(findings)


def _collect_resolved_answer_ids(answers_text: str) -> set[str]:
    resolved_ids: set[str] = set()
    for line in answers_text.splitlines():
        match = _ANSWER_ID_PATTERN.search(line)
        if match is None:
            continue
        question_id = match.group(1)
        marker = match.group(2)
        if marker == "resolved":
            resolved_ids.add(question_id)
    return resolved_ids


def _collect_blocking_question_ids(questions_text: str) -> dict[str, int]:
    blocking_ids: dict[str, int] = {}
    for line_number, line in enumerate(questions_text.splitlines(), start=1):
        match = _QUESTION_ID_PATTERN.search(line)
        if match is None:
            continue
        question_id = match.group(1)
        marker = match.group(2)
        if marker == "blocking":
            blocking_ids.setdefault(question_id, line_number)
    return blocking_ids


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def validate_cross_document_consistency(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[ValidationFinding, ...]:
    # Dependency guard: validation should fail fast if stage contract is invalid.
    load_stage_manifest(stage=stage, contracts_root=contracts_root)

    stage_root = _stage_root(workspace_root=workspace_root, work_item=work_item, stage=stage)
    questions_path = stage_root / "questions.md"
    answers_path = stage_root / "answers.md"
    repair_brief_path = stage_root / "repair-brief.md"
    stage_result_path = stage_root / "stage-result.md"

    findings: list[ValidationFinding] = []

    questions_text = _read_optional(questions_path)
    answers_text = _read_optional(answers_path)
    stage_result_text = _read_optional(stage_result_path)
    repair_brief_text = _read_optional(repair_brief_path)

    question_ids: dict[str, int] = {}
    answer_ids: dict[str, int] = {}
    resolved_answer_ids: set[str] = set()
    blocking_question_ids: dict[str, int] = {}
    stage_status, stage_status_line = (
        _extract_stage_status(stage_result_text) if stage_result_text is not None else (None, None)
    )

    if questions_text is not None:
        question_ids, question_findings = _collect_question_ids(questions_text)
        blocking_question_ids = _collect_blocking_question_ids(questions_text)
        for finding in question_findings:
            findings.append(
                ValidationFinding(
                    code=finding.code,
                    message=finding.message,
                    severity=finding.severity,
                    location=ValidationIssueLocation(
                        workspace_relative_path=_workspace_relative(questions_path, workspace_root),
                        line_number=finding.location.line_number if finding.location else None,
                    ),
                )
            )

    if answers_text is not None:
        answer_ids, answer_findings = _collect_answer_ids(answers_text)
        resolved_answer_ids = _collect_resolved_answer_ids(answers_text)
        for finding in answer_findings:
            findings.append(
                ValidationFinding(
                    code=finding.code,
                    message=finding.message,
                    severity=finding.severity,
                    location=ValidationIssueLocation(
                        workspace_relative_path=_workspace_relative(answers_path, workspace_root),
                        line_number=finding.location.line_number if finding.location else None,
                    ),
                )
            )

        for question_id, line_number in answer_ids.items():
            if question_id in question_ids:
                continue
            findings.append(
                ValidationFinding(
                    code=ANSWER_WITHOUT_QUESTION_CODE,
                    message=(
                        f"Answer references `{question_id}` but no matching question exists in "
                        "questions.md."
                    ),
                    severity="high",
                    location=ValidationIssueLocation(
                        workspace_relative_path=_workspace_relative(answers_path, workspace_root),
                        line_number=line_number,
                    ),
                )
            )

    for question_id, line_number in blocking_question_ids.items():
        if question_id in resolved_answer_ids:
            continue
        message = (
            f"`{question_id}` is marked `[blocking]` and has no matching `[resolved]` answer in "
            "`answers.md`."
        )
        if stage_status == "succeeded":
            message += " Stage status must not be `succeeded` while blocking questions remain."
        findings.append(
            ValidationFinding(
                code=BLOCKING_UNANSWERED_CODE,
                message=message,
                severity="critical",
                location=ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(questions_path, workspace_root),
                    line_number=line_number,
                ),
            )
        )

    repair_brief_exists = repair_brief_path.exists()
    if stage_result_text is not None:
        mentions_repair_attempt = "(`repair`)" in stage_result_text
        mentions_repair_brief = "repair-brief.md" in stage_result_text

        if mentions_repair_attempt and not repair_brief_exists:
            findings.append(
                ValidationFinding(
                    code=REPAIR_MENTION_WITHOUT_BRIEF_CODE,
                    message=(
                        "Stage result records a repair attempt but `repair-brief.md` is missing."
                    ),
                    severity="high",
                    location=ValidationIssueLocation(
                        workspace_relative_path=_workspace_relative(
                            stage_result_path, workspace_root
                        ),
                    ),
                )
            )

        if repair_brief_exists and not mentions_repair_brief:
            findings.append(
                ValidationFinding(
                    code=REPAIR_BRIEF_NOT_REFERENCED_CODE,
                    message=(
                        "`repair-brief.md` exists but stage-result.md does not reference it for "
                        "repair traceability."
                    ),
                    severity="medium",
                    location=ValidationIssueLocation(
                        workspace_relative_path=_workspace_relative(
                            stage_result_path, workspace_root
                        ),
                    ),
                )
            )

    if (
        repair_brief_text is not None
        and _REPAIR_BUDGET_EXHAUSTED_TOKEN in repair_brief_text.lower()
        and stage_status != "failed"
    ):
        findings.append(
            ValidationFinding(
                code=REPAIR_BUDGET_EXHAUSTED_CODE,
                message=(
                    "`repair-brief.md` declares `repair-budget-exhausted`; "
                    "stage-result.md status must be `failed`."
                ),
                severity="critical",
                location=ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(stage_result_path, workspace_root),
                    line_number=stage_status_line,
                ),
            )
        )

    return tuple(findings)

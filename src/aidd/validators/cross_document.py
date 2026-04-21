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

_QUESTION_ID_PATTERN = re.compile(r"`(Q[\w-]+)`\s+`\[(blocking|non-blocking)\]`")
_ANSWER_ID_PATTERN = re.compile(r"`(Q[\w-]+)`\s+`\[(resolved|partial|deferred)\]`")


def _stage_root(*, workspace_root: Path, work_item: str, stage: str) -> Path:
    return workspace_root / "workitems" / work_item / "stages" / stage


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


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

    question_ids: dict[str, int] = {}
    answer_ids: dict[str, int] = {}

    if questions_text is not None:
        question_ids, question_findings = _collect_question_ids(questions_text)
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

    return tuple(findings)

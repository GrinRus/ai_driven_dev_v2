from __future__ import annotations

import re
from pathlib import Path

from aidd.core.implementation_eligibility import implementation_finalization_blocker
from aidd.core.interview import (
    AnswerResolution,
    InterviewMarkdownParseError,
    QuestionPolicy,
    parse_answer_entries,
    parse_question_entries,
)
from aidd.core.run_lookup import latest_run_id
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT, load_stage_manifest
from aidd.core.task_plan import TaskCard, TaskPlanParseError, parse_task_plan
from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic_rules.common import (
    IMPLEMENT_FILE_ENTRY_PATTERN,
    REVIEW_FINDING_ID_PATTERN,
    extract_qa_release_recommendation,
    extract_qa_verdict,
    extract_review_finding_blocks,
    extract_risk_blocks,
    is_empty_risk_entry,
    is_risk_metadata_entry,
)

ANSWER_WITHOUT_QUESTION_CODE = "CROSS-ANSWER-WITHOUT-QUESTION"
DUPLICATE_QUESTION_ID_CODE = "CROSS-DUPLICATE-QUESTION-ID"
DUPLICATE_ANSWER_ID_CODE = "CROSS-DUPLICATE-ANSWER-ID"
REPAIR_MENTION_WITHOUT_BRIEF_CODE = "CROSS-REPAIR-MENTION-WITHOUT-BRIEF"
REPAIR_BRIEF_NOT_REFERENCED_CODE = "CROSS-REPAIR-BRIEF-NOT-REFERENCED"
BLOCKING_UNANSWERED_CODE = "CROSS-BLOCKING-UNANSWERED"
REPAIR_BUDGET_EXHAUSTED_CODE = "CROSS-REPAIR-BUDGET-EXHAUSTED"
PROJECT_SET_EVIDENCE_MISSING_CODE = "CROSS-PROJECT-SET-EVIDENCE-MISSING"
TASKLIST_PLAN_MILESTONE_CODE = "CROSS-TASKLIST-PLAN-MILESTONE"
TASKLIST_PLAN_DEPENDENCY_CODE = "CROSS-TASKLIST-PLAN-DEPENDENCY"
TASKLIST_PLAN_VERIFICATION_CODE = "CROSS-TASKLIST-PLAN-VERIFICATION"
REVIEW_IMPLEMENT_FINDING_CODE = "CROSS-REVIEW-IMPLEMENT-FINDING"
REVIEW_IMPLEMENT_EVIDENCE_CODE = "CROSS-REVIEW-IMPLEMENT-EVIDENCE"
REVIEW_IMPLEMENT_PATH_CODE = "CROSS-REVIEW-IMPLEMENT-PATH"
QA_REVIEW_RISK_CODE = "CROSS-QA-REVIEW-RISK"
QA_UPSTREAM_EVIDENCE_CODE = "CROSS-QA-UPSTREAM-EVIDENCE"
QA_UPSTREAM_VERDICT_CODE = "CROSS-QA-UPSTREAM-VERDICT"
IMPLEMENTATION_FINALIZATION_CODE = "CROSS-IMPLEMENTATION-FINALIZATION"
MALFORMED_INTERVIEW_DOCUMENT_CODE = "INTERVIEW-MALFORMED-DOCUMENT"

_REPAIR_BUDGET_EXHAUSTED_TOKEN = "repair-budget-exhausted"
_STAGE_STATUS_PATTERN = re.compile(r"`?(succeeded|failed|blocked|needs-input)`?", re.IGNORECASE)
_PROJECT_SET_ROW_PATTERN = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|")
_MILESTONE_ID_PATTERN = re.compile(r"\b(M[1-9]\d*)\b", re.IGNORECASE)
_COMMAND_PREFIXES = (
    "uv ",
    "pytest ",
    "python ",
    "ruff ",
    "mypy ",
    "git ",
    "npm ",
    "pnpm ",
    "yarn ",
    "cargo ",
    "go test",
)
_EVIDENCE_ID_PATTERN = re.compile(r"\bEV-\d+\b", re.IGNORECASE)
_BACKTICKED_REFERENCE_PATTERN = re.compile(r"`([^`]+)`")
_ARTIFACT_SUFFIXES = frozenset({".md", ".json", ".jsonl", ".log", ".txt"})
_REVIEW_ACCEPTED_RISK_PATTERN = re.compile(r"\bAR-[1-9]\d*\b", re.IGNORECASE)
_QA_EVIDENCE_ENTRY_PATTERN = re.compile(r"^\s*-\s+", re.MULTILINE)


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


def _heading_line_number(markdown_text: str, heading: str) -> int | None:
    target = heading.strip().lower()
    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
        if match is None:
            continue
        if match.group(2).strip().lower() == target:
            return line_number
    return None


def _extract_stage_status(stage_result_text: str) -> tuple[str | None, int | None]:
    for line_number, line in _extract_section_lines(stage_result_text, heading="Status"):
        match = _STAGE_STATUS_PATTERN.search(line)
        if match is None:
            continue
        return match.group(1).lower(), line_number
    return None, None


def _interview_parse_finding(
    error: InterviewMarkdownParseError,
) -> ValidationFinding:
    if error.kind == "duplicate-id" and error.entry_id is not None:
        is_question = error.document_name == "questions.md"
        return ValidationFinding(
            code=DUPLICATE_QUESTION_ID_CODE if is_question else DUPLICATE_ANSWER_ID_CODE,
            message=(
                f"Duplicate {'question' if is_question else 'answer'} id "
                f"`{error.entry_id}` in {error.document_name}."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=error.document_name,
                line_number=error.line_number,
            ),
        )
    return ValidationFinding(
        code=MALFORMED_INTERVIEW_DOCUMENT_CODE,
        message=f"Malformed interview document `{error.document_name}`: {error}",
        severity="high",
        location=ValidationIssueLocation(
            workspace_relative_path=error.document_name,
            line_number=error.line_number,
        ),
    )


def _question_state(
    questions_text: str,
) -> tuple[dict[str, int], dict[str, int], tuple[ValidationFinding, ...], bool]:
    try:
        entries = parse_question_entries(questions_text)
        parse_usable = True
        parse_findings: tuple[ValidationFinding, ...] = ()
    except InterviewMarkdownParseError as error:
        entries = error.parsed_questions
        parse_usable = error.kind == "duplicate-id" or bool(entries)
        parse_findings = (_interview_parse_finding(error),)
    question_ids = {entry.value.question_id: entry.line_number for entry in entries}
    blocking_ids = {
        entry.value.question_id: entry.line_number
        for entry in entries
        if entry.value.policy is QuestionPolicy.BLOCKING
    }
    return question_ids, blocking_ids, parse_findings, parse_usable


def _answer_state(
    answers_text: str,
) -> tuple[dict[str, int], set[str], tuple[ValidationFinding, ...], bool]:
    try:
        entries = parse_answer_entries(answers_text)
        parse_usable = True
        parse_findings: tuple[ValidationFinding, ...] = ()
    except InterviewMarkdownParseError as error:
        entries = error.parsed_answers
        parse_usable = error.kind == "duplicate-id" or bool(entries)
        parse_findings = (_interview_parse_finding(error),)
    answer_ids = {entry.value.question_id: entry.line_number for entry in entries}
    resolved_ids = {
        entry.value.question_id
        for entry in entries
        if entry.value.resolution is AnswerResolution.RESOLVED
    }
    return answer_ids, resolved_ids, parse_findings, parse_usable


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def _extract_project_set_entries(project_set_text: str) -> tuple[tuple[str, str], ...]:
    entries: list[tuple[str, str]] = []
    for line in project_set_text.splitlines():
        match = _PROJECT_SET_ROW_PATTERN.match(line.strip())
        if match is None:
            continue
        entries.append((match.group(1), match.group(2)))
    return tuple(entries)


def _validate_project_set_stage_result_evidence(
    *,
    workspace_root: Path,
    project_set_path: Path,
    project_set_text: str,
    stage_result_path: Path,
    stage_result_text: str,
) -> tuple[ValidationFinding, ...]:
    findings: list[ValidationFinding] = []
    project_set_relative_path = _workspace_relative(project_set_path, workspace_root)
    stage_result_relative_path = _workspace_relative(stage_result_path, workspace_root)
    evidence_line = _heading_line_number(stage_result_text, "Project-set evidence")

    if evidence_line is None:
        findings.append(
            ValidationFinding(
                code=PROJECT_SET_EVIDENCE_MISSING_CODE,
                message=(
                    "stage-result.md must include `Project-set evidence` when "
                    f"`{project_set_relative_path}` exists."
                ),
                severity="high",
                location=ValidationIssueLocation(
                    workspace_relative_path=stage_result_relative_path,
                ),
            )
        )

    if f"`{project_set_relative_path}`" not in stage_result_text:
        findings.append(
            ValidationFinding(
                code=PROJECT_SET_EVIDENCE_MISSING_CODE,
                message=(
                    "Project-set evidence must reference the project-set context path "
                    f"`{project_set_relative_path}`."
                ),
                severity="high",
                location=ValidationIssueLocation(
                    workspace_relative_path=stage_result_relative_path,
                    line_number=evidence_line,
                ),
            )
        )

    for project_id, project_root in _extract_project_set_entries(project_set_text):
        missing_parts: list[str] = []
        if f"`{project_id}`" not in stage_result_text:
            missing_parts.append(f"project id `{project_id}`")
        if f"`{project_root}`" not in stage_result_text:
            missing_parts.append(f"project root `{project_root}`")
        if not missing_parts:
            continue
        findings.append(
            ValidationFinding(
                code=PROJECT_SET_EVIDENCE_MISSING_CODE,
                message=(
                    "Project-set evidence must cite declared "
                    + " and ".join(missing_parts)
                    + "."
                ),
                severity="high",
                location=ValidationIssueLocation(
                    workspace_relative_path=stage_result_relative_path,
                    line_number=evidence_line,
                ),
            )
        )

    return tuple(findings)


def _section_text(markdown: str, heading: str) -> str:
    return "\n".join(line for _, line in _extract_section_lines(markdown, heading))


def _level_two_section_text(markdown: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        markdown,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group("body").strip() if match is not None else ""


def _ordered_plan_milestones(plan_text: str) -> tuple[str, ...]:
    milestones: list[str] = []
    for _, line in _extract_section_lines(plan_text, "Milestones"):
        match = re.match(r"^\s*[-*+]\s+`?(M[1-9]\d*)`?\s*:", line, re.IGNORECASE)
        if match is not None:
            milestones.append(match.group(1).upper())
    return tuple(dict.fromkeys(milestones))


def _task_milestones(task: TaskCard) -> tuple[str, ...]:
    authored_text = "\n".join(
        (
            task.outcome,
            task.context or "",
            *(criterion.text for criterion in task.acceptance_criteria),
            task.verification,
        )
    )
    return tuple(
        dict.fromkeys(
            match.group(1).upper()
            for match in _MILESTONE_ID_PATTERN.finditer(authored_text)
        )
    )


def _plan_milestone_dependencies(plan_text: str) -> tuple[tuple[str, str], ...]:
    edges: list[tuple[str, str]] = []
    for _, line in _extract_section_lines(plan_text, "Dependencies"):
        if not re.search(r"\b(depends? on|after|requires?)\b", line, re.IGNORECASE):
            continue
        ids = [match.group(1).upper() for match in _MILESTONE_ID_PATTERN.finditer(line)]
        if len(ids) < 2:
            continue
        edges.extend((ids[0], dependency) for dependency in ids[1:])
    return tuple(dict.fromkeys(edges))


def _milestone_verification_commands(plan_text: str) -> dict[str, tuple[str, ...]]:
    commands: dict[str, list[str]] = {}
    for _, line in _extract_section_lines(plan_text, "Verification notes"):
        milestone_match = _MILESTONE_ID_PATTERN.search(line)
        if milestone_match is None:
            continue
        milestone = milestone_match.group(1).upper()
        for value in re.findall(r"`([^`]+)`", line):
            normalized = value.strip()
            if normalized.casefold().startswith(_COMMAND_PREFIXES):
                commands.setdefault(milestone, []).append(normalized)
    return {key: tuple(dict.fromkeys(values)) for key, values in commands.items()}


def _task_has_ancestor_milestone(
    *,
    task_id: str,
    milestone: str,
    dependencies: dict[str, tuple[str, ...]],
    task_milestones: dict[str, tuple[str, ...]],
) -> bool:
    pending = list(dependencies.get(task_id, ()))
    visited: set[str] = set()
    while pending:
        dependency = pending.pop()
        if dependency in visited:
            continue
        visited.add(dependency)
        if milestone in task_milestones.get(dependency, ()):
            return True
        pending.extend(dependencies.get(dependency, ()))
    return False


def _validate_tasklist_against_plan(
    *,
    workspace_root: Path,
    tasklist_path: Path,
    tasklist_text: str,
    plan_text: str,
) -> tuple[ValidationFinding, ...]:
    try:
        task_plan = parse_task_plan(tasklist_text)
    except TaskPlanParseError:
        return ()

    milestones = _ordered_plan_milestones(plan_text)
    if not milestones:
        return ()
    known = set(milestones)
    positions = {milestone: index for index, milestone in enumerate(milestones)}
    mappings = {task.id: _task_milestones(task) for task in task_plan.tasks}
    tasklist_relative = _workspace_relative(tasklist_path, workspace_root)
    findings: list[ValidationFinding] = []

    for task in task_plan.tasks:
        task_line = next(
            (
                number
                for number, line in enumerate(tasklist_text.splitlines(), start=1)
                if re.match(rf"^###\s+{re.escape(task.id)}\b", line.strip())
            ),
            None,
        )
        mapped = mappings[task.id]
        unknown = tuple(item for item in mapped if item not in known)
        if not mapped or unknown:
            detail = "no plan milestone" if not mapped else "unknown " + ", ".join(unknown)
            findings.append(
                ValidationFinding(
                    code=TASKLIST_PLAN_MILESTONE_CODE,
                    message=f"Task `{task.id}` maps to {detail}; cite an existing milestone id.",
                    severity="high",
                    location=ValidationIssueLocation(tasklist_relative, task_line),
                )
            )

    covered = {
        milestone
        for mapped in mappings.values()
        for milestone in mapped
        if milestone in known
    }
    for milestone in milestones:
        if milestone not in covered:
            findings.append(
                ValidationFinding(
                    code=TASKLIST_PLAN_MILESTONE_CODE,
                    message=f"Plan milestone `{milestone}` is not covered by any task card.",
                    severity="high",
                    location=ValidationIssueLocation(tasklist_relative),
                )
            )

    dependencies = {task.id: task.dependencies for task in task_plan.tasks}
    for task in task_plan.tasks:
        current_positions = [positions[item] for item in mappings[task.id] if item in positions]
        for dependency_id in task.dependencies:
            dependency_positions = [
                positions[item] for item in mappings.get(dependency_id, ()) if item in positions
            ]
            inverted = (
                current_positions
                and dependency_positions
                and max(dependency_positions) > min(current_positions)
            )
            if inverted:
                findings.append(
                    ValidationFinding(
                        code=TASKLIST_PLAN_DEPENDENCY_CODE,
                        message=(
                            f"Task `{task.id}` depends on `{dependency_id}`, which maps to a later "
                            "plan milestone."
                        ),
                        severity="high",
                        location=ValidationIssueLocation(tasklist_relative),
                    )
                )

    for target, prerequisite in _plan_milestone_dependencies(plan_text):
        if target not in known or prerequisite not in known:
            continue
        for task in task_plan.tasks:
            if target not in mappings[task.id]:
                continue
            if prerequisite in mappings[task.id] or _task_has_ancestor_milestone(
                task_id=task.id,
                milestone=prerequisite,
                dependencies=dependencies,
                task_milestones=mappings,
            ):
                continue
            findings.append(
                ValidationFinding(
                    code=TASKLIST_PLAN_DEPENDENCY_CODE,
                    message=(
                        f"Task `{task.id}` covers `{target}` but its dependency chain does not "
                        f"preserve plan prerequisite `{prerequisite}`."
                    ),
                    severity="high",
                    location=ValidationIssueLocation(tasklist_relative),
                )
            )

    for milestone, commands in _milestone_verification_commands(plan_text).items():
        mapped_verification = "\n".join(
            task.verification for task in task_plan.tasks if milestone in mappings[task.id]
        )
        for command in commands:
            if command in mapped_verification:
                continue
            findings.append(
                ValidationFinding(
                    code=TASKLIST_PLAN_VERIFICATION_CODE,
                    message=(
                        f"Tasks mapped to `{milestone}` must preserve authored verification "
                        f"command `{command}` exactly."
                    ),
                    severity="high",
                    location=ValidationIssueLocation(tasklist_relative),
                )
            )
    return tuple(findings)


def _review_implementation_findings(
    *,
    workspace_root: Path,
    review_path: Path,
    review_text: str,
    implementation_output_root: Path,
    implementation_text: str,
) -> tuple[ValidationFinding, ...]:
    review_relative = _workspace_relative(review_path, workspace_root)
    findings_section = _level_two_section_text(review_text, "Findings")
    finding_blocks = extract_review_finding_blocks(findings_section)
    declared: dict[str, int] = {}
    findings: list[ValidationFinding] = []
    for block in finding_blocks:
        match = REVIEW_FINDING_ID_PATTERN.search(block)
        if match is None:
            continue
        finding_id = match.group(0).strip("`").upper()
        declared[finding_id] = declared.get(finding_id, 0) + 1
    for finding_id, count in declared.items():
        if count == 1:
            continue
        findings.append(
            ValidationFinding(
                code=REVIEW_IMPLEMENT_FINDING_CODE,
                message=f"Review finding `{finding_id}` must be declared exactly once.",
                severity="high",
                location=ValidationIssueLocation(review_relative),
            )
        )

    review_without_findings = re.sub(
        r"^##\s+Findings\s*$.*?(?=^##\s+|\Z)",
        "",
        review_text,
        flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    for match in REVIEW_FINDING_ID_PATTERN.finditer(review_without_findings):
        finding_id = match.group(0).strip("`").upper()
        if declared.get(finding_id) == 1:
            continue
        findings.append(
            ValidationFinding(
                code=REVIEW_IMPLEMENT_FINDING_CODE,
                message=f"Review references undeclared finding `{finding_id}`.",
                severity="high",
                location=ValidationIssueLocation(review_relative),
            )
        )

    touched_paths = {
        match.group(0).strip("`").strip().strip("/")
        for match in IMPLEMENT_FILE_ENTRY_PATTERN.finditer(
            _level_two_section_text(implementation_text, "Touched files")
        )
    }
    available_artifacts = {
        path.name for path in implementation_output_root.iterdir() if path.is_file()
    }
    available_evidence_ids = {
        match.group(0).upper()
        for match in _EVIDENCE_ID_PATTERN.finditer(implementation_text)
    }

    for block in finding_blocks:
        evidence_lines = "\n".join(
            line for line in block.splitlines() if re.search(r"\bevidence\s*:", line, re.I)
        )
        for evidence_match in _EVIDENCE_ID_PATTERN.finditer(evidence_lines):
            evidence_id = evidence_match.group(0).upper()
            if evidence_id in available_evidence_ids:
                continue
            findings.append(
                ValidationFinding(
                    code=REVIEW_IMPLEMENT_EVIDENCE_CODE,
                    message=f"Review references unknown implementation evidence `{evidence_id}`.",
                    severity="high",
                    location=ValidationIssueLocation(review_relative),
                )
            )
        for value in _BACKTICKED_REFERENCE_PATTERN.findall(evidence_lines):
            reference = value.strip().removeprefix("./").rstrip("/")
            if not reference:
                continue
            suffix = Path(reference).suffix.lower()
            if "/" not in reference and suffix in _ARTIFACT_SUFFIXES:
                if reference not in available_artifacts:
                    findings.append(
                        ValidationFinding(
                            code=REVIEW_IMPLEMENT_EVIDENCE_CODE,
                            message=(
                                "Review references missing implementation artifact "
                                f"`{reference}`."
                            ),
                            severity="high",
                            location=ValidationIssueLocation(review_relative),
                        )
                    )
                continue
            if "/" not in reference and not suffix:
                continue
            if reference not in touched_paths:
                findings.append(
                    ValidationFinding(
                        code=REVIEW_IMPLEMENT_PATH_CODE,
                        message=(
                            f"Review references changed path `{reference}` not declared "
                            "by implementation."
                        ),
                        severity="high",
                        location=ValidationIssueLocation(review_relative),
                    )
                )
    return tuple(findings)


def _qa_upstream_findings(
    *,
    workspace_root: Path,
    qa_path: Path,
    qa_text: str,
    review_path: Path,
    review_text: str,
    implementation_output_root: Path,
    implementation_text: str,
) -> tuple[ValidationFinding, ...]:
    qa_relative = _workspace_relative(qa_path, workspace_root)
    available_ids = {
        match.group(0).strip("`").upper()
        for pattern, text in (
            (REVIEW_FINDING_ID_PATTERN, review_text),
            (_REVIEW_ACCEPTED_RISK_PATTERN, review_text),
            (_EVIDENCE_ID_PATTERN, review_text),
            (_EVIDENCE_ID_PATTERN, implementation_text),
        )
        for match in pattern.finditer(text)
    }
    upstream_roots = (review_path.parent, implementation_output_root)
    available_paths = {
        _workspace_relative(path, workspace_root)
        for root in upstream_roots
        if root.is_dir()
        for path in root.iterdir()
        if path.is_file()
    }

    def _resolved_reference(text: str) -> bool:
        if any(
            match.group(0).upper() in available_ids
            for match in _EVIDENCE_ID_PATTERN.finditer(text)
        ):
            return True
        if any(
            match.group(0).strip("`").upper() in available_ids
            for pattern in (REVIEW_FINDING_ID_PATTERN, _REVIEW_ACCEPTED_RISK_PATTERN)
            for match in pattern.finditer(text)
        ):
            return True
        return any(
            value.strip().removeprefix("./").rstrip("/") in available_paths
            for value in _BACKTICKED_REFERENCE_PATTERN.findall(text)
        )

    findings: list[ValidationFinding] = []
    risk_section = _level_two_section_text(qa_text, "Residual risks") or _level_two_section_text(
        qa_text, "Known issues"
    )
    risk_entries = tuple(
        item
        for item in extract_risk_blocks(risk_section)
        if not is_empty_risk_entry(item) and not is_risk_metadata_entry(item)
    )
    for risk in risk_entries:
        if _resolved_reference(risk):
            continue
        findings.append(
            ValidationFinding(
                code=QA_REVIEW_RISK_CODE,
                message=(
                    "Each QA residual risk must cite exact upstream review or "
                    "implementation evidence."
                ),
                severity="high",
                location=ValidationIssueLocation(qa_relative),
            )
        )

    evidence_sections = "\n".join(
        _level_two_section_text(qa_text, heading)
        for heading in ("Evidence references", "Evidence", "Verification summary")
    )
    for entry in re.split(r"(?=^\s*-\s+)", evidence_sections, flags=re.MULTILINE):
        if _QA_EVIDENCE_ENTRY_PATTERN.match(entry) is None:
            continue
        if _resolved_reference(entry):
            continue
        findings.append(
            ValidationFinding(
                code=QA_UPSTREAM_EVIDENCE_CODE,
                message=(
                    "QA evidence entry does not resolve to exact upstream evidence or "
                    "an artifact path."
                ),
                severity="high",
                location=ValidationIssueLocation(qa_relative),
            )
        )

    review_status_match = re.search(
        r"Review status\s*:\s*`?(approved-with-conditions|approved|rejected)`?",
        review_text,
        re.IGNORECASE,
    )
    review_rejected = (
        review_status_match is not None
        and review_status_match.group(1).lower() == "rejected"
    )
    unresolved_must_fix = any(
        "must-fix" in block.casefold()
        for block in extract_review_finding_blocks(
            _level_two_section_text(review_text, "Findings")
        )
    )
    verdict = extract_qa_verdict(qa_text, prefer_labeled=True)
    recommendation = extract_qa_release_recommendation(qa_text)
    if (review_rejected or unresolved_must_fix) and (
        verdict != "not-ready" or recommendation != "hold"
    ):
        findings.append(
            ValidationFinding(
                code=QA_UPSTREAM_VERDICT_CODE,
                message=(
                    "Rejected review or unresolved must-fix evidence requires "
                    "`QA verdict: not-ready` and release recommendation `hold`."
                ),
                severity="critical",
                location=ValidationIssueLocation(qa_relative),
            )
        )
    return tuple(findings)


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
    project_set_path = workspace_root / "workitems" / work_item / "context" / "project-set.md"
    tasklist_path = stage_root / "tasklist.md"
    plan_path = workspace_root / "workitems" / work_item / "stages" / "plan" / "output" / "plan.md"
    review_path = stage_root / "review-report.md"
    qa_path = stage_root / "qa-report.md"
    upstream_review_path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "review"
        / "output"
        / "review-report.md"
    )
    implementation_output_root = (
        workspace_root / "workitems" / work_item / "stages" / "implement" / "output"
    )
    implementation_report_path = implementation_output_root / "implementation-report.md"

    findings: list[ValidationFinding] = []

    questions_text = _read_optional(questions_path)
    answers_text = _read_optional(answers_path)
    stage_result_text = _read_optional(stage_result_path)
    repair_brief_text = _read_optional(repair_brief_path)
    project_set_text = _read_optional(project_set_path)
    tasklist_text = _read_optional(tasklist_path)
    plan_text = _read_optional(plan_path)
    review_text = _read_optional(review_path)
    qa_text = _read_optional(qa_path)
    upstream_review_text = _read_optional(upstream_review_path)
    implementation_text = _read_optional(implementation_report_path)

    question_ids: dict[str, int] = {}
    answer_ids: dict[str, int] = {}
    resolved_answer_ids: set[str] = set()
    blocking_question_ids: dict[str, int] = {}
    questions_usable = True
    answers_usable = True
    stage_status, stage_status_line = (
        _extract_stage_status(stage_result_text) if stage_result_text is not None else (None, None)
    )

    if questions_text is not None:
        (
            question_ids,
            blocking_question_ids,
            question_findings,
            questions_usable,
        ) = _question_state(questions_text)
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
        answer_ids, resolved_answer_ids, answer_findings, answers_usable = _answer_state(
            answers_text
        )
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

        if questions_usable and answers_usable:
            for question_id, line_number in answer_ids.items():
                if question_id in question_ids:
                    continue
                findings.append(
                    ValidationFinding(
                        code=ANSWER_WITHOUT_QUESTION_CODE,
                        message=(
                            f"Answer references `{question_id}` but no matching question exists "
                            "in questions.md."
                        ),
                        severity="high",
                        location=ValidationIssueLocation(
                            workspace_relative_path=_workspace_relative(
                                answers_path, workspace_root
                            ),
                            line_number=line_number,
                        ),
                    )
                )

    if questions_usable and answers_usable:
        for question_id, line_number in blocking_question_ids.items():
            if question_id in resolved_answer_ids:
                continue
            message = (
                f"`{question_id}` is marked `[blocking]` and has no matching `[resolved]` answer "
                "in `answers.md`."
            )
            if stage_status == "succeeded":
                message += (
                    " Stage status must not be `succeeded` while blocking questions remain."
                )
            findings.append(
                ValidationFinding(
                    code=BLOCKING_UNANSWERED_CODE,
                    message=message,
                    severity="critical",
                    location=ValidationIssueLocation(
                        workspace_relative_path=_workspace_relative(
                            questions_path, workspace_root
                        ),
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

    if project_set_text is not None and stage_result_text is not None:
        findings.extend(
            _validate_project_set_stage_result_evidence(
                workspace_root=workspace_root,
                project_set_path=project_set_path,
                project_set_text=project_set_text,
                stage_result_path=stage_result_path,
                stage_result_text=stage_result_text,
            )
        )

    if stage == "tasklist" and tasklist_text is not None and plan_text is not None:
        findings.extend(
            _validate_tasklist_against_plan(
                workspace_root=workspace_root,
                tasklist_path=tasklist_path,
                tasklist_text=tasklist_text,
                plan_text=plan_text,
            )
        )

    if stage == "review" and review_text is not None and implementation_text is not None:
        findings.extend(
            _review_implementation_findings(
                workspace_root=workspace_root,
                review_path=review_path,
                review_text=review_text,
                implementation_output_root=implementation_output_root,
                implementation_text=implementation_text,
            )
        )

    if (
        stage == "qa"
        and qa_text is not None
        and upstream_review_text is not None
        and implementation_text is not None
    ):
        findings.extend(
            _qa_upstream_findings(
                workspace_root=workspace_root,
                qa_path=qa_path,
                qa_text=qa_text,
                review_path=upstream_review_path,
                review_text=upstream_review_text,
                implementation_output_root=implementation_output_root,
                implementation_text=implementation_text,
            )
        )

    published_tasklist = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    if stage in {"review", "qa"} and published_tasklist.exists():
        run_id = latest_run_id(workspace_root=workspace_root, work_item=work_item)
        blocker = (
            "Implementation run is missing."
            if run_id is None
            else implementation_finalization_blocker(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
            )
        )
        if blocker is not None:
            findings.append(
                ValidationFinding(
                    code=IMPLEMENTATION_FINALIZATION_CODE,
                    message=blocker,
                    severity="critical",
                    location=ValidationIssueLocation(
                        _workspace_relative(stage_root, workspace_root)
                    ),
                )
            )

    return tuple(findings)

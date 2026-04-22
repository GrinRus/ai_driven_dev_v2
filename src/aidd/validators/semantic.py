from __future__ import annotations

import re
from pathlib import Path

from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    load_stage_manifest,
    resolve_expected_output_documents,
)
from aidd.validators.document_loader import load_markdown_document
from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.structural import MarkdownHeading, extract_markdown_headings

INCOMPLETE_SECTION_CODE = "SEM-INCOMPLETE-SECTION"
UNSUPPORTED_CLAIM_CODE = "SEM-UNSUPPORTED-CLAIM"
PLACEHOLDER_CONTENT_CODE = "SEM-PLACEHOLDER-CONTENT"
MISSING_EVIDENCE_LINK_CODE = "SEM-MISSING-EVIDENCE-LINK"
MISSING_DIFF_EVIDENCE_CODE = "SEM-MISSING-DIFF-EVIDENCE"
UNVERIFIABLE_CHECK_CLAIM_CODE = "SEM-UNVERIFIABLE-CHECK-CLAIM"
INCOMPLETE_EXECUTION_SUMMARY_CODE = "SEM-INCOMPLETE-EXECUTION-SUMMARY"
UNSUPPORTED_VERDICT_CODE = "SEM-UNSUPPORTED-VERDICT"
MISSING_EVIDENCE_REF_CODE = "SEM-MISSING-EVIDENCE-REF"
RISK_UNDERREPORT_CODE = "SEM-RISK-UNDERREPORT"

_INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
_STAGE_HEADING_REQUIREMENT_PATTERN = re.compile(
    r"required heading coverage in\s+`([^`]+)`\s*\((.+)\)",
    flags=re.IGNORECASE,
)
_PLACEHOLDER_PATTERN = re.compile(r"\b(TBD|TODO|TBA|N/A)\b|\.{3}", flags=re.IGNORECASE)
_UNSUPPORTED_CLAIM_PATTERN = re.compile(
    r"\b(always|never|guarantee(?:d|s)?|proven|certain(?:ly)?)\b",
    flags=re.IGNORECASE,
)
_CITATION_ID_PATTERN = re.compile(r"\[(S\d+)\]")
_MILESTONE_ID_PATTERN = re.compile(r"\b(M\d+)\b", flags=re.IGNORECASE)
_RISK_MITIGATION_PATTERN = re.compile(
    r"\b(mitigation|mitigate|fallback|retry|reduce|avoid|monitor)\b",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_READINESS_PATTERN = re.compile(
    r"\b(ready-with-conditions|not-ready|ready)\b",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_DECISION_PATTERN = re.compile(
    r"\b(approved-with-conditions|rejected|approved)\b",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_SEVERITY_PATTERN = re.compile(
    r"\b(critical|high|medium|low)\b",
    flags=re.IGNORECASE,
)
_REVIEW_SPEC_RATIONALE_PATTERN = re.compile(
    r"\b(rationale|because)\b",
    flags=re.IGNORECASE,
)
_TASKLIST_TASK_ID_PATTERN = re.compile(
    r"\b([A-Z][A-Z0-9]{0,15}-\d+)\b",
    flags=re.IGNORECASE,
)
_IMPLEMENT_FILE_ENTRY_PATTERN = re.compile(r"`[^`]*?/[^`]+`")
_IMPLEMENT_COMMAND_PATTERN = re.compile(
    r"\b(uv run|pytest|ruff|mypy|python -m|npm|pnpm|yarn|go test|cargo test|make)\b",
    flags=re.IGNORECASE,
)
_IMPLEMENT_RESULT_PATTERN = re.compile(
    r"(->\s*(pass|fail|ok|error)|\b(pass(?:ed)?|fail(?:ed)?|error|exit code)\b)",
    flags=re.IGNORECASE,
)
_IMPLEMENT_COMPLETION_CLAIM_PATTERN = re.compile(
    r"\b(completed|fully|done|implemented|finished)\b",
    flags=re.IGNORECASE,
)
_IMPLEMENT_NOOP_JUSTIFICATION_PATTERN = re.compile(
    r"\b(no-op|already (satisfied|implemented)|blocked|external constraint|out of scope)\b",
    flags=re.IGNORECASE,
)
_REVIEW_FINDING_ID_PATTERN = re.compile(r"\bRV-\d+\b", flags=re.IGNORECASE)
_REVIEW_DISPOSITION_PATTERN = re.compile(
    r"\b(must-fix|follow-up|accepted-risk|invalid)\b",
    flags=re.IGNORECASE,
)
_REVIEW_ACCEPTANCE_CRITERIA_PATTERN = re.compile(r"\bAC-\d+\b", flags=re.IGNORECASE)
_QA_VERDICT_PATTERN = re.compile(
    r"\b(ready-with-risks|not-ready|ready)\b",
    flags=re.IGNORECASE,
)
_QA_RELEASE_RECOMMENDATION_PATTERN = re.compile(
    r"\b(proceed-with-conditions|hold|proceed)\b",
    flags=re.IGNORECASE,
)
_QA_EVIDENCE_ID_PATTERN = re.compile(r"\bEV-\d+\b", flags=re.IGNORECASE)
_QA_OWNER_PATTERN = re.compile(r"\bowner\b", flags=re.IGNORECASE)


def _extract_section_lines(markdown_text: str, heading: str) -> list[str]:
    target_heading = f"## {heading}".lower()
    in_section = False
    section_lines: list[str] = []

    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped.lower() == target_heading
            continue
        if in_section:
            section_lines.append(raw_line)

    return section_lines


def _extract_required_sections_from_document_contract(contract_text: str) -> tuple[str, ...]:
    sections: list[str] = []
    for line in _extract_section_lines(contract_text, heading="Required sections"):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        sections.extend(token.strip() for token in _INLINE_CODE_PATTERN.findall(stripped))
    return tuple(dict.fromkeys(section for section in sections if section))


def _extract_stage_required_heading_map(stage_contract_text: str) -> dict[str, tuple[str, ...]]:
    requirements: dict[str, tuple[str, ...]] = {}
    for line in _extract_section_lines(stage_contract_text, heading="Validation focus"):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue

        match = _STAGE_HEADING_REQUIREMENT_PATTERN.search(stripped)
        if match is None:
            continue

        document_name = match.group(1).strip()
        sections = tuple(
            token.strip() for token in _INLINE_CODE_PATTERN.findall(match.group(2)) if token.strip()
        )
        if sections:
            requirements[document_name] = sections

    return requirements


def _required_sections_for_document(
    *,
    stage: str,
    document_name: str,
    contracts_root: Path,
) -> tuple[str, ...]:
    sections: list[str] = []
    document_contract_path = contracts_root.parent / "documents" / document_name
    if document_contract_path.exists():
        sections.extend(
            _extract_required_sections_from_document_contract(
                document_contract_path.read_text(encoding="utf-8")
            )
        )

    stage_contract_path = contracts_root / f"{stage}.md"
    if stage_contract_path.exists():
        stage_requirements = _extract_stage_required_heading_map(
            stage_contract_path.read_text(encoding="utf-8")
        )
        sections.extend(stage_requirements.get(document_name, ()))

    return tuple(dict.fromkeys(section for section in sections if section))


def _normalized_heading(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def _section_content_for_heading(
    *,
    heading_index: int,
    headings: tuple[MarkdownHeading, ...],
    markdown_lines: list[str],
) -> str:
    # headings come from structural.extract_markdown_headings (MarkdownHeading instances).
    heading = headings[heading_index]
    start_index = heading.line_number
    end_index = len(markdown_lines)

    for next_heading in headings[heading_index + 1 :]:
        if next_heading.level <= heading.level:
            end_index = next_heading.line_number - 1
            break

    return "\n".join(markdown_lines[start_index:end_index]).strip()


def has_non_placeholder_text(text: str) -> bool:
    return _PLACEHOLDER_PATTERN.search(text) is None


def _has_bullet_items(section_content: str) -> bool:
    return any(line.strip().startswith("- ") for line in section_content.splitlines())


def _extract_bullet_items(section_content: str) -> tuple[str, ...]:
    return tuple(
        line.strip()[2:].strip()
        for line in section_content.splitlines()
        if line.strip().startswith("- ")
    )


def _extract_citation_ids(text: str) -> set[str]:
    return {match.group(1) for match in _CITATION_ID_PATTERN.finditer(text)}


def _extract_milestone_ids(text: str) -> set[str]:
    return {match.group(1).upper() for match in _MILESTONE_ID_PATTERN.finditer(text)}


def _extract_review_spec_readiness_state(text: str) -> str | None:
    match = _REVIEW_SPEC_READINESS_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def _extract_review_spec_decision(text: str) -> str | None:
    match = _REVIEW_SPEC_DECISION_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def _extract_qa_verdict(text: str) -> str | None:
    match = _QA_VERDICT_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def _extract_qa_release_recommendation(text: str) -> str | None:
    match = _QA_RELEASE_RECOMMENDATION_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def _extract_tasklist_task_ids(text: str) -> set[str]:
    return {match.group(1).upper() for match in _TASKLIST_TASK_ID_PATTERN.finditer(text)}


def _first_heading_match(
    *,
    headings_by_title: dict[str, list[tuple[int, MarkdownHeading]]],
    candidates: tuple[str, ...],
) -> tuple[int, MarkdownHeading] | None:
    for candidate in candidates:
        matches = headings_by_title.get(_normalized_heading(candidate), [])
        if matches:
            return matches[0]
    return None


def validate_semantic_outputs(
    *,
    stage: str,
    work_item: str,
    workspace_root: Path,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> tuple[ValidationFinding, ...]:
    load_stage_manifest(stage=stage, contracts_root=contracts_root)
    expected_outputs = resolve_expected_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    findings: list[ValidationFinding] = []
    for output_path in expected_outputs:
        if not output_path.exists():
            continue

        required_sections = _required_sections_for_document(
            stage=stage,
            document_name=output_path.name,
            contracts_root=contracts_root,
        )
        if not required_sections:
            continue

        loaded_document = load_markdown_document(path=output_path, workspace_root=workspace_root)
        headings = extract_markdown_headings(loaded_document.body)
        markdown_lines = loaded_document.body.splitlines()
        headings_by_title: dict[str, list[tuple[int, MarkdownHeading]]] = {}
        for index, heading in enumerate(headings):
            normalized_title = _normalized_heading(heading.title)
            headings_by_title.setdefault(normalized_title, []).append((index, heading))

        research_source_ids: set[str] = set()
        if stage == "research" and output_path.name == "research-notes.md":
            sources_matches = headings_by_title.get(_normalized_heading("Sources"), [])
            if sources_matches:
                sources_index, _ = sources_matches[0]
                sources_content = _section_content_for_heading(
                    heading_index=sources_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                research_source_ids = _extract_citation_ids(sources_content)

        plan_milestone_ids: set[str] = set()
        if stage == "plan" and output_path.name == "plan.md":
            milestone_matches = headings_by_title.get(_normalized_heading("Milestones"), [])
            if milestone_matches:
                milestone_index, _ = milestone_matches[0]
                milestones_content = _section_content_for_heading(
                    heading_index=milestone_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                plan_milestone_ids = _extract_milestone_ids(milestones_content)

        review_spec_readiness_state: str | None = None
        review_spec_decision: str | None = None
        review_spec_decision_location: ValidationIssueLocation | None = None
        if stage == "review-spec" and output_path.name == "review-spec-report.md":
            readiness_matches = headings_by_title.get(_normalized_heading("Readiness state"), [])
            if readiness_matches:
                readiness_index, _ = readiness_matches[0]
                readiness_content = _section_content_for_heading(
                    heading_index=readiness_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                review_spec_readiness_state = _extract_review_spec_readiness_state(
                    readiness_content
                )

            decision_matches = headings_by_title.get(_normalized_heading("Decision"), [])
            if decision_matches:
                decision_index, decision_heading = decision_matches[0]
                decision_content = _section_content_for_heading(
                    heading_index=decision_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                review_spec_decision = _extract_review_spec_decision(decision_content)
                review_spec_decision_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=decision_heading.line_number,
                )

        tasklist_task_ids: set[str] = set()
        if stage == "tasklist" and output_path.name == "tasklist.md":
            ordered_task_matches = headings_by_title.get(
                _normalized_heading("Ordered tasks"), []
            )
            if ordered_task_matches:
                ordered_tasks_index, _ = ordered_task_matches[0]
                ordered_tasks_content = _section_content_for_heading(
                    heading_index=ordered_tasks_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                tasklist_task_ids = _extract_tasklist_task_ids(ordered_tasks_content)

        if stage == "implement" and output_path.name == "implementation-report.md":
            selected_task_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Selected task",),
            )
            summary_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Change summary", "Summary"),
            )
            touched_files_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Touched files",),
            )
            verification_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Verification notes", "Verification"),
            )
            follow_up_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Follow-up notes", "Follow-up", "Risks"),
            )

            selected_task_content = ""
            selected_task_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if selected_task_match is not None:
                selected_task_index, selected_task_heading = selected_task_match
                selected_task_content = _section_content_for_heading(
                    heading_index=selected_task_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                selected_task_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=selected_task_heading.line_number,
                )

            summary_content = ""
            summary_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if summary_match is not None:
                summary_index, summary_heading = summary_match
                summary_content = _section_content_for_heading(
                    heading_index=summary_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                summary_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=summary_heading.line_number,
                )

            touched_files_content = ""
            touched_files_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if touched_files_match is not None:
                touched_files_index, touched_files_heading = touched_files_match
                touched_files_content = _section_content_for_heading(
                    heading_index=touched_files_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                touched_files_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=touched_files_heading.line_number,
                )

            verification_content = ""
            verification_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if verification_match is not None:
                verification_index, verification_heading = verification_match
                verification_content = _section_content_for_heading(
                    heading_index=verification_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                verification_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=verification_heading.line_number,
                )

            follow_up_content = ""
            follow_up_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if follow_up_match is not None:
                follow_up_index, follow_up_heading = follow_up_match
                follow_up_content = _section_content_for_heading(
                    heading_index=follow_up_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                follow_up_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=follow_up_heading.line_number,
                )

            if not _extract_tasklist_task_ids(selected_task_content):
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Selected task` must include a stable task id "
                            "(for example `TL-2`)."
                        ),
                        severity="medium",
                        location=selected_task_location,
                    )
                )

            compact_summary_content = re.sub(r"\s+", " ", summary_content).strip()
            if (
                compact_summary_content.lower() in {"none", "- none"}
                or len(compact_summary_content) < 30
            ):
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
                        message=(
                            "Section `Change summary` is too brief to explain task intent, "
                            "actual edits, and execution outcome."
                        ),
                        severity="medium",
                        location=summary_location,
                    )
                )

            touched_file_items = _extract_bullet_items(touched_files_content)
            if not touched_file_items:
                findings.append(
                    ValidationFinding(
                        code=MISSING_DIFF_EVIDENCE_CODE,
                        message=(
                            "Section `Touched files` must list concrete file entries "
                            "or explicit no-op justification."
                        ),
                        severity="high",
                        location=touched_files_location,
                    )
                )

            has_real_touched_file_entries = any(
                item.lower() != "none" for item in touched_file_items
            )
            if has_real_touched_file_entries:
                if any(
                    _IMPLEMENT_FILE_ENTRY_PATTERN.search(item) is None
                    for item in touched_file_items
                    if item.lower() != "none"
                ):
                    findings.append(
                        ValidationFinding(
                            code=MISSING_DIFF_EVIDENCE_CODE,
                            message=(
                                "Section `Touched files` entries must include file paths "
                                "in backticks."
                            ),
                            severity="high",
                            location=touched_files_location,
                        )
                    )

                if any(
                    " - " not in item and ":" not in item
                    for item in touched_file_items
                    if item.lower() != "none"
                ):
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Each `Touched files` entry must include short change intent "
                                "after the path."
                            ),
                            severity="medium",
                            location=touched_files_location,
                        )
                    )
            else:
                no_op_context = " ".join((summary_content, follow_up_content))
                if _IMPLEMENT_NOOP_JUSTIFICATION_PATTERN.search(no_op_context) is None:
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
                            message=(
                                "No-op output requires explicit evidence-backed justification "
                                "in summary or follow-up notes."
                            ),
                            severity="medium",
                            location=summary_location,
                        )
                    )

                compact_follow_up_content = re.sub(r"\s+", " ", follow_up_content).strip()
                if compact_follow_up_content.lower() in {"", "none", "- none"}:
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
                            message=(
                                "No-op output must include an actionable next step in "
                                "`Follow-up notes`."
                            ),
                            severity="medium",
                            location=follow_up_location,
                        )
                    )

                if _IMPLEMENT_COMPLETION_CLAIM_PATTERN.search(compact_summary_content):
                    findings.append(
                        ValidationFinding(
                            code=MISSING_DIFF_EVIDENCE_CODE,
                            message=(
                                "Change summary claims completed implementation but "
                                "touched-files list is empty."
                            ),
                            severity="high",
                            location=summary_location,
                        )
                    )

            verification_items = _extract_bullet_items(verification_content)
            if not verification_items:
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Verification notes` must list concrete checks and outcomes."
                        ),
                        severity="medium",
                        location=verification_location,
                    )
                )
            else:
                for verification_item in verification_items:
                    normalized_item = verification_item.lower()
                    if normalized_item in {"none", "not run"}:
                        continue

                    has_command_reference = (
                        _IMPLEMENT_COMMAND_PATTERN.search(verification_item) is not None
                    )
                    has_result_reference = (
                        _IMPLEMENT_RESULT_PATTERN.search(verification_item) is not None
                    )
                    if has_result_reference and not has_command_reference:
                        findings.append(
                            ValidationFinding(
                                code=UNVERIFIABLE_CHECK_CLAIM_CODE,
                                message=(
                                    "Verification note includes outcome claim without executable "
                                    "command evidence."
                                ),
                                severity="high",
                                location=verification_location,
                            )
                        )
                        continue

                    if has_command_reference and not has_result_reference:
                        findings.append(
                            ValidationFinding(
                                code=UNVERIFIABLE_CHECK_CLAIM_CODE,
                                message=(
                                    "Verification note must include observed command outcome "
                                    "(for example `-> pass` or exit code)."
                                ),
                                severity="medium",
                                location=verification_location,
                            )
                        )

        if stage == "review" and output_path.name == "review-report.md":
            findings_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Findings",),
            )
            approval_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Approval status", "Verdict"),
            )
            required_changes_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Required changes", "Required follow-up"),
            )

            findings_content = ""
            findings_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if findings_match is not None:
                findings_index, findings_heading = findings_match
                findings_content = _section_content_for_heading(
                    heading_index=findings_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                findings_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=findings_heading.line_number,
                )

            findings_items = _extract_bullet_items(findings_content)
            if not findings_items:
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Findings` must include bullet entries with stable ids, "
                            "severity, disposition, and rationale."
                        ),
                        severity="medium",
                        location=findings_location,
                    )
                )

            unresolved_must_fix_count = 0
            for finding_item in findings_items:
                if _REVIEW_FINDING_ID_PATTERN.search(finding_item) is None:
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Each finding must include a stable id "
                                "(for example `RV-1`)."
                            ),
                            severity="medium",
                            location=findings_location,
                        )
                    )

                if _REVIEW_SPEC_SEVERITY_PATTERN.search(finding_item) is None:
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Each finding must include explicit severity "
                                "(critical/high/medium/low)."
                            ),
                            severity="medium",
                            location=findings_location,
                        )
                    )

                if _REVIEW_DISPOSITION_PATTERN.search(finding_item) is None:
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Each finding must include explicit disposition "
                                "(`must-fix`, `follow-up`, `accepted-risk`, or `invalid`)."
                            ),
                            severity="medium",
                            location=findings_location,
                        )
                    )

                if _REVIEW_SPEC_RATIONALE_PATTERN.search(finding_item) is None:
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Each finding must include rationale "
                                "(for example `Rationale:` or `because ...`)."
                            ),
                            severity="medium",
                            location=findings_location,
                        )
                    )

                has_implementation_evidence = _IMPLEMENT_FILE_ENTRY_PATTERN.search(
                    finding_item
                ) is not None
                has_acceptance_reference = (
                    _REVIEW_ACCEPTANCE_CRITERIA_PATTERN.search(finding_item) is not None
                )
                if not has_implementation_evidence and not has_acceptance_reference:
                    findings.append(
                        ValidationFinding(
                            code=UNSUPPORTED_CLAIM_CODE,
                            message=(
                                "Finding is missing evidence reference to implementation output "
                                "or acceptance criteria."
                            ),
                            severity="high",
                            location=findings_location,
                        )
                    )

                if re.search(r"\bmust-fix\b", finding_item, flags=re.IGNORECASE):
                    unresolved_must_fix_count += 1

            approval_content = ""
            approval_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if approval_match is not None:
                approval_index, approval_heading = approval_match
                approval_content = _section_content_for_heading(
                    heading_index=approval_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                approval_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=approval_heading.line_number,
                )

            approval_status = _extract_review_spec_decision(approval_content)
            if approval_status is None:
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Approval status` must declare one explicit state: "
                            "`approved`, `approved-with-conditions`, or `rejected`."
                        ),
                        severity="medium",
                        location=approval_location,
                    )
                )
            elif approval_status == "approved" and unresolved_must_fix_count > 0:
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Approval status cannot be `approved` while unresolved "
                            "`must-fix` findings remain."
                        ),
                        severity="high",
                        location=approval_location,
                    )
                )

            required_changes_content = ""
            required_changes_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if required_changes_match is not None:
                required_changes_index, required_changes_heading = required_changes_match
                required_changes_content = _section_content_for_heading(
                    heading_index=required_changes_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                required_changes_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=required_changes_heading.line_number,
                )

            required_changes_items = _extract_bullet_items(required_changes_content)
            has_required_change_entries = any(
                item.lower() != "none" for item in required_changes_items
            )
            if (
                approval_status in {"approved-with-conditions", "rejected"}
                and not has_required_change_entries
            ):
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Non-approved outcomes must include concrete required-change entries."
                        ),
                        severity="medium",
                        location=required_changes_location,
                    )
                )

        if stage == "qa" and output_path.name == "qa-report.md":
            verdict_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Quality verdict", "Readiness"),
            )
            risks_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Residual risks", "Known issues"),
            )
            recommendation_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Release recommendation",),
            )
            evidence_match = _first_heading_match(
                headings_by_title=headings_by_title,
                candidates=("Evidence references", "Evidence"),
            )

            verdict_content = ""
            verdict_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if verdict_match is not None:
                verdict_index, verdict_heading = verdict_match
                verdict_content = _section_content_for_heading(
                    heading_index=verdict_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                verdict_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=verdict_heading.line_number,
                )

            risks_content = ""
            risks_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if risks_match is not None:
                risks_index, risks_heading = risks_match
                risks_content = _section_content_for_heading(
                    heading_index=risks_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                risks_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=risks_heading.line_number,
                )

            recommendation_content = ""
            recommendation_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if recommendation_match is not None:
                recommendation_index, recommendation_heading = recommendation_match
                recommendation_content = _section_content_for_heading(
                    heading_index=recommendation_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                recommendation_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=recommendation_heading.line_number,
                )

            evidence_content = ""
            evidence_location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=1,
            )
            if evidence_match is not None:
                evidence_index, evidence_heading = evidence_match
                evidence_content = _section_content_for_heading(
                    heading_index=evidence_index,
                    headings=headings,
                    markdown_lines=markdown_lines,
                )
                evidence_location = ValidationIssueLocation(
                    workspace_relative_path=_workspace_relative(output_path, workspace_root),
                    line_number=evidence_heading.line_number,
                )

            qa_verdict = _extract_qa_verdict(verdict_content)
            if qa_verdict is None:
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Quality verdict` must declare one explicit state: "
                            "`ready`, `ready-with-risks`, or `not-ready`."
                        ),
                        severity="medium",
                        location=verdict_location,
                    )
                )

            qa_recommendation = _extract_qa_release_recommendation(
                recommendation_content
            )
            if qa_recommendation is None:
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Section `Release recommendation` must declare one explicit state: "
                            "`proceed`, `proceed-with-conditions`, or `hold`."
                        ),
                        severity="medium",
                        location=recommendation_location,
                    )
                )

            risk_items = _extract_bullet_items(risks_content)
            has_residual_risk_entries = any(
                item.lower() != "none" for item in risk_items
            )
            if qa_verdict == "ready-with-risks" and not has_residual_risk_entries:
                findings.append(
                    ValidationFinding(
                        code=RISK_UNDERREPORT_CODE,
                        message=(
                            "Verdict `ready-with-risks` requires explicit residual risk entries "
                            "with mitigation/ownership notes."
                        ),
                        severity="high",
                        location=risks_location,
                    )
                )
            if (
                qa_recommendation == "proceed-with-conditions"
                and not has_residual_risk_entries
            ):
                findings.append(
                    ValidationFinding(
                        code=RISK_UNDERREPORT_CODE,
                        message=(
                            "Recommendation `proceed-with-conditions` requires explicit residual "
                            "risk entries."
                        ),
                        severity="high",
                        location=risks_location,
                    )
                )

            for risk_item in (item for item in risk_items if item.lower() != "none"):
                if _REVIEW_SPEC_SEVERITY_PATTERN.search(risk_item) is None:
                    findings.append(
                        ValidationFinding(
                            code=RISK_UNDERREPORT_CODE,
                            message=(
                                "Each residual risk item must include explicit severity "
                                "(critical/high/medium/low)."
                            ),
                            severity="medium",
                            location=risks_location,
                        )
                    )
                    break

                has_mitigation_note = (
                    _RISK_MITIGATION_PATTERN.search(risk_item) is not None
                    or _QA_OWNER_PATTERN.search(risk_item) is not None
                )
                if not has_mitigation_note:
                    findings.append(
                        ValidationFinding(
                            code=RISK_UNDERREPORT_CODE,
                            message=(
                                "Each residual risk item must include mitigation and/or "
                                "ownership note."
                            ),
                            severity="medium",
                            location=risks_location,
                        )
                    )
                    break

            evidence_items = _extract_bullet_items(evidence_content)
            has_evidence_entries = any(
                item.lower() not in {"none", "none recorded"}
                for item in evidence_items
            )
            if not has_evidence_entries:
                findings.append(
                    ValidationFinding(
                        code=MISSING_EVIDENCE_REF_CODE,
                        message=(
                            "Material QA claims and release recommendation must reference "
                            "verification artifacts or execution outputs."
                        ),
                        severity="high",
                        location=evidence_location,
                    )
                )
            else:
                for evidence_item in (
                    item
                    for item in evidence_items
                    if item.lower() not in {"none", "none recorded"}
                ):
                    has_artifact_path_reference = (
                        _IMPLEMENT_FILE_ENTRY_PATTERN.search(evidence_item) is not None
                    )
                    has_evidence_id = _QA_EVIDENCE_ID_PATTERN.search(evidence_item) is not None
                    if not has_artifact_path_reference and not has_evidence_id:
                        findings.append(
                            ValidationFinding(
                                code=MISSING_EVIDENCE_REF_CODE,
                                message=(
                                    "Evidence entries must include stable evidence id "
                                    "(for example `EV-1`) and/or artifact path in backticks."
                                ),
                                severity="medium",
                                location=evidence_location,
                            )
                        )
                        break

            if qa_verdict is not None and qa_recommendation is not None:
                if qa_verdict == "not-ready" and qa_recommendation != "hold":
                    findings.append(
                        ValidationFinding(
                            code=UNSUPPORTED_VERDICT_CODE,
                            message=(
                                "Verdict `not-ready` must align with release recommendation "
                                "`hold`."
                            ),
                            severity="high",
                            location=recommendation_location,
                        )
                    )

                if qa_verdict in {"ready", "ready-with-risks"} and qa_recommendation == "hold":
                    findings.append(
                        ValidationFinding(
                            code=UNSUPPORTED_VERDICT_CODE,
                            message=(
                                "Verdicts `ready` or `ready-with-risks` cannot pair with "
                                "release recommendation `hold`."
                            ),
                            severity="high",
                            location=recommendation_location,
                        )
                    )

                if (
                    qa_verdict in {"ready", "ready-with-risks"}
                    and not has_evidence_entries
                ):
                    findings.append(
                        ValidationFinding(
                            code=UNSUPPORTED_VERDICT_CODE,
                            message=(
                                "Ready/proceed-style outcomes are unsupported without concrete "
                                "verification evidence references."
                            ),
                            severity="high",
                            location=verdict_location,
                        )
                    )

        for section in required_sections:
            matches = headings_by_title.get(_normalized_heading(section), [])
            if not matches:
                continue

            heading_index, heading = matches[0]
            section_content = _section_content_for_heading(
                heading_index=heading_index,
                headings=headings,
                markdown_lines=markdown_lines,
            )
            location = ValidationIssueLocation(
                workspace_relative_path=_workspace_relative(output_path, workspace_root),
                line_number=heading.line_number,
            )

            if _PLACEHOLDER_PATTERN.search(section_content):
                findings.append(
                    ValidationFinding(
                        code=PLACEHOLDER_CONTENT_CODE,
                        message=(
                            "Placeholder content remains in required section "
                            f"`{section}`."
                        ),
                        severity="high",
                        location=location,
                    )
                )

            if stage == "idea" and output_path.name == "idea-brief.md":
                normalized_section = _normalized_heading(section)
                compact_content = re.sub(r"\s+", " ", section_content).strip()

                if normalized_section in {"problem statement", "desired outcome"}:
                    if compact_content.lower() in {"none", "- none"} or len(compact_content) < 20:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    f"Required section `{section}` is too brief to establish "
                                    "a reviewable semantic baseline."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )

                if normalized_section in {"problem statement", "desired outcome"}:
                    if _UNSUPPORTED_CLAIM_PATTERN.search(compact_content):
                        findings.append(
                            ValidationFinding(
                                code=UNSUPPORTED_CLAIM_CODE,
                                message=(
                                    f"Section `{section}` includes unsupported absolute claims "
                                    "without evidence grounding."
                                ),
                                severity="high",
                                location=location,
                            )
                        )

                if normalized_section in {"constraints", "open questions"}:
                    if not _has_bullet_items(section_content):
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    f"Required section `{section}` must use bullet items "
                                    "(or `- none`) so downstream stages can parse "
                                    "constraints and open questions deterministically."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )

            if stage == "research" and output_path.name == "research-notes.md":
                normalized_section = _normalized_heading(section)
                compact_content = re.sub(r"\s+", " ", section_content).strip()

                if normalized_section == "sources" and not research_source_ids:
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Required section `Sources` must declare citation ids "
                                "(for example `[S1]`) for downstream evidence linking."
                            ),
                            severity="medium",
                            location=location,
                        )
                    )

                if normalized_section in {"findings", "evidence trace"}:
                    if compact_content.lower() in {"none", "- none"}:
                        continue
                    referenced_ids = _extract_citation_ids(section_content)
                    if not referenced_ids:
                        findings.append(
                            ValidationFinding(
                                code=MISSING_EVIDENCE_LINK_CODE,
                                message=(
                                    f"Section `{section}` must reference citation ids from "
                                    "`Sources` for material research claims."
                                ),
                                severity="high",
                                location=location,
                            )
                        )
                        continue

                    unknown_ids = sorted(referenced_ids - research_source_ids)
                    if unknown_ids:
                        findings.append(
                            ValidationFinding(
                                code=MISSING_EVIDENCE_LINK_CODE,
                                message=(
                                    f"Section `{section}` references unknown citation ids: "
                                    f"{', '.join(f'[{item}]' for item in unknown_ids)}."
                                ),
                                severity="high",
                                location=location,
                            )
                        )

            if stage == "plan" and output_path.name == "plan.md":
                normalized_section = _normalized_heading(section)
                compact_content = re.sub(r"\s+", " ", section_content).strip()
                bullet_items = _extract_bullet_items(section_content)

                if normalized_section == "milestones":
                    if not bullet_items:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Required section `Milestones` must use bullet items "
                                    "with stable milestone ids (for example `M1`)."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    elif not plan_milestone_ids:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Milestones` must declare stable milestone ids "
                                    "(for example `M1`, `M2`) for sequencing and "
                                    "verification mapping."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )

                if normalized_section == "dependencies":
                    if not bullet_items:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Required section `Dependencies` must use bullet items "
                                    "so ordering constraints are explicit."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    elif compact_content.lower() in {"none", "- none"}:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Dependencies` cannot be `none`; list explicit "
                                    "upstream or sequencing constraints."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )

                if normalized_section == "risks":
                    if not bullet_items:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Required section `Risks` must use bullet items with "
                                    "concrete mitigation direction."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    elif compact_content.lower() in {"none", "- none"}:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Risks` cannot be `none`; include concrete delivery "
                                    "risks with mitigation intent."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    elif any(
                        _RISK_MITIGATION_PATTERN.search(item) is None for item in bullet_items
                    ):
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Each `Risks` item must include mitigation direction "
                                    "(for example `mitigation:`)."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )

                if normalized_section == "verification notes":
                    if not bullet_items:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Required section `Verification notes` must use bullet "
                                    "items mapped to milestone ids."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    elif compact_content.lower() in {"none", "- none"}:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Verification notes` cannot be `none`; map checks "
                                    "to milestone ids (for example `M1`)."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    else:
                        referenced_milestone_ids = _extract_milestone_ids(section_content)
                        if not referenced_milestone_ids:
                            findings.append(
                                ValidationFinding(
                                    code=INCOMPLETE_SECTION_CODE,
                                    message=(
                                        "Section `Verification notes` must reference milestone ids "
                                        "(for example `M1`) to keep checks tied to "
                                        "planned increments."
                                    ),
                                    severity="medium",
                                    location=location,
                                )
                            )
                        else:
                            unknown_milestone_ids = sorted(
                                referenced_milestone_ids - plan_milestone_ids
                            )
                            if unknown_milestone_ids:
                                unknown_ids_text = ", ".join(unknown_milestone_ids)
                                findings.append(
                                    ValidationFinding(
                                        code=INCOMPLETE_SECTION_CODE,
                                        message=(
                                            "Section `Verification notes` references "
                                            f"unknown milestone ids: {unknown_ids_text}."
                                        ),
                                        severity="medium",
                                        location=location,
                                    )
                                )

            if stage == "review-spec" and output_path.name == "review-spec-report.md":
                normalized_section = _normalized_heading(section)
                compact_content = re.sub(r"\s+", " ", section_content).strip()
                bullet_items = _extract_bullet_items(section_content)

                if normalized_section == "issue list":
                    if not bullet_items:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Required section `Issue list` must use bullet items with "
                                    "severity and rationale."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    else:
                        if any(
                            _REVIEW_SPEC_SEVERITY_PATTERN.search(item) is None
                            for item in bullet_items
                        ):
                            findings.append(
                                ValidationFinding(
                                    code=INCOMPLETE_SECTION_CODE,
                                    message=(
                                        "Each `Issue list` item must include explicit severity "
                                        "(critical/high/medium/low)."
                                    ),
                                    severity="medium",
                                    location=location,
                                )
                            )
                        if any(
                            _REVIEW_SPEC_RATIONALE_PATTERN.search(item) is None
                            for item in bullet_items
                        ):
                            findings.append(
                                ValidationFinding(
                                    code=INCOMPLETE_SECTION_CODE,
                                    message=(
                                        "Each `Issue list` item must include rationale "
                                        "(for example `because ...`)."
                                    ),
                                    severity="medium",
                                    location=location,
                                )
                            )

                if normalized_section == "recommendation summary":
                    if not bullet_items:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Required section `Recommendation summary` must use "
                                    "prioritized bullet items."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    elif compact_content.lower() in {"none", "- none"}:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Recommendation summary` cannot be `none`; "
                                    "include actionable remediation steps."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )

                if normalized_section == "readiness state" and review_spec_readiness_state is None:
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Section `Readiness state` must declare one explicit state: "
                                "`ready`, `ready-with-conditions`, or `not-ready`."
                            ),
                            severity="medium",
                            location=location,
                        )
                    )

                if normalized_section == "decision" and review_spec_decision is None:
                    findings.append(
                        ValidationFinding(
                            code=INCOMPLETE_SECTION_CODE,
                            message=(
                                "Section `Decision` must declare one explicit sign-off status: "
                                "`approved`, `approved-with-conditions`, or `rejected`."
                            ),
                            severity="medium",
                            location=location,
                        )
                    )

            if stage == "tasklist" and output_path.name == "tasklist.md":
                normalized_section = _normalized_heading(section)
                compact_content = re.sub(r"\s+", " ", section_content).strip()
                bullet_items = _extract_bullet_items(section_content)

                if normalized_section == "task summary":
                    if compact_content.lower() in {"none", "- none"} or len(compact_content) < 30:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Task summary` is too brief to explain decomposition "
                                    "scope and sequencing intent."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )

                if normalized_section == "ordered tasks":
                    if not tasklist_task_ids:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Ordered tasks` must declare stable task ids "
                                    "(for example `TL-1`) in executable order."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    elif not bullet_items and "###" not in section_content:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Ordered tasks` must enumerate task entries as bullet "
                                    "items or task subheadings with ids."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )

                if normalized_section == "dependencies":
                    if not bullet_items:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Dependencies` must use bullet items with explicit "
                                    "task dependency notes."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    else:
                        referenced_task_ids = _extract_tasklist_task_ids(section_content)
                        if (
                            tasklist_task_ids
                            and not referenced_task_ids
                            and compact_content.lower() not in {"none", "- none"}
                        ):
                            findings.append(
                                ValidationFinding(
                                    code=INCOMPLETE_SECTION_CODE,
                                    message=(
                                        "Section `Dependencies` must reference task ids or "
                                        "explicitly mark entries as `none`."
                                    ),
                                    severity="medium",
                                    location=location,
                                )
                            )
                        else:
                            unknown_task_ids = sorted(
                                referenced_task_ids - tasklist_task_ids
                            )
                            if unknown_task_ids:
                                unknown_ids_text = ", ".join(unknown_task_ids)
                                findings.append(
                                    ValidationFinding(
                                        code=INCOMPLETE_SECTION_CODE,
                                        message=(
                                            "Section `Dependencies` references unknown task ids: "
                                            f"{unknown_ids_text}."
                                        ),
                                        severity="medium",
                                        location=location,
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
                                    ValidationFinding(
                                        code=INCOMPLETE_SECTION_CODE,
                                        message=(
                                            "Section `Dependencies` must include explicit entries "
                                            f"for each task id. Missing: {missing_ids_text}."
                                        ),
                                        severity="medium",
                                        location=location,
                                    )
                                )

                if normalized_section == "verification notes":
                    if not bullet_items:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Verification notes` must use bullet items mapped "
                                    "to task ids."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    elif compact_content.lower() in {"none", "- none"}:
                        findings.append(
                            ValidationFinding(
                                code=INCOMPLETE_SECTION_CODE,
                                message=(
                                    "Section `Verification notes` cannot be `none`; include at "
                                    "least one concrete check per task."
                                ),
                                severity="medium",
                                location=location,
                            )
                        )
                    else:
                        referenced_task_ids = _extract_tasklist_task_ids(section_content)
                        if tasklist_task_ids and not referenced_task_ids:
                            findings.append(
                                ValidationFinding(
                                    code=INCOMPLETE_SECTION_CODE,
                                    message=(
                                        "Section `Verification notes` must reference task ids "
                                        "so checks map to task decomposition."
                                    ),
                                    severity="medium",
                                    location=location,
                                )
                            )
                        else:
                            unknown_task_ids = sorted(
                                referenced_task_ids - tasklist_task_ids
                            )
                            if unknown_task_ids:
                                unknown_ids_text = ", ".join(unknown_task_ids)
                                findings.append(
                                    ValidationFinding(
                                        code=INCOMPLETE_SECTION_CODE,
                                        message=(
                                            "Section `Verification notes` references unknown task "
                                            f"ids: {unknown_ids_text}."
                                        ),
                                        severity="medium",
                                        location=location,
                                    )
                                )

                            missing_verification_entries = sorted(
                                tasklist_task_ids - referenced_task_ids
                            )
                            if missing_verification_entries:
                                missing_ids_text = ", ".join(missing_verification_entries)
                                findings.append(
                                    ValidationFinding(
                                        code=INCOMPLETE_SECTION_CODE,
                                        message=(
                                            "Section `Verification notes` must include "
                                            "at least one "
                                            f"check per task id. Missing: {missing_ids_text}."
                                        ),
                                        severity="medium",
                                        location=location,
                                    )
                                )

        if (
            stage == "review-spec"
            and output_path.name == "review-spec-report.md"
            and review_spec_readiness_state is not None
            and review_spec_decision is not None
        ):
            expected_decision_by_state = {
                "ready": "approved",
                "ready-with-conditions": "approved-with-conditions",
                "not-ready": "rejected",
            }
            expected_decision = expected_decision_by_state[review_spec_readiness_state]
            if review_spec_decision != expected_decision:
                findings.append(
                    ValidationFinding(
                        code=INCOMPLETE_SECTION_CODE,
                        message=(
                            "Sections `Readiness state` and `Decision` are inconsistent: "
                            f"`{review_spec_readiness_state}` expects `{expected_decision}`."
                        ),
                        severity="high",
                        location=review_spec_decision_location
                        or ValidationIssueLocation(
                            workspace_relative_path=_workspace_relative(
                                output_path, workspace_root
                            ),
                            line_number=1,
                        ),
                    )
                )

    return tuple(findings)

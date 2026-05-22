from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from aidd.core.markdown import (
    MarkdownSectionIndex,
    extract_inline_code_tokens,
)
from aidd.core.workspace import stage_output_root as workspace_stage_output_root
from aidd.evals.repository_changes import RepositoryChanges, collect_repository_changes
from aidd.harness.runner import HarnessQualityResult
from aidd.harness.scenarios import Scenario, ScenarioAuthoredTask

QualityGate = Literal["pass", "warn", "fail", "none"]
QualityVerdict = Literal["ready", "ready-with-risks", "not-ready", "none"]

_REVIEW_STATUS_VALUES = ("approved", "approved-with-conditions", "rejected")
_QA_VERDICT_VALUES = ("ready", "ready-with-risks", "not-ready")
_FULL_FLOW_PRIMARY_OUTPUTS: dict[str, str] = {
    "idea": "idea-brief.md",
    "research": "research-notes.md",
    "plan": "plan.md",
    "review-spec": "review-spec-report.md",
    "tasklist": "tasklist.md",
    "implement": "implementation-report.md",
    "review": "review-report.md",
    "qa": "qa-report.md",
}


@dataclass(frozen=True, slots=True)
class QualityDimensionScore:
    name: str
    score: int
    rationale: str


@dataclass(frozen=True, slots=True)
class LiveQualityAssessment:
    gate: QualityGate
    verdict: QualityVerdict
    dimensions: tuple[QualityDimensionScore, ...]
    review_status: str | None
    qa_verdict: str | None
    blocking_findings: tuple[str, ...]
    suggested_follow_ups: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LiveQualityEvidence:
    missing_stage_paths: tuple[Path, ...]
    review_status: str | None
    qa_verdict: str | None
    unresolved_must_fix_count: int
    evidence_reference_count: int
    repair_attempt_count: int
    changed_file_count: int | None
    repository_change_errors: tuple[str, ...]
    touched_file_mismatches: tuple[str, ...]
    weak_doc_example_count: int


@dataclass(frozen=True, slots=True)
class LiveQualityReportSections:
    blocking_lines: tuple[str, ...]
    root_failure_lines: tuple[str, ...]
    downstream_lines: tuple[str, ...]
    follow_up_lines: tuple[str, ...]
    evidence_lines: tuple[str, ...]


def _read_text_if_exists(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _extract_backticked_value(text: str | None, *, allowed: tuple[str, ...]) -> str | None:
    if text is None:
        return None
    for value in allowed:
        token = f"`{value}`"
        if token in text:
            return value
    return None


def _normalized_status_line_value(line: str) -> str:
    normalized = line.strip()
    normalized = re.sub(r"^\s*[-*]\s+", "", normalized)
    normalized = normalized.replace("**", "")
    normalized = normalized.strip("` \t.")
    label_match = re.match(
        r"^(?:review status|approval status|qa verdict|quality verdict|verdict|status)"
        r"\s*:\s*(?P<value>.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if label_match is not None:
        normalized = label_match.group("value").strip("` \t.")
    return normalized.lower()


def _status_value_from_normalized_line(
    normalized: str,
    *,
    allowed: tuple[str, ...],
    allow_leading_token: bool,
) -> str | None:
    allowed_by_length = sorted(allowed, key=len, reverse=True)
    for value in allowed_by_length:
        if normalized == value:
            return value
        if allow_leading_token and normalized.startswith(value):
            suffix = normalized[len(value) :]
            if suffix and suffix[0] in ".:;,-":
                return value
    return None


def _extract_markdown_status_value(
    text: str | None,
    *,
    allowed: tuple[str, ...],
    section_candidates: tuple[str, ...],
) -> str | None:
    backticked = _extract_backticked_value(text, allowed=allowed)
    if backticked is not None:
        return backticked
    if text is None:
        return None

    in_target_section = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip().lower()
            in_target_section = heading in section_candidates
            continue

        normalized = _normalized_status_line_value(stripped)
        status_value = _status_value_from_normalized_line(
            normalized,
            allowed=allowed,
            allow_leading_token=in_target_section,
        )
        if status_value is not None:
            return status_value
        if in_target_section:
            return None
    return None


def _count_must_fix_findings(text: str | None) -> int:
    if text is None:
        return 0
    count = 0
    finding_item_pattern = re.compile(
        r"^\s*[-*]\s*`?(?:REV|RV|I|FINDING|QA)-?\d+\b.*\bmust-fix\b",
        flags=re.IGNORECASE,
    )
    disposition_pattern = re.compile(
        r"^\s*[-*]?\s*(?:disposition|status)\s*:\s*`?must-fix`?\b",
        flags=re.IGNORECASE,
    )
    for line in text.splitlines():
        if disposition_pattern.search(line) or finding_item_pattern.search(line):
            count += 1
    return count


def _count_evidence_references(text: str | None) -> int:
    if text is None:
        return 0
    evidence_pattern = re.compile(
        r"^\s*[-*]\s*(?:`|\*\*)?EV-\d+\b",
        flags=re.IGNORECASE,
    )
    return sum(1 for line in text.splitlines() if evidence_pattern.search(line))


def _repo_root_from_workspace(workspace_root: Path) -> Path | None:
    if workspace_root.name == ".aidd":
        return workspace_root.parent
    return None


def _git_output(*, repo_root: Path, args: tuple[str, ...]) -> str | None:
    if not (repo_root / ".git").exists():
        return None
    try:
        completed = subprocess.run(
            ("git", *args),
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def _repository_changes_from_workspace(workspace_root: Path) -> RepositoryChanges | None:
    repo_root = _repo_root_from_workspace(workspace_root)
    if repo_root is None:
        return None
    if not (repo_root / ".git").exists():
        return None
    return collect_repository_changes(repo_root)


def _implementation_report_touched_files(report_text: str | None) -> tuple[str, ...]:
    if report_text is None:
        return tuple()
    section_index = MarkdownSectionIndex.from_markdown(report_text)
    match = section_index.first_match(("Touched files",))
    if match is None:
        return tuple()

    section_text = section_index.section_content(match[0])
    paths: list[str] = []
    for raw_line in section_text.splitlines():
        line = raw_line.lstrip()
        if not line.startswith("- "):
            continue
        tokens = extract_inline_code_tokens(line)
        if not tokens:
            continue
        normalized = _normalize_reported_touched_file(tokens[0])
        if normalized is None:
            continue
        paths.append(normalized)
    return tuple(dict.fromkeys(paths))


def _normalize_reported_touched_file(path_text: str) -> str | None:
    normalized = path_text.removeprefix("./").strip()
    line_suffix_match = re.match(r"^(?P<path>.+?):\d+(?::\d+)?$", normalized)
    if line_suffix_match is not None:
        normalized = line_suffix_match.group("path")
    if not _looks_like_reported_touched_file(normalized):
        return None
    return normalized


def _looks_like_reported_touched_file(path_text: str) -> bool:
    if (
        not path_text
        or path_text.startswith("/")
        or path_text.startswith(".aidd/")
        or "://" in path_text
        or any(char.isspace() for char in path_text)
        or any(char in path_text for char in "()")
        or "'" in path_text
        or '"' in path_text
    ):
        return False
    return "/" in path_text or "." in Path(path_text).name


def _touched_file_mismatches(
    *,
    changed_files: tuple[str, ...] | None,
    implementation_report_text: str | None,
) -> tuple[str, ...]:
    if changed_files is None:
        return tuple()
    changed_set = {path.removeprefix("./") for path in changed_files}
    return tuple(
        path
        for path in _implementation_report_touched_files(implementation_report_text)
        if path not in changed_set
    )


def _count_weak_doc_examples(
    workspace_root: Path,
    *,
    repository_changes: RepositoryChanges | None = None,
) -> int:
    repo_root = _repo_root_from_workspace(workspace_root)
    if repo_root is None:
        return 0
    output = _git_output(
        repo_root=repo_root,
        args=("diff", "--", "*.md", "docs", "README.md"),
    )
    weak_patterns = (
        "https://example.org",
        "https://example.com",
        "http://example.org",
        "http://example.com",
        "placeholder",
        "todo",
    )
    normalized = (output or "").lower()
    weak_count = sum(normalized.count(pattern) for pattern in weak_patterns)
    if not (repo_root / ".git").exists():
        return weak_count

    changes = repository_changes or collect_repository_changes(repo_root)
    for path_text in changes.untracked_files:
        path = repo_root / path_text
        if path.suffix.lower() != ".md" and path.name.lower() != "readme.md":
            continue
        if not (path_text.startswith("docs/") or path.name.lower() == "readme.md"):
            continue
        text = _read_text_if_exists(path)
        if text is None:
            continue
        lowered = text.lower()
        weak_count += sum(lowered.count(pattern) for pattern in weak_patterns)
    return weak_count


def _count_repair_attempt_signals(*, workspace_root: Path, work_item: str) -> int:
    count = 0
    for stage in _FULL_FLOW_PRIMARY_OUTPUTS:
        output_root = workspace_stage_output_root(
            root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        stage_result_text = _read_text_if_exists(output_root / "stage-result.md") or ""
        count += len(re.findall(r"\brepair\b|attempt-000[2-9]", stage_result_text, re.I))
    return count


def _required_stage_paths(*, workspace_root: Path, work_item: str) -> tuple[Path, ...]:
    paths: list[Path] = []
    for stage, filename in _FULL_FLOW_PRIMARY_OUTPUTS.items():
        output_root = workspace_stage_output_root(
            root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        paths.extend(
            (
                output_root / filename,
                output_root / "stage-result.md",
                output_root / "validator-report.md",
            )
        )
    return tuple(paths)


def _collect_live_quality_evidence(
    *,
    workspace_root: Path,
    work_item: str,
) -> LiveQualityEvidence:
    missing_stage_paths = tuple(
        path for path in _required_stage_paths(workspace_root=workspace_root, work_item=work_item)
        if not path.exists()
    )
    review_report_path = workspace_stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="review",
    ) / "review-report.md"
    qa_report_path = workspace_stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="qa",
    ) / "qa-report.md"
    implementation_report_path = workspace_stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="implement",
    ) / "implementation-report.md"
    review_report_text = _read_text_if_exists(review_report_path)
    qa_report_text = _read_text_if_exists(qa_report_path)
    implementation_report_text = _read_text_if_exists(implementation_report_path)
    repository_changes = _repository_changes_from_workspace(workspace_root)
    repository_change_errors = (
        tuple() if repository_changes is None else repository_changes.command_errors
    )
    changed_files = (
        None
        if repository_changes is None or repository_change_errors
        else repository_changes.changed_files
    )
    return LiveQualityEvidence(
        missing_stage_paths=missing_stage_paths,
        review_status=_extract_markdown_status_value(
            review_report_text,
            allowed=_REVIEW_STATUS_VALUES,
            section_candidates=("verdict", "approval status", "approval decision"),
        ),
        qa_verdict=_extract_markdown_status_value(
            qa_report_text,
            allowed=_QA_VERDICT_VALUES,
            section_candidates=("readiness", "verdict"),
        ),
        unresolved_must_fix_count=_count_must_fix_findings(review_report_text),
        evidence_reference_count=_count_evidence_references(qa_report_text),
        repair_attempt_count=_count_repair_attempt_signals(
            workspace_root=workspace_root,
            work_item=work_item,
        ),
        changed_file_count=None if changed_files is None else len(changed_files),
        repository_change_errors=repository_change_errors,
        touched_file_mismatches=_touched_file_mismatches(
            changed_files=changed_files,
            implementation_report_text=implementation_report_text,
        ),
        weak_doc_example_count=_count_weak_doc_examples(
            workspace_root,
            repository_changes=repository_changes,
        ),
    )


def _blocking_findings_for_live_quality(
    *,
    evidence: LiveQualityEvidence,
    execution_status: str,
    selected_task: ScenarioAuthoredTask | None,
    quality_error: BaseException | None,
) -> list[str]:
    blocking_findings: list[str] = []
    if selected_task is None:
        blocking_findings.append("selected authored task snapshot is missing")
    if execution_status != "pass":
        blocking_findings.append(
            "execution verdict is not pass, so the full-flow live audit is not clean"
        )
    if evidence.missing_stage_paths:
        missing_preview = ", ".join(path.name for path in evidence.missing_stage_paths[:4])
        blocking_findings.append(
            f"required full-flow stage artifacts are missing ({missing_preview})"
        )
    if quality_error is not None:
        blocking_findings.append(f"quality commands failed: {quality_error}")
    if evidence.unresolved_must_fix_count > 0:
        blocking_findings.append(
            "review report still contains unresolved must-fix findings "
            f"({evidence.unresolved_must_fix_count})"
        )
    if evidence.qa_verdict == "not-ready":
        blocking_findings.append("QA report declares `not-ready`")
    if evidence.review_status is None:
        blocking_findings.append("review approval status is missing from review-report.md")
    if evidence.qa_verdict is None:
        blocking_findings.append("QA verdict is missing from qa-report.md")
    if evidence.weak_doc_example_count > 0:
        blocking_findings.append(
            "documentation examples include placeholder or non-runnable example endpoints "
            f"({evidence.weak_doc_example_count})"
        )
    if evidence.repository_change_errors:
        blocking_findings.append(
            "repository change collection failed: "
            + "; ".join(evidence.repository_change_errors[:3])
        )
    if evidence.touched_file_mismatches:
        preview = ", ".join(evidence.touched_file_mismatches[:4])
        blocking_findings.append(
            "implementation report lists touched files with no matching repository change "
            f"evidence ({preview})"
        )
    return blocking_findings


def _score_flow_fidelity(
    *,
    evidence: LiveQualityEvidence,
    execution_status: str,
    selected_task: ScenarioAuthoredTask | None,
    quality_error: BaseException | None,
) -> QualityDimensionScore:
    if (
        quality_error is not None
        or selected_task is None
        or evidence.missing_stage_paths
        or execution_status != "pass"
    ):
        return QualityDimensionScore(
            name="flow_fidelity",
            score=0,
            rationale="Full-flow contract evidence is incomplete or execution did not pass.",
        )
    return QualityDimensionScore(
        name="flow_fidelity",
        score=3,
        rationale=(
            "Installed live run preserved selected authored task evidence and complete "
            "`idea -> qa` artifacts."
        ),
    )


def _score_artifact_quality(
    *,
    evidence: LiveQualityEvidence,
    follow_ups: list[str],
) -> QualityDimensionScore:
    if (
        evidence.missing_stage_paths
        or evidence.review_status is None
        or evidence.qa_verdict is None
    ):
        return QualityDimensionScore(
            name="artifact_quality",
            score=0,
            rationale="Required stage artifacts or review/QA decisions are missing.",
        )
    if evidence.evidence_reference_count == 0:
        follow_ups.append(
            "Strengthen QA evidence references so verdict claims cite concrete artifacts."
        )
        return QualityDimensionScore(
            name="artifact_quality",
            score=1,
            rationale="QA artifacts exist but evidence references are weak or absent.",
        )
    if (
        evidence.review_status == "approved-with-conditions"
        or evidence.qa_verdict == "ready-with-risks"
        or evidence.repair_attempt_count >= 3
    ):
        if evidence.repair_attempt_count >= 3:
            follow_ups.append(
                "Reduce repair burden by tightening stage skeleton guidance or task context."
            )
        return QualityDimensionScore(
            name="artifact_quality",
            score=2,
            rationale=(
                "Artifacts are valid and usable, but review or QA still carries "
                "bounded caveats."
            ),
        )
    return QualityDimensionScore(
        name="artifact_quality",
        score=3,
        rationale="Artifacts are complete, validated, and evidence-backed.",
    )


def _score_code_quality(
    *,
    scenario: Scenario,
    evidence: LiveQualityEvidence,
    quality_result: HarnessQualityResult | None,
    quality_error: BaseException | None,
    follow_ups: list[str],
) -> QualityDimensionScore:
    if (
        quality_error is not None
        or evidence.unresolved_must_fix_count > 0
        or evidence.qa_verdict == "not-ready"
        or evidence.repository_change_errors
        or evidence.touched_file_mismatches
    ):
        return QualityDimensionScore(
            name="code_quality",
            score=0,
            rationale=(
                "Quality checks failed, review/QA evidence says the code result "
                "is not ready, repository change evidence could not be collected, "
                "or implementation file claims do not match repository change evidence."
            ),
        )
    suspiciously_small = (
        evidence.changed_file_count is not None
        and scenario.feature_size in {"medium", "large", "xlarge"}
        and evidence.changed_file_count < 2
    )
    if suspiciously_small or evidence.weak_doc_example_count > 0:
        if suspiciously_small:
            follow_ups.append(
                "Inspect why the implementation changed fewer files than the authored "
                "task scope implies."
            )
        if evidence.weak_doc_example_count > 0:
            follow_ups.append(
                "Replace placeholder documentation examples with runnable, target-relevant "
                "examples."
            )
        return QualityDimensionScore(
            name="code_quality",
            score=1,
            rationale=(
                "Code or docs result passed basic gates but quality heuristics flagged "
                "scope or example weakness."
            ),
        )
    if (
        evidence.review_status == "approved-with-conditions"
        or evidence.qa_verdict == "ready-with-risks"
    ):
        follow_ups.append(
            "Resolve review conditions and residual QA risks before treating the run "
            "as clean."
        )
        return QualityDimensionScore(
            name="code_quality",
            score=1,
            rationale="Code result is usable but still carries explicit review or QA conditions.",
        )
    if quality_result is None:
        return QualityDimensionScore(
            name="code_quality",
            score=0,
            rationale="No quality command evidence was recorded for the live run.",
        )
    return QualityDimensionScore(
        name="code_quality",
        score=3,
        rationale="Quality commands passed and review/QA do not report blocking code concerns.",
    )


def _quality_verdict_from_evidence(evidence: LiveQualityEvidence) -> QualityVerdict:
    if evidence.qa_verdict == "not-ready":
        return "not-ready"
    if evidence.qa_verdict == "ready-with-risks":
        return "ready-with-risks"
    if evidence.qa_verdict == "ready":
        return "ready"
    return "not-ready"


def _quality_gate_for_dimensions(
    *,
    evidence: LiveQualityEvidence,
    dimensions: tuple[QualityDimensionScore, ...],
    quality_verdict: QualityVerdict,
) -> QualityGate:
    any_zero = any(dimension.score == 0 for dimension in dimensions)
    any_one = any(dimension.score == 1 for dimension in dimensions)
    if any_zero:
        return "fail"
    if (
        any_one
        or evidence.review_status == "approved-with-conditions"
        or quality_verdict == "ready-with-risks"
    ):
        return "warn"
    return "pass"


def build_live_quality_assessment(
    *,
    scenario: Scenario,
    workspace_root: Path,
    work_item: str,
    execution_status: str,
    selected_task: ScenarioAuthoredTask | None,
    quality_result: HarnessQualityResult | None,
    quality_error: BaseException | None,
) -> LiveQualityAssessment:
    if not scenario.is_live:
        return LiveQualityAssessment(
            gate="none",
            verdict="none",
            dimensions=tuple(),
            review_status=None,
            qa_verdict=None,
            blocking_findings=tuple(),
            suggested_follow_ups=tuple(),
        )

    evidence = _collect_live_quality_evidence(
        workspace_root=workspace_root,
        work_item=work_item,
    )

    follow_ups: list[str] = []
    blocking_findings = _blocking_findings_for_live_quality(
        evidence=evidence,
        execution_status=execution_status,
        selected_task=selected_task,
        quality_error=quality_error,
    )
    dimensions = (
        _score_flow_fidelity(
            evidence=evidence,
            execution_status=execution_status,
            selected_task=selected_task,
            quality_error=quality_error,
        ),
        _score_artifact_quality(evidence=evidence, follow_ups=follow_ups),
        _score_code_quality(
            scenario=scenario,
            evidence=evidence,
            quality_result=quality_result,
            quality_error=quality_error,
            follow_ups=follow_ups,
        ),
    )
    quality_verdict = _quality_verdict_from_evidence(evidence)
    gate = _quality_gate_for_dimensions(
        evidence=evidence,
        dimensions=dimensions,
        quality_verdict=quality_verdict,
    )

    if gate == "fail" and not follow_ups:
        follow_ups.append("Fix the blocking quality findings before re-running the live scenario.")
    if gate == "warn" and not follow_ups:
        follow_ups.append(
            "Address the bounded review or QA caveats before treating this as a clean "
            "live proof."
        )

    return LiveQualityAssessment(
        gate=gate,
        verdict=quality_verdict,
        dimensions=dimensions,
        review_status=evidence.review_status,
        qa_verdict=evidence.qa_verdict,
        blocking_findings=tuple(blocking_findings),
        suggested_follow_ups=tuple(follow_ups),
    )


def _build_live_quality_report_sections(
    *,
    assessment: LiveQualityAssessment,
    feature_selection_path: Path | None,
    quality_transcript_path: Path | None,
    review_report_path: Path | None,
    qa_report_path: Path | None,
) -> LiveQualityReportSections:
    blocking_lines = (
        ("- none",)
        if not assessment.blocking_findings
        else tuple(f"- {finding}" for finding in assessment.blocking_findings)
    )
    root_failure_lines = tuple(
        f"- {finding}"
        for finding in assessment.blocking_findings
        if (
            "execution verdict" in finding
            or "quality commands failed" in finding
            or "selected authored task" in finding
            or "documentation examples include" in finding
        )
    )
    downstream_lines = tuple(
        f"- {finding}"
        for finding in assessment.blocking_findings
        if finding not in {line[2:] for line in root_failure_lines}
    )
    follow_up_lines = (
        ("- none",)
        if not assessment.suggested_follow_ups
        else tuple(f"- {item}" for item in assessment.suggested_follow_ups)
    )
    evidence_lines: list[str] = []
    if feature_selection_path is not None:
        evidence_lines.append(f"- Feature selection: `{feature_selection_path.as_posix()}`")
    if quality_transcript_path is not None:
        evidence_lines.append(f"- Quality transcript: `{quality_transcript_path.as_posix()}`")
    if review_report_path is not None:
        evidence_lines.append(f"- Review report: `{review_report_path.as_posix()}`")
    if qa_report_path is not None:
        evidence_lines.append(f"- QA report: `{qa_report_path.as_posix()}`")
    return LiveQualityReportSections(
        blocking_lines=blocking_lines,
        root_failure_lines=root_failure_lines or ("- none",),
        downstream_lines=downstream_lines or ("- none",),
        follow_up_lines=follow_up_lines,
        evidence_lines=tuple(evidence_lines) or ("- none",),
    )


def render_live_quality_report_markdown(
    *,
    scenario: Scenario,
    assessment: LiveQualityAssessment,
    feature_selection_path: Path | None = None,
    quality_transcript_path: Path | None = None,
    review_report_path: Path | None = None,
    qa_report_path: Path | None = None,
) -> str:
    report_sections = _build_live_quality_report_sections(
        assessment=assessment,
        feature_selection_path=feature_selection_path,
        quality_transcript_path=quality_transcript_path,
        review_report_path=review_report_path,
        qa_report_path=qa_report_path,
    )

    lines = [
        "# Live Quality Report",
        "",
        "## Overview",
        f"- Scenario: `{scenario.scenario_id}`",
        f"- Quality gate: `{assessment.gate}`",
        f"- Quality verdict: `{assessment.verdict}`",
        f"- Review status: `{assessment.review_status or 'missing'}`",
        f"- QA verdict: `{assessment.qa_verdict or 'missing'}`",
        "",
        "## Dimension Scores",
    ]
    for dimension in assessment.dimensions:
        lines.extend(
            (
                f"### {dimension.name}",
                f"- Score: `{dimension.score}`",
                f"- Rationale: {dimension.rationale}",
                "",
            )
        )
    lines.extend(
        (
            "## Root Failure",
            *report_sections.root_failure_lines,
            "",
            "## Downstream Artifact Effects",
            *report_sections.downstream_lines,
            "",
            "## Blocking Findings",
            *report_sections.blocking_lines,
            "",
            "## Evidence",
            *report_sections.evidence_lines,
            "",
            "## Suggested Follow-Ups",
            *report_sections.follow_up_lines,
            "",
        )
    )
    return "\n".join(lines)


def write_live_quality_report_markdown(
    *,
    path: Path,
    scenario: Scenario,
    assessment: LiveQualityAssessment,
    feature_selection_path: Path | None = None,
    quality_transcript_path: Path | None = None,
    review_report_path: Path | None = None,
    qa_report_path: Path | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_live_quality_report_markdown(
            scenario=scenario,
            assessment=assessment,
            feature_selection_path=feature_selection_path,
            quality_transcript_path=quality_transcript_path,
            review_report_path=review_report_path,
            qa_report_path=qa_report_path,
        ),
        encoding="utf-8",
    )
    return path


__all__ = [
    "LiveQualityAssessment",
    "QualityDimensionScore",
    "QualityGate",
    "QualityVerdict",
    "build_live_quality_assessment",
    "render_live_quality_report_markdown",
    "write_live_quality_report_markdown",
]

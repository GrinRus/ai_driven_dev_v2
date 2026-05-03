from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from aidd.core.workspace import stage_output_root as workspace_stage_output_root
from aidd.harness.runner import HarnessQualityResult
from aidd.harness.scenarios import Scenario, ScenarioIssueSeed

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
    evidence_pattern = re.compile(r"^\s*[-*]\s*`?EV-\d+\b", flags=re.IGNORECASE)
    return sum(1 for line in text.splitlines() if evidence_pattern.search(line))


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
    review_report_text = _read_text_if_exists(review_report_path)
    qa_report_text = _read_text_if_exists(qa_report_path)
    return LiveQualityEvidence(
        missing_stage_paths=missing_stage_paths,
        review_status=_extract_backticked_value(
            review_report_text,
            allowed=_REVIEW_STATUS_VALUES,
        ),
        qa_verdict=_extract_backticked_value(
            qa_report_text,
            allowed=_QA_VERDICT_VALUES,
        ),
        unresolved_must_fix_count=_count_must_fix_findings(review_report_text),
        evidence_reference_count=_count_evidence_references(qa_report_text),
    )


def build_live_quality_assessment(
    *,
    scenario: Scenario,
    workspace_root: Path,
    work_item: str,
    execution_status: str,
    selected_issue: ScenarioIssueSeed | None,
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

    blocking_findings: list[str] = []
    follow_ups: list[str] = []

    if selected_issue is None:
        blocking_findings.append("selected issue snapshot is missing")
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

    if (
        quality_error is not None
        or selected_issue is None
        or evidence.missing_stage_paths
        or execution_status != "pass"
    ):
        flow_fidelity = QualityDimensionScore(
            name="flow_fidelity",
            score=0,
            rationale="Full-flow contract evidence is incomplete or execution did not pass.",
        )
    else:
        flow_fidelity = QualityDimensionScore(
            name="flow_fidelity",
            score=3,
            rationale=(
                "Installed live run preserved selected issue evidence and complete "
                "`idea -> qa` artifacts."
            ),
        )

    if (
        evidence.missing_stage_paths
        or evidence.review_status is None
        or evidence.qa_verdict is None
    ):
        artifact_quality = QualityDimensionScore(
            name="artifact_quality",
            score=0,
            rationale="Required stage artifacts or review/QA decisions are missing.",
        )
    elif evidence.evidence_reference_count == 0:
        artifact_quality = QualityDimensionScore(
            name="artifact_quality",
            score=1,
            rationale="QA artifacts exist but evidence references are weak or absent.",
        )
        follow_ups.append(
            "Strengthen QA evidence references so verdict claims cite concrete artifacts."
        )
    elif (
        evidence.review_status == "approved-with-conditions"
        or evidence.qa_verdict == "ready-with-risks"
    ):
        artifact_quality = QualityDimensionScore(
            name="artifact_quality",
            score=2,
            rationale=(
                "Artifacts are valid and usable, but review or QA still carries "
                "bounded caveats."
            ),
        )
    else:
        artifact_quality = QualityDimensionScore(
            name="artifact_quality",
            score=3,
            rationale="Artifacts are complete, validated, and evidence-backed.",
        )

    if (
        quality_error is not None
        or evidence.unresolved_must_fix_count > 0
        or evidence.qa_verdict == "not-ready"
    ):
        code_quality = QualityDimensionScore(
            name="code_quality",
            score=0,
            rationale=(
                "Quality checks failed or review/QA evidence says the code result "
                "is not ready."
            ),
        )
    elif (
        evidence.review_status == "approved-with-conditions"
        or evidence.qa_verdict == "ready-with-risks"
    ):
        code_quality = QualityDimensionScore(
            name="code_quality",
            score=1,
            rationale="Code result is usable but still carries explicit review or QA conditions.",
        )
        follow_ups.append(
            "Resolve review conditions and residual QA risks before treating the run "
            "as clean."
        )
    elif quality_result is None:
        code_quality = QualityDimensionScore(
            name="code_quality",
            score=0,
            rationale="No quality command evidence was recorded for the live run.",
        )
    else:
        code_quality = QualityDimensionScore(
            name="code_quality",
            score=3,
            rationale="Quality commands passed and review/QA do not report blocking code concerns.",
        )

    dimensions = (flow_fidelity, artifact_quality, code_quality)
    any_zero = any(dimension.score == 0 for dimension in dimensions)
    any_one = any(dimension.score == 1 for dimension in dimensions)

    if evidence.qa_verdict == "not-ready":
        quality_verdict: QualityVerdict = "not-ready"
    elif evidence.qa_verdict == "ready-with-risks":
        quality_verdict = "ready-with-risks"
    elif evidence.qa_verdict == "ready":
        quality_verdict = "ready"
    else:
        quality_verdict = "not-ready"

    if any_zero:
        gate: QualityGate = "fail"
    elif (
        any_one
        or evidence.review_status == "approved-with-conditions"
        or quality_verdict == "ready-with-risks"
    ):
        gate = "warn"
    else:
        gate = "pass"

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
    issue_selection_path: Path | None,
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
            or "selected issue" in finding
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
    if issue_selection_path is not None:
        evidence_lines.append(f"- Issue selection: `{issue_selection_path.as_posix()}`")
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
    issue_selection_path: Path | None = None,
    quality_transcript_path: Path | None = None,
    review_report_path: Path | None = None,
    qa_report_path: Path | None = None,
) -> str:
    report_sections = _build_live_quality_report_sections(
        assessment=assessment,
        issue_selection_path=issue_selection_path,
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
    issue_selection_path: Path | None = None,
    quality_transcript_path: Path | None = None,
    review_report_path: Path | None = None,
    qa_report_path: Path | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_live_quality_report_markdown(
            scenario=scenario,
            assessment=assessment,
            issue_selection_path=issue_selection_path,
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

from __future__ import annotations

from pathlib import Path

from aidd.core.workspace import stage_output_root
from aidd.evals.quality import (
    build_live_quality_assessment,
    render_live_quality_report_markdown,
)
from aidd.harness.runner import HarnessCommandTranscript, HarnessQualityResult
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioFeatureSource,
    ScenarioIssueSeed,
    ScenarioQualityConfig,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _build_live_scenario() -> Scenario:
    return Scenario(
        scenario_id="AIDD-LIVE-TEST-QUALITY",
        task="Exercise live quality scoring",
        repo=ScenarioRepoSource(
            url="https://github.com/example/repo",
            default_branch="main",
            revision="deadbeef",
        ),
        setup=ScenarioCommandSteps(commands=("echo setup",)),
        run=ScenarioRunConfig(
            stage_start="idea",
            stage_end="qa",
            runtime_targets=("generic-cli",),
            patch_budget_files=3,
            timeout_minutes=10,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=("echo verify",)),
        feature_source=ScenarioFeatureSource(
            mode="curated-issue-pool",
            selection_policy="first-listed",
            issues=(
                ScenarioIssueSeed(
                    issue_id="101",
                    title="Example issue",
                    url="https://github.com/example/repo/issues/101",
                    summary="Example summary",
                    labels=("bug",),
                ),
            ),
        ),
        quality=ScenarioQualityConfig(
            commands=("echo quality",),
            rubric_profile="live-full",
            require_review_status="approved",
            allowed_qa_verdicts=("ready", "ready-with-risks"),
            code_review_required=True,
        ),
        runtime_targets=("generic-cli",),
        is_live=True,
        raw={"id": "AIDD-LIVE-TEST-QUALITY"},
    )


def _quality_result() -> HarnessQualityResult:
    return HarnessQualityResult(
        executed_commands=("echo quality",),
        command_transcripts=(
            HarnessCommandTranscript(
                command="echo quality",
                exit_code=0,
                stdout_text="quality\n",
                stderr_text="",
                duration_seconds=0.2,
            ),
        ),
        duration_seconds=0.2,
    )


def _write_stage_outputs(
    workspace_root: Path,
    *,
    work_item: str,
    review_status: str,
    qa_verdict: str,
) -> None:
    stage_files = {
        "idea": ("idea-brief.md", "# Idea Brief\n\n- ok\n"),
        "research": ("research-notes.md", "# Research Notes\n\n- ok\n"),
        "plan": ("plan.md", "# Plan\n\n- ok\n"),
        "review-spec": ("review-spec-report.md", "# Review Spec\n\n- ok\n"),
        "tasklist": ("tasklist.md", "# Tasklist\n\n- ok\n"),
        "implement": ("implementation-report.md", "# Implementation Report\n\n- ok\n"),
        "review": (
            "review-report.md",
            f"# Review Report\n\n- Review status: `{review_status}`\n",
        ),
        "qa": (
            "qa-report.md",
            f"# QA Report\n\n- QA verdict: `{qa_verdict}`\n- EV-001: runtime.log\n",
        ),
    }
    for stage, (filename, content) in stage_files.items():
        output_root = stage_output_root(root=workspace_root, work_item=work_item, stage=stage)
        output_root.mkdir(parents=True, exist_ok=True)
        (output_root / "stage-result.md").write_text(
            "# Stage result\n\n- status: succeeded\n",
            encoding="utf-8",
        )
        (output_root / "validator-report.md").write_text(
            "# Validator report\n\n- Verdict: `pass`\n",
            encoding="utf-8",
        )
        (output_root / filename).write_text(content, encoding="utf-8")


def test_build_live_quality_assessment_returns_pass_for_clean_full_flow(tmp_path: Path) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-PASS"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_issue=scenario.feature_source.issues[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "pass"
    assert assessment.verdict == "ready"
    assert [dimension.score for dimension in assessment.dimensions] == [3, 3, 3]


def test_build_live_quality_assessment_returns_warn_for_bounded_quality_risks(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-WARN"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved-with-conditions",
        qa_verdict="ready-with-risks",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_issue=scenario.feature_source.issues[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "warn"
    assert assessment.verdict == "ready-with-risks"
    report = render_live_quality_report_markdown(scenario=scenario, assessment=assessment)
    assert "Suggested Follow-Ups" in report
    assert "Resolve review conditions" in report


def test_build_live_quality_assessment_returns_fail_when_quality_commands_fail(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-FAIL"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_issue=scenario.feature_source.issues[0],
        quality_result=None,
        quality_error=RuntimeError("quality command failed"),
    )

    assert assessment.gate == "fail"
    assert assessment.verdict == "ready"
    report = render_live_quality_report_markdown(scenario=scenario, assessment=assessment)
    assert "quality command failed" in report

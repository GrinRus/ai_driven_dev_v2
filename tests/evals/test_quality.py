from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

from aidd.core.workspace import stage_output_root
from aidd.evals.quality import (
    build_live_quality_assessment,
    render_live_quality_report_markdown,
)
from aidd.harness.runner import HarnessCommandTranscript, HarnessQualityResult
from aidd.harness.scenarios import (
    Scenario,
    ScenarioAuthoredTask,
    ScenarioCommandSteps,
    ScenarioFeatureSource,
    ScenarioLiveFlowConfig,
    ScenarioQualityConfig,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _build_live_scenario() -> Scenario:
    return Scenario(
        scenario_id="AIDD-LIVE-TEST-QUALITY",
        scenario_class="live-full-flow",
        feature_size="small",
        automation_lane="manual",
        canonical_runtime="generic-cli",
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
            mode="authored-task-pool",
            selection_policy="first-listed",
            tasks=(
                ScenarioAuthoredTask(
                    task_id="TASK-101",
                    title="Example task",
                    summary="Example summary",
                    intent="Exercise live quality scoring.",
                    target_change="Produce a bounded implementation.",
                    expected_scope="Localized test fixture change.",
                    acceptance_criteria=("The change is ready.",),
                    verification=("echo verify",),
                    quality_bar="Quality evidence is complete.",
                    size_rationale="Small test fixture.",
                    interview=tuple(),
                ),
            ),
            fixture_path=None,
            seed_id=None,
            summary=None,
        ),
        quality=ScenarioQualityConfig(
            commands=("echo quality",),
            rubric_profile="live-full",
            require_review_status="approved",
            allowed_qa_verdicts=("ready", "ready-with-risks"),
            code_review_required=True,
        ),
        live_flow=ScenarioLiveFlowConfig(
            driver="stepwise-black-box",
            checkpoint_policy="after-each-step",
            answer_policy="agent-decides",
            frontend_checkpoints=True,
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


def _init_git_repo(path: Path) -> None:
    subprocess.run(("git", "init"), cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ("git", "config", "user.email", "tests@example.com"),
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ("git", "config", "user.name", "AIDD Tests"),
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    (path / "README.md").write_text("baseline\n", encoding="utf-8")
    subprocess.run(("git", "add", "README.md"), cwd=path, check=True, capture_output=True)
    subprocess.run(
        ("git", "commit", "-m", "baseline"),
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
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
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "pass"
    assert assessment.verdict == "ready"
    assert [dimension.score for dimension in assessment.dimensions] == [3, 3, 3]


def test_build_live_quality_assessment_counts_untracked_touched_files(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    workspace_root = repo_root / ".aidd"
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-UNTRACKED"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    source_path = repo_root / "src" / "new_feature.py"
    source_path.parent.mkdir()
    source_path.write_text("print('ok')\n", encoding="utf-8")
    implement_root = stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="implement",
    )
    implement_root.joinpath("implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `src/new_feature.py` - add the selected behavior for route `/**` "
        "without changing `/*`.\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "pass"
    assert assessment.blocking_findings == tuple()


def test_build_live_quality_assessment_ignores_route_snippets_in_touched_files(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    workspace_root = repo_root / ".aidd"
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-ROUTE-SNIPPETS"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    source_path = repo_root / "src" / "router.ts"
    source_path.parent.mkdir()
    source_path.write_text("export const ok = true\n", encoding="utf-8")
    implement_root = stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="implement",
    )
    implement_root.joinpath("implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `src/router.ts` - normalized `/**` to `/*` before the "
        "`path === '/*'` shortcut.\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "pass"
    assert assessment.blocking_findings == tuple()


def test_build_live_quality_assessment_ignores_function_call_tokens_in_touched_files(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    workspace_root = repo_root / ".aidd"
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-FUNCTION-CALL-SNIPPETS"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    source_path = repo_root / "sqlite_utils" / "cli.py"
    source_path.parent.mkdir()
    source_path.write_text("print('ok')\n", encoding="utf-8")
    implement_root = stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="implement",
    )
    implement_root.joinpath("implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `sqlite_utils/cli.py` - integrated Python rows while bypassing "
        "`io.TextIOWrapper(file)` when generated rows are provided.\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "pass"
    assert assessment.blocking_findings == tuple()


def test_build_live_quality_assessment_normalizes_touched_file_line_suffix(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    workspace_root = repo_root / ".aidd"
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-TOUCHED-LINE-SUFFIX"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    source_path = repo_root / "src" / "router.ts"
    source_path.parent.mkdir()
    source_path.write_text("export const ok = true\n", encoding="utf-8")
    implement_root = stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="implement",
    )
    implement_root.joinpath("implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "  - `src/router.ts:12` - normalize `/**` to `/*`.\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "pass"
    assert assessment.blocking_findings == tuple()


def test_build_live_quality_assessment_ignores_url_tokens_in_touched_files(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    workspace_root = repo_root / ".aidd"
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-TOUCHED-URL"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    implement_root = stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="implement",
    )
    implement_root.joinpath("implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `https://example.com:443/docs` - cited compatibility reference, not a file.\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "pass"
    assert assessment.blocking_findings == tuple()


def test_build_live_quality_assessment_ignores_nested_touched_file_explanations(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    workspace_root = repo_root / ".aidd"
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-NESTED-TOUCHED-NOTES"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    readme_path = repo_root / "README.md"
    readme_path.write_text("updated docs\n", encoding="utf-8")
    implement_root = stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="implement",
    )
    implement_root.joinpath("implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `README.md` - updated CLI docs.\n"
        "  - Left `docs/img/httpx-request.png` unchanged and out of scope.\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "pass"
    assert assessment.blocking_findings == tuple()


def test_build_live_quality_assessment_fails_when_touched_files_lack_diff_evidence(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    workspace_root = repo_root / ".aidd"
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-TOUCHED-MISMATCH"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    implement_root = stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="implement",
    )
    implement_root.joinpath("implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `src/missing.py` - claimed source change.\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "fail"
    assert assessment.dimensions[2].score == 0
    assert any(
        "no matching repository change evidence" in finding
        for finding in assessment.blocking_findings
    )


def test_build_live_quality_assessment_fails_on_repository_change_collection_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    workspace_root = repo_root / ".aidd"
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-GIT-ERROR"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    implement_root = stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage="implement",
    )
    implement_root.joinpath("implementation-report.md").write_text(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `src/router.ts` - claimed source change.\n",
        encoding="utf-8",
    )

    def raise_os_error(*_args: object, **_kwargs: object) -> None:
        raise OSError("git unavailable")

    monkeypatch.setattr(subprocess, "run", raise_os_error)

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "fail"
    assert assessment.dimensions[2].score == 0
    assert any(
        "repository change collection failed" in finding
        for finding in assessment.blocking_findings
    )
    assert not any(
        "no matching repository change evidence" in finding
        for finding in assessment.blocking_findings
    )


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
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "warn"
    assert assessment.verdict == "ready-with-risks"
    report = render_live_quality_report_markdown(scenario=scenario, assessment=assessment)
    assert "Suggested Follow-Ups" in report
    assert "Resolve review conditions" in report


def test_build_live_quality_assessment_accepts_contract_verdict_and_bold_evidence(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-CONTRACT-VERDICT"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    review_root = stage_output_root(root=tmp_path, work_item=work_item, stage="review")
    review_root.joinpath("review-report.md").write_text(
        "# Review Report\n\n"
        "## Findings\n\n"
        "### REV-001\n\n"
        "- Severity: `low`\n"
        "- Disposition: `accepted-risk`\n"
        "- Evidence: `implementation-report.md`\n"
        "- Rationale: because the risk is explicitly bounded.\n\n"
        "## Verdict\n\n"
        "**approved**\n\n"
        "## Required follow-up\n\n"
        "- None.\n",
        encoding="utf-8",
    )
    qa_root = stage_output_root(root=tmp_path, work_item=work_item, stage="qa")
    qa_root.joinpath("qa-report.md").write_text(
        "# QA Report\n\n"
        "## Evidence\n\n"
        "- **EV-1** Implementation report verification passed.\n\n"
        "## Readiness\n\n"
        "- **Verdict:** `ready-with-risks`\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.review_status == "approved"
    assert assessment.qa_verdict == "ready-with-risks"
    assert assessment.gate == "warn"
    assert "review approval status is missing from review-report.md" not in (
        assessment.blocking_findings
    )
    assert [dimension.score for dimension in assessment.dimensions] == [3, 2, 1]


def test_build_live_quality_assessment_accepts_verdict_prefix_with_rationale(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-VERDICT-PREFIX"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    review_root = stage_output_root(root=tmp_path, work_item=work_item, stage="review")
    review_root.joinpath("review-report.md").write_text(
        "# Review Report\n\n"
        "## Verdict\n\n"
        "- approved. The implementation satisfies the selected acceptance criteria.\n\n"
        "## Findings\n\n"
        "- none\n\n"
        "## Required follow-up\n\n"
        "- none\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.review_status == "approved"
    assert assessment.gate == "pass"
    assert "review approval status is missing from review-report.md" not in (
        assessment.blocking_findings
    )


def test_build_live_quality_assessment_accepts_quality_verdict_label(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-QA-LABEL"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    qa_root = stage_output_root(root=tmp_path, work_item=work_item, stage="qa")
    qa_root.joinpath("qa-report.md").write_text(
        "# QA Report\n\n"
        "## Verification summary\n\n"
        "- Quality verdict: ready.\n"
        "- Required verification passed.\n\n"
        "## Evidence\n\n"
        "- EV-1: `verify-transcript.json` records passing checks.\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.qa_verdict == "ready"
    assert assessment.gate == "pass"
    assert "QA verdict is missing from qa-report.md" not in assessment.blocking_findings


def test_build_live_quality_assessment_scores_flow_fidelity_independently(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-FLOW-FIDELITY"
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
        execution_status="fail",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert [dimension.name for dimension in assessment.dimensions] == [
        "flow_fidelity",
        "artifact_quality",
        "code_quality",
    ]
    assert [dimension.score for dimension in assessment.dimensions] == [0, 3, 3]
    assert assessment.gate == "fail"


def test_build_live_quality_assessment_scores_artifact_quality_independently(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-ARTIFACT-QUALITY"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    qa_report_path = (
        stage_output_root(root=tmp_path, work_item=work_item, stage="qa")
        / "qa-report.md"
    )
    qa_report_path.write_text(
        "# QA Report\n\n- QA verdict: `ready`\n- Evidence: none recorded\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert [dimension.score for dimension in assessment.dimensions] == [3, 1, 3]
    assert assessment.gate == "warn"
    assert assessment.suggested_follow_ups == (
        "Strengthen QA evidence references so verdict claims cite concrete artifacts.",
    )


def test_build_live_quality_assessment_scores_code_quality_independently(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-CODE-QUALITY"
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
        selected_task=scenario.feature_source.tasks[0],
        quality_result=None,
        quality_error=None,
    )

    assert [dimension.score for dimension in assessment.dimensions] == [3, 3, 0]
    assert assessment.gate == "fail"


def test_build_live_quality_assessment_accounts_for_repair_burden(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-REPAIR-BURDEN"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    for stage in ("idea", "research", "plan"):
        stage_result = stage_output_root(
            root=tmp_path,
            work_item=work_item,
            stage=stage,
        ) / "stage-result.md"
        stage_result.write_text(
            "# Stage result\n\n- repair attempt-0002 resolved contract drift\n",
            encoding="utf-8",
        )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.dimensions[1].score == 2
    assert any("Reduce repair burden" in item for item in assessment.suggested_follow_ups)


def test_build_live_quality_assessment_flags_small_patch_for_medium_scope(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    workspace_root = tmp_path / ".aidd"
    scenario = replace(_build_live_scenario(), feature_size="medium")
    work_item = "WI-QUALITY-SMALL-PATCH"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.dimensions[2].score == 1
    assert any("fewer files" in item for item in assessment.suggested_follow_ups)


def test_build_live_quality_assessment_flags_placeholder_doc_examples(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "README.md").write_text(
        "Use https://example.org/echo as the endpoint.\n",
        encoding="utf-8",
    )
    workspace_root = tmp_path / ".aidd"
    scenario = replace(_build_live_scenario(), feature_size="medium")
    work_item = "WI-QUALITY-WEAK-DOC-EXAMPLE"
    _write_stage_outputs(
        workspace_root,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=workspace_root,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.dimensions[2].score == 1
    assert any("placeholder" in finding for finding in assessment.blocking_findings)


def test_build_live_quality_assessment_ignores_negated_must_fix_mentions(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-NEGATED-MUST-FIX"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready-with-risks",
    )
    review_root = stage_output_root(root=tmp_path, work_item=work_item, stage="review")
    review_root.joinpath("review-report.md").write_text(
        "# Review Report\n\n"
        "- Review status: `approved`\n\n"
        "## Verdict\n\n"
        "- approval status: `approved`\n"
        "- rationale: No `must-fix` findings remain.\n\n"
        "## Required changes\n\n"
        "None. Approval is unconditional; no findings carry `must-fix`.\n",
        encoding="utf-8",
    )
    qa_root = stage_output_root(root=tmp_path, work_item=work_item, stage="qa")
    qa_root.joinpath("qa-report.md").write_text(
        "# QA Report\n\n"
        "- QA verdict: `ready-with-risks`\n"
        "- `EV-1` - runtime.log\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "warn"
    assert "review report still contains unresolved must-fix findings (2)" not in (
        assessment.blocking_findings
    )
    assert assessment.blocking_findings == tuple()
    assert assessment.dimensions[1].score == 2


def test_build_live_quality_assessment_fails_for_actual_must_fix_disposition(
    tmp_path: Path,
) -> None:
    scenario = _build_live_scenario()
    work_item = "WI-QUALITY-MUST-FIX"
    _write_stage_outputs(
        tmp_path,
        work_item=work_item,
        review_status="approved",
        qa_verdict="ready",
    )
    review_root = stage_output_root(root=tmp_path, work_item=work_item, stage="review")
    review_root.joinpath("review-report.md").write_text(
        "# Review Report\n\n"
        "- Review status: `approved`\n\n"
        "## Findings\n\n"
        "### REV-1\n\n"
        "- title: Missing regression coverage.\n"
        "- disposition: `must-fix`\n"
        "- severity: `high`\n",
        encoding="utf-8",
    )

    assessment = build_live_quality_assessment(
        scenario=scenario,
        workspace_root=tmp_path,
        work_item=work_item,
        execution_status="pass",
        selected_task=scenario.feature_source.tasks[0],
        quality_result=_quality_result(),
        quality_error=None,
    )

    assert assessment.gate == "fail"
    assert assessment.blocking_findings == (
        "review report still contains unresolved must-fix findings (1)",
    )


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
        selected_task=scenario.feature_source.tasks[0],
        quality_result=None,
        quality_error=RuntimeError("quality command failed"),
    )

    assert assessment.gate == "fail"
    assert assessment.verdict == "ready"
    report = render_live_quality_report_markdown(scenario=scenario, assessment=assessment)
    assert "quality command failed" in report

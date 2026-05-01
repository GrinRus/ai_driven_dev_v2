from __future__ import annotations

import json
from pathlib import Path

from aidd.evals.stage_timing import (
    build_self_repair_matrix_payload,
    build_stage_timing_payload,
    render_self_repair_matrix_markdown,
    render_stage_timing_markdown,
)
from aidd.harness.runner import HarnessAiddRunResult, HarnessCommandTranscript
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _scenario() -> Scenario:
    return Scenario(
        scenario_id="AIDD-TEST-STAGE-TIMING",
        scenario_class="live-full-flow",
        feature_size="small",
        automation_lane="manual",
        canonical_runtime="claude-code",
        task="measure stage timing",
        repo=ScenarioRepoSource(
            url="https://github.com/example/repo",
            default_branch="main",
            revision=None,
        ),
        setup=ScenarioCommandSteps(commands=("echo setup",)),
        run=ScenarioRunConfig(
            stage_start="idea",
            stage_end="qa",
            runtime_targets=("claude-code",),
            patch_budget_files=3,
            timeout_minutes=90,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=("echo verify",)),
        feature_source=None,
        quality=None,
        runtime_targets=("claude-code",),
        is_live=True,
        raw={"id": "AIDD-TEST-STAGE-TIMING"},
    )


def test_stage_timing_payload_reports_attempt_windows_and_harness_steps(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_root = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-001"
        / "run-20260426T100000Z"
        / "stages"
        / "idea"
    )
    attempt_root = stage_root / "attempts" / "attempt-0001"
    attempt_root.mkdir(parents=True)
    (stage_root / "stage-metadata.json").write_text(
        json.dumps(
            {
                "status": "repair-needed",
                "status_history": [
                    {"status": "executing", "changed_at_utc": "2026-04-26T10:00:00Z"},
                    {"status": "validating", "changed_at_utc": "2026-04-26T10:02:03Z"},
                    {"status": "repair-needed", "changed_at_utc": "2026-04-26T10:02:04Z"},
                    {"status": "executing", "changed_at_utc": "2026-04-26T10:02:04Z"},
                    {"status": "validating", "changed_at_utc": "2026-04-26T10:03:00Z"},
                    {"status": "succeeded", "changed_at_utc": "2026-04-26T10:03:01Z"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (attempt_root / "runtime-exit.json").write_text(
        '{"exit_classification": "success", "exit_code": 0}\n',
        encoding="utf-8",
    )
    repair_attempt_root = stage_root / "attempts" / "attempt-0002"
    repair_attempt_root.mkdir(parents=True)
    (repair_attempt_root / "repair-context.md").write_text(
        "# Repair context\n\n"
        "# Failed checks\n\n"
        "- `STRUCT-MISSING-REQUIRED-SECTION` `high` in `idea-brief.md`: add heading.\n",
        encoding="utf-8",
    )
    work_item_stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "idea"
    work_item_stage_root.mkdir(parents=True)
    (work_item_stage_root / "repair-brief.md").write_text(
        "# Failed checks\n\n- `SEM-PLACEHOLDER-CONTENT` `high` in `idea-brief.md`: fix.\n",
        encoding="utf-8",
    )
    (work_item_stage_root / "stage-result.md").write_text(
        "# Stage Result\n\n## Status\n\n- `succeeded`\n",
        encoding="utf-8",
    )
    (work_item_stage_root / "validator-report.md").write_text(
        "# Validator Report\n\n## Result\n\n- Verdict: `pass`\n",
        encoding="utf-8",
    )
    run_result = HarnessAiddRunResult(
        command=("aidd", "run"),
        runtime_id="claude-code",
        work_item="WI-001",
        exit_code=1,
        stdout_text="",
        stderr_text="",
        duration_seconds=125.0,
        command_transcript=HarnessCommandTranscript(
            command="aidd run",
            exit_code=1,
            stdout_text="",
            stderr_text="",
            duration_seconds=125.0,
            timeout_seconds=5400.0,
        ),
        timeout_seconds=5400.0,
    )

    payload = build_stage_timing_payload(
        scenario=_scenario(),
        run_id="eval-run",
        runtime_id="claude-code",
        work_item="WI-001",
        workspace_root=workspace_root,
        total_duration_seconds=130.0,
        aidd_run_result=run_result,
    )
    markdown = render_stage_timing_markdown(payload)

    steps = payload["steps"]
    stages = payload["stages"]
    assert isinstance(steps, list)
    assert isinstance(stages, list)
    assert steps[2]["step"] == "run"
    assert steps[2]["duration_seconds"] == 125.0
    assert stages[0]["stage"] == "idea"
    assert stages[0]["attempts"][0]["runtime_seconds"] == 123.0
    assert stages[0]["attempts"][1]["runtime_seconds"] == 56.0
    assert "STRUCT-MISSING-REQUIRED-SECTION" in stages[0]["attempts"][1]["repair_reason"]
    assert stages[0]["terminal_docs_consistent"] is True
    assert "| `idea` | 1 | 123.000 | `success`/`0` | `False` | `repair-needed`" in markdown
    matrix = build_self_repair_matrix_payload(payload)
    assert matrix["matrix"][0]["stage"] == "idea"
    assert matrix["matrix"][0]["attempts_used"] == 2
    assert matrix["matrix"][0]["terminal_docs_consistent"] is True
    assert matrix["matrix"][0]["probes"][0]["probe_id"] == "idea-missing-headings"
    assert matrix["deterministic_probe_count"] >= 15
    matrix_markdown = render_self_repair_matrix_markdown(matrix)
    assert "## Deterministic Probe Coverage" in matrix_markdown
    assert "`idea-placeholder-content`" in matrix_markdown


def test_stage_timing_marks_terminal_doc_mismatch(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_root = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-001"
        / "run-20260426T100000Z"
        / "stages"
        / "plan"
    )
    stage_root.mkdir(parents=True)
    (stage_root / "stage-metadata.json").write_text(
        json.dumps(
            {
                "status": "failed",
                "status_history": [
                    {"status": "executing", "changed_at_utc": "2026-04-26T10:00:00Z"},
                    {"status": "validating", "changed_at_utc": "2026-04-26T10:01:00Z"},
                    {"status": "failed", "changed_at_utc": "2026-04-26T10:01:01Z"},
                ],
            }
        ),
        encoding="utf-8",
    )
    work_item_stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    work_item_stage_root.mkdir(parents=True)
    (work_item_stage_root / "stage-result.md").write_text(
        "# Stage Result\n\n## Status\n\n- `succeeded`\n\n"
        "## Validation summary\n\n- Validator verdict: `pass`\n",
        encoding="utf-8",
    )
    (work_item_stage_root / "validator-report.md").write_text(
        "# Validator Report\n\n"
        "## Semantic checks\n\n"
        "- `SEM-PLACEHOLDER-CONTENT` (`high`) in `plan.md`: fix.\n\n"
        "## Result\n\n- Verdict: `fail`\n- Repair required for progression: yes\n",
        encoding="utf-8",
    )
    (work_item_stage_root / "repair-brief.md").write_text(
        "# Failed checks\n\n- fix\n",
        encoding="utf-8",
    )

    payload = build_stage_timing_payload(
        scenario=_scenario(),
        run_id="eval-run",
        runtime_id="claude-code",
        work_item="WI-001",
        workspace_root=workspace_root,
        total_duration_seconds=65.0,
    )

    stages = payload["stages"]
    assert isinstance(stages, list)
    plan_stage = next(item for item in stages if item["stage"] == "plan")
    assert plan_stage["terminal_docs_consistent"] is False
    assert plan_stage["final_failure_code"] == "SEM-PLACEHOLDER-CONTENT"

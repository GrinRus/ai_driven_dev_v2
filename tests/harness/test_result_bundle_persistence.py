from __future__ import annotations

import json
from pathlib import Path

from aidd.harness.result_bundle import (
    build_result_bundle_layout,
    write_command_transcripts,
    write_harness_metadata,
)
from aidd.harness.runner import (
    HarnessAiddRunResult,
    HarnessCommandTranscript,
    HarnessSetupResult,
    HarnessTeardownResult,
    HarnessVerificationResult,
)
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _build_scenario() -> Scenario:
    return Scenario(
        scenario_id="AIDD-TEST-BUNDLE-PERSISTENCE",
        scenario_class="deterministic-workflow",
        feature_size="small",
        automation_lane="ci",
        canonical_runtime="generic-cli",
        task="Persist bundle artifacts",
        repo=ScenarioRepoSource(
            url="https://github.com/example/repo",
            default_branch="main",
            revision=None,
        ),
        setup=ScenarioCommandSteps(commands=("echo setup",)),
        run=ScenarioRunConfig(
            stage_start="plan",
            stage_end="qa",
            runtime_targets=("generic-cli",),
            patch_budget_files=3,
            timeout_minutes=10,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=("echo verify",)),
        feature_source=None,
        quality=None,
        runtime_targets=("generic-cli",),
        is_live=False,
        raw={"id": "AIDD-TEST-BUNDLE-PERSISTENCE"},
    )


def _build_transcript(*, command: str, exit_code: int = 0) -> HarnessCommandTranscript:
    return HarnessCommandTranscript(
        command=command,
        exit_code=exit_code,
        stdout_text=f"stdout:{command}",
        stderr_text=f"stderr:{command}",
        duration_seconds=0.25,
    )


def test_write_harness_metadata_persists_references(tmp_path: Path) -> None:
    layout = build_result_bundle_layout(workspace_root=tmp_path, run_id="eval-run-100")
    scenario = _build_scenario()
    aidd_run_result = HarnessAiddRunResult(
        command=("uv", "run", "aidd", "run", "--work-item", "WI-100", "--runtime", "generic-cli"),
        runtime_id="generic-cli",
        work_item="WI-100",
        exit_code=0,
        stdout_text="ok",
        stderr_text="",
        duration_seconds=1.5,
        command_transcript=_build_transcript(command="uv run aidd run --work-item WI-100"),
    )

    metadata_path = write_harness_metadata(
        layout=layout,
        scenario=scenario,
        runtime_id="generic-cli",
        work_item="WI-100",
        status="pass",
        aidd_run_id="run-100",
        aidd_run_result=aidd_run_result,
        aidd_artifact_references={
            "stage_result": "reports/runs/WI-100/run-100/stages/qa/stage-result.md",
            "runtime_log": (
                "reports/runs/WI-100/run-100/stages/qa/attempts/attempt-0001/runtime.log"
            ),
        },
    )

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["scenario_id"] == "AIDD-TEST-BUNDLE-PERSISTENCE"
    assert payload["scenario_class"] == "deterministic-workflow"
    assert payload["feature_size"] == "small"
    assert payload["automation_lane"] == "ci"
    assert payload["canonical_runtime"] == "generic-cli"
    assert payload["runtime_id"] == "generic-cli"
    assert payload["work_item"] == "WI-100"
    assert payload["aidd_run_id"] == "run-100"
    assert payload["aidd_run"]["exit_code"] == 0
    assert payload["aidd_artifact_references"]["stage_result"].endswith("stage-result.md")


def test_write_command_transcripts_persists_all_step_transcripts(tmp_path: Path) -> None:
    layout = build_result_bundle_layout(workspace_root=tmp_path, run_id="eval-run-101")
    setup_result = HarnessSetupResult(
        executed_commands=("echo setup",),
        command_transcripts=(_build_transcript(command="echo setup"),),
        duration_seconds=0.25,
    )
    aidd_run_result = HarnessAiddRunResult(
        command=("uv", "run", "aidd", "run", "--work-item", "WI-101", "--runtime", "generic-cli"),
        runtime_id="generic-cli",
        work_item="WI-101",
        exit_code=0,
        stdout_text="run-ok",
        stderr_text="",
        duration_seconds=1.0,
        command_transcript=_build_transcript(
            command="uv run aidd run --work-item WI-101 --runtime generic-cli"
        ),
    )
    verification_result = HarnessVerificationResult(
        executed_commands=("echo verify",),
        aidd_exit_code=0,
        command_transcripts=(_build_transcript(command="echo verify"),),
        duration_seconds=0.25,
    )
    teardown_result = HarnessTeardownResult(
        executed_commands=("echo teardown",),
        command_transcripts=(_build_transcript(command="echo teardown"),),
        duration_seconds=0.25,
    )

    install_path, setup_path, run_path, verify_path, quality_path, teardown_path = (
        write_command_transcripts(
            layout=layout,
            setup_result=setup_result,
            aidd_run_result=aidd_run_result,
            verification_result=verification_result,
            teardown_result=teardown_result,
        )
    )

    install_payload = json.loads(install_path.read_text(encoding="utf-8"))
    setup_payload = json.loads(setup_path.read_text(encoding="utf-8"))
    run_payload = json.loads(run_path.read_text(encoding="utf-8"))
    verify_payload = json.loads(verify_path.read_text(encoding="utf-8"))
    teardown_payload = json.loads(teardown_path.read_text(encoding="utf-8"))

    assert install_payload["step"] == "install"
    assert install_payload["command_count"] == 0
    assert setup_payload["step"] == "setup"
    assert setup_payload["command_count"] == 1
    assert run_payload["step"] == "run"
    assert run_payload["exit_code"] == 0
    assert verify_payload["step"] == "verify"
    assert verify_payload["command_count"] == 1
    assert json.loads(quality_path.read_text(encoding="utf-8"))["step"] == "quality"
    assert teardown_payload["step"] == "teardown"
    assert teardown_payload["command_count"] == 1

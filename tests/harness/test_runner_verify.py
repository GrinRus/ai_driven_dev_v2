from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.runner import (
    HarnessAiddRunResult,
    HarnessCommandTranscript,
    HarnessVerificationError,
    run_verification_steps,
)
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _build_scenario(*, verify_commands: tuple[str, ...]) -> Scenario:
    return Scenario(
        scenario_id="AIDD-TEST-RUNNER-VERIFY",
        scenario_class="deterministic-workflow",
        feature_size="small",
        automation_lane="ci",
        canonical_runtime="generic-cli",
        task="Run verify commands",
        repo=ScenarioRepoSource(
            url="https://github.com/example/repo",
            default_branch="main",
            revision=None,
        ),
        setup=ScenarioCommandSteps(commands=("echo setup",)),
        run=ScenarioRunConfig(
            stage_start=None,
            stage_end=None,
            runtime_targets=("generic-cli",),
            patch_budget_files=None,
            timeout_minutes=None,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=verify_commands),
        feature_source=None,
        quality=None,
        runtime_targets=("generic-cli",),
        is_live=False,
        raw={"id": "AIDD-TEST-RUNNER-VERIFY"},
    )


def _build_aidd_run_result(*, exit_code: int) -> HarnessAiddRunResult:
    return HarnessAiddRunResult(
        command=("uv", "run", "aidd", "run", "--work-item", "WI-001", "--runtime", "generic-cli"),
        runtime_id="generic-cli",
        work_item="WI-001",
        exit_code=exit_code,
        stdout_text="stdout",
        stderr_text="stderr",
        duration_seconds=0.01,
        command_transcript=HarnessCommandTranscript(
            command="uv run aidd run --work-item WI-001 --runtime generic-cli",
            exit_code=exit_code,
            stdout_text="stdout",
            stderr_text="stderr",
            duration_seconds=0.01,
        ),
    )


def test_run_verification_steps_executes_commands_after_aidd_run(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    scenario = _build_scenario(
        verify_commands=(
            "printf '%s\\n' \"$AIDD_HARNESS_AIDD_EXIT_CODE\" > verify-exit-code.txt",
            "printf 'verified\\n' > verify.log",
        )
    )

    result = run_verification_steps(
        scenario=scenario,
        working_copy_path=working_copy_path,
        aidd_run_result=_build_aidd_run_result(exit_code=0),
    )

    assert result.executed_commands == scenario.verify.commands
    assert result.aidd_exit_code == 0
    assert len(result.command_transcripts) == 2
    assert result.command_transcripts[0].command == scenario.verify.commands[0]
    assert result.command_transcripts[0].exit_code == 0
    assert result.duration_seconds >= 0
    assert (working_copy_path / "verify-exit-code.txt").read_text(encoding="utf-8") == "0\n"
    assert (working_copy_path / "verify.log").read_text(encoding="utf-8") == "verified\n"


def test_run_verification_steps_stops_after_first_failing_command(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    scenario = _build_scenario(
        verify_commands=(
            "printf 'before\\n' > before.txt",
            "exit 9",
            "printf 'must-not-run\\n' > after.txt",
        )
    )

    with pytest.raises(
        HarnessVerificationError,
        match=r"Verification command failed with non-zero exit \(9\): exit 9",
    ):
        run_verification_steps(
            scenario=scenario,
            working_copy_path=working_copy_path,
            aidd_run_result=_build_aidd_run_result(exit_code=3),
        )

    assert (working_copy_path / "before.txt").exists()
    assert not (working_copy_path / "after.txt").exists()

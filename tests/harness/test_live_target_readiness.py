from __future__ import annotations

import os
from pathlib import Path

import pytest

from aidd.harness.live_target_readiness import (
    LiveTargetReadinessError,
    run_live_target_readiness,
    select_target_readiness_commands,
)
from aidd.harness.scenarios import ScenarioAuthoredTask


def _task(*commands: str) -> ScenarioAuthoredTask:
    return ScenarioAuthoredTask(
        task_id="TASK-1",
        title="target readiness",
        summary="Exercise provider-free target readiness.",
        intent="Detect target setup failures before provider allocation.",
        target_change="No product change in the readiness fixture.",
        expected_scope="Fixture only.",
        acceptance_criteria=("Readiness is classified.",),
        verification=commands,
        quality_bar="The signal is deterministic.",
        size_rationale="Small fixture.",
        interview=tuple(),
    )


def test_target_readiness_runs_authored_smoke_and_defers_aidd_artifacts(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "node_modules" / ".bin" / "verify"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    task = _task(
        "./node_modules/.bin/verify --smoke",
        "test -f .aidd/workitems/WI/stages/qa/output/stage-result.md",
    )

    result = run_live_target_readiness(
        task=task,
        working_copy_path=tmp_path,
        environment=dict(os.environ),
        timeout_seconds=5.0,
    )

    assert result.classification == "pass"
    assert result.smoke_commands == ("./node_modules/.bin/verify --smoke",)
    assert result.deferred_artifact_commands == (
        "test -f .aidd/workitems/WI/stages/qa/output/stage-result.md",
    )
    assert result.prerequisites[0].exists is True
    assert result.prerequisites[0].executable is True
    assert result.command_transcripts[0].exit_code == 0


def test_target_readiness_classifies_missing_generated_executable(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        LiveTargetReadinessError,
        match="prerequisite is unavailable",
    ) as raised:
        run_live_target_readiness(
            task=_task("./generated/bin/native-check --smoke"),
            working_copy_path=tmp_path,
            environment=dict(os.environ),
            timeout_seconds=5.0,
        )

    assert raised.value.result.classification == "target-setup"
    assert raised.value.result.prerequisites[0].exists is False
    assert raised.value.result.command_transcripts == tuple()


def test_target_readiness_detects_missing_optional_dependency_before_provider(
    tmp_path: Path,
) -> None:
    command = (
        "python -c 'import importlib.util; "
        "raise SystemExit(0 if importlib.util.find_spec(\"missing_optional_dep\") else 7)'"
    )

    with pytest.raises(LiveTargetReadinessError) as raised:
        run_live_target_readiness(
            task=_task(command),
            working_copy_path=tmp_path,
            environment=dict(os.environ),
            timeout_seconds=5.0,
        )

    assert raised.value.result.classification == "target-setup"
    assert raised.value.result.command_transcripts[0].exit_code == 7
    assert command in str(raised.value)


def test_target_readiness_uses_one_bounded_lifecycle_budget(tmp_path: Path) -> None:
    with pytest.raises(LiveTargetReadinessError) as raised:
        run_live_target_readiness(
            task=_task("sleep 1"),
            working_copy_path=tmp_path,
            environment=dict(os.environ),
            timeout_seconds=0.01,
        )

    transcript = raised.value.result.command_transcripts[0]
    assert transcript.exit_code == 124
    assert transcript.timed_out is True
    assert transcript.timeout_seconds is not None
    assert transcript.timeout_seconds <= 0.01


def test_target_readiness_rejects_artifact_only_verification() -> None:
    smoke, deferred = select_target_readiness_commands(
        _task("test -f .aidd/workitems/WI/stages/qa/output/validator-report.md")
    )

    assert smoke == tuple()
    assert deferred

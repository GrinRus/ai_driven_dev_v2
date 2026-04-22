from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.runner import HarnessSetupError, run_setup_steps
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _build_scenario(*, setup_commands: tuple[str, ...]) -> Scenario:
    return Scenario(
        scenario_id="AIDD-TEST-RUNNER-SETUP",
        task="Run setup commands",
        repo=ScenarioRepoSource(
            url="https://github.com/example/repo",
            default_branch="main",
            revision=None,
        ),
        setup=ScenarioCommandSteps(commands=setup_commands),
        run=ScenarioRunConfig(
            stage_start=None,
            stage_end=None,
            runtime_targets=("generic-cli",),
            patch_budget_files=None,
            timeout_minutes=None,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=("echo verify",)),
        runtime_targets=("generic-cli",),
        raw={"id": "AIDD-TEST-RUNNER-SETUP"},
    )


def test_run_setup_steps_executes_commands_in_order(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    scenario = _build_scenario(
        setup_commands=(
            "printf 'first\\n' > setup.log",
            "printf 'second\\n' >> setup.log",
        )
    )

    result = run_setup_steps(
        scenario=scenario,
        working_copy_path=working_copy_path,
    )

    assert result.executed_commands == scenario.setup.commands
    assert len(result.command_transcripts) == 2
    assert result.command_transcripts[0].command == scenario.setup.commands[0]
    assert result.command_transcripts[0].exit_code == 0
    assert result.duration_seconds >= 0
    assert (working_copy_path / "setup.log").read_text(encoding="utf-8") == "first\nsecond\n"


def test_run_setup_steps_stops_after_first_failing_command(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    scenario = _build_scenario(
        setup_commands=(
            "printf 'prepared\\n' > before.txt",
            "exit 7",
            "printf 'must-not-run\\n' > after.txt",
        )
    )

    with pytest.raises(
        HarnessSetupError,
        match=r"Setup command failed with non-zero exit \(7\): exit 7",
    ):
        run_setup_steps(
            scenario=scenario,
            working_copy_path=working_copy_path,
        )

    assert (working_copy_path / "before.txt").exists()
    assert not (working_copy_path / "after.txt").exists()

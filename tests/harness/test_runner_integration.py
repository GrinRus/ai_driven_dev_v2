from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.runner import (
    HarnessSetupError,
    HarnessVerificationError,
    invoke_aidd_run,
    run_setup_steps,
    run_verification_steps,
    run_with_teardown,
)
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _build_scenario(
    *,
    setup_commands: tuple[str, ...],
    verify_commands: tuple[str, ...],
) -> Scenario:
    return Scenario(
        scenario_id="AIDD-TEST-RUNNER-INTEGRATION",
        task="Exercise harness lifecycle",
        repo=ScenarioRepoSource(
            url="https://github.com/example/repo",
            default_branch="main",
            revision=None,
        ),
        setup=ScenarioCommandSteps(commands=setup_commands),
        run=ScenarioRunConfig(
            stage_start="plan",
            stage_end="qa",
            runtime_targets=("generic-cli",),
            patch_budget_files=3,
            timeout_minutes=5,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=verify_commands),
        feature_source=None,
        quality=None,
        runtime_targets=("generic-cli",),
        is_live=False,
        raw={"id": "AIDD-TEST-RUNNER-INTEGRATION"},
    )


def _write_fake_aidd(path: Path, *, exit_code: int) -> None:
    path.write_text(
        "\n".join(
            (
                "#!/bin/sh",
                "printf 'fake aidd\\n'",
                f"exit {exit_code}",
            )
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_harness_lifecycle_pass_path_runs_teardown(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(fake_aidd, exit_code=0)
    scenario = _build_scenario(
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
    )

    def _action() -> tuple[object, object, object]:
        setup_result = run_setup_steps(
            scenario=scenario,
            working_copy_path=working_copy_path,
        )
        aidd_result = invoke_aidd_run(
            scenario=scenario,
            working_copy_path=working_copy_path,
            runtime_id="generic-cli",
            work_item="WI-700",
            aidd_command=(fake_aidd.as_posix(),),
        )
        verify_result = run_verification_steps(
            scenario=scenario,
            working_copy_path=working_copy_path,
            aidd_run_result=aidd_result,
        )
        return setup_result, aidd_result, verify_result

    (_setup_result, _aidd_result, _verify_result), teardown_result = run_with_teardown(
        action=_action,
        teardown_commands=("printf 'teardown\\n' > teardown.log",),
        working_copy_path=working_copy_path,
    )

    assert teardown_result.executed_commands == ("printf 'teardown\\n' > teardown.log",)
    assert (working_copy_path / "setup.log").read_text(encoding="utf-8") == "setup\n"
    assert (working_copy_path / "verify.log").read_text(encoding="utf-8") == "verify\n"
    assert (working_copy_path / "teardown.log").read_text(encoding="utf-8") == "teardown\n"


def test_harness_lifecycle_runs_teardown_when_setup_fails(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    scenario = _build_scenario(
        setup_commands=("exit 4",),
        verify_commands=("printf 'verify\\n' > verify.log",),
    )

    with pytest.raises(HarnessSetupError, match="Setup command failed"):
        run_with_teardown(
            action=lambda: run_setup_steps(
                scenario=scenario,
                working_copy_path=working_copy_path,
            ),
            teardown_commands=("printf 'teardown\\n' > teardown.log",),
            working_copy_path=working_copy_path,
        )

    assert (working_copy_path / "teardown.log").read_text(encoding="utf-8") == "teardown\n"
    assert not (working_copy_path / "verify.log").exists()


def test_harness_lifecycle_runs_teardown_when_verification_fails(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(fake_aidd, exit_code=0)
    scenario = _build_scenario(
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("exit 9",),
    )

    def _action() -> object:
        run_setup_steps(
            scenario=scenario,
            working_copy_path=working_copy_path,
        )
        aidd_result = invoke_aidd_run(
            scenario=scenario,
            working_copy_path=working_copy_path,
            runtime_id="generic-cli",
            work_item="WI-701",
            aidd_command=(fake_aidd.as_posix(),),
        )
        return run_verification_steps(
            scenario=scenario,
            working_copy_path=working_copy_path,
            aidd_run_result=aidd_result,
        )

    with pytest.raises(HarnessVerificationError, match="Verification command failed"):
        run_with_teardown(
            action=_action,
            teardown_commands=("printf 'teardown\\n' > teardown.log",),
            working_copy_path=working_copy_path,
        )

    assert (working_copy_path / "teardown.log").read_text(encoding="utf-8") == "teardown\n"


def test_harness_lifecycle_runs_teardown_for_interrupted_run(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)

    def _action() -> object:
        raise KeyboardInterrupt("interrupted")

    with pytest.raises(KeyboardInterrupt, match="interrupted"):
        run_with_teardown(
            action=_action,
            teardown_commands=("printf 'teardown\\n' > teardown.log",),
            working_copy_path=working_copy_path,
        )

    assert (working_copy_path / "teardown.log").read_text(encoding="utf-8") == "teardown\n"

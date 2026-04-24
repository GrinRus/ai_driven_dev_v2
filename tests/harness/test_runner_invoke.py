from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.runner import invoke_aidd_run
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _build_scenario(*, runtime_targets: tuple[str, ...]) -> Scenario:
    return Scenario(
        scenario_id="AIDD-TEST-RUNNER-INVOKE",
        scenario_class="deterministic-workflow",
        feature_size="small",
        automation_lane="ci",
        canonical_runtime="generic-cli",
        task="Run AIDD from harness",
        repo=ScenarioRepoSource(
            url="https://github.com/example/repo",
            default_branch="main",
            revision=None,
        ),
        setup=ScenarioCommandSteps(commands=("echo setup",)),
        run=ScenarioRunConfig(
            stage_start=None,
            stage_end=None,
            runtime_targets=runtime_targets,
            patch_budget_files=None,
            timeout_minutes=None,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=("echo verify",)),
        feature_source=None,
        quality=None,
        runtime_targets=runtime_targets,
        is_live=False,
        raw={"id": "AIDD-TEST-RUNNER-INVOKE"},
    )


def _write_fake_aidd(path: Path, *, exit_code: int) -> None:
    path.write_text(
        "\n".join(
            (
                "#!/bin/sh",
                "printf '%s\\n' \"$@\" > invoked-args.txt",
                "printf '%s\\n' \"$AIDD_HARNESS_SCENARIO_ID\" > invoked-scenario.txt",
                "printf '%s\\n' \"$AIDD_HARNESS_RUNTIME_ID\" > invoked-runtime.txt",
                "printf '%s\\n' \"$AIDD_HARNESS_WORK_ITEM\" > invoked-work-item.txt",
                "printf 'stdout from fake aidd\\n'",
                "printf 'stderr from fake aidd\\n' 1>&2",
                f"exit {exit_code}",
            )
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_invoke_aidd_run_executes_with_runtime_and_work_item(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(fake_aidd, exit_code=0)
    scenario = _build_scenario(runtime_targets=("generic-cli", "claude-code"))

    result = invoke_aidd_run(
        scenario=scenario,
        working_copy_path=working_copy_path,
        runtime_id="generic-cli",
        work_item="WI-123",
        aidd_command=(fake_aidd.as_posix(),),
    )

    assert result.command == (
        fake_aidd.as_posix(),
        "run",
        "--work-item",
        "WI-123",
        "--runtime",
        "generic-cli",
    )
    assert result.exit_code == 0
    assert "stdout from fake aidd" in result.stdout_text
    assert "stderr from fake aidd" in result.stderr_text
    assert result.duration_seconds >= 0
    assert result.command_transcript.command == " ".join(result.command)
    assert result.command_transcript.exit_code == 0
    assert (working_copy_path / "invoked-args.txt").read_text(encoding="utf-8").splitlines() == [
        "run",
        "--work-item",
        "WI-123",
        "--runtime",
        "generic-cli",
    ]
    assert (working_copy_path / "invoked-scenario.txt").read_text(encoding="utf-8").strip() == (
        "AIDD-TEST-RUNNER-INVOKE"
    )
    assert (
        (working_copy_path / "invoked-runtime.txt").read_text(encoding="utf-8").strip()
        == "generic-cli"
    )
    assert (
        (working_copy_path / "invoked-work-item.txt").read_text(encoding="utf-8").strip()
        == "WI-123"
    )


def test_invoke_aidd_run_includes_stage_bounds_when_requested(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(fake_aidd, exit_code=0)
    scenario = _build_scenario(runtime_targets=("generic-cli",))

    result = invoke_aidd_run(
        scenario=scenario,
        working_copy_path=working_copy_path,
        runtime_id="generic-cli",
        work_item="WI-124",
        aidd_command=(fake_aidd.as_posix(),),
        stage_start="idea",
        stage_end="qa",
    )

    assert result.command == (
        fake_aidd.as_posix(),
        "run",
        "--work-item",
        "WI-124",
        "--runtime",
        "generic-cli",
        "--from-stage",
        "idea",
        "--to-stage",
        "qa",
    )


def test_invoke_aidd_run_normalizes_config_path_to_absolute(tmp_path: Path, monkeypatch) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    fake_aidd = tmp_path / "fake-aidd"
    config_path = tmp_path / "configs" / "aidd.example.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("[workspace]\nroot = \".aidd\"\n", encoding="utf-8")
    _write_fake_aidd(fake_aidd, exit_code=0)
    scenario = _build_scenario(runtime_targets=("generic-cli",))
    monkeypatch.chdir(tmp_path)

    result = invoke_aidd_run(
        scenario=scenario,
        working_copy_path=working_copy_path,
        runtime_id="generic-cli",
        work_item="WI-125",
        aidd_command=(fake_aidd.as_posix(),),
        config_path=Path("configs/aidd.example.toml"),
    )

    assert result.command[-2:] == ("--config", config_path.as_posix())


def test_invoke_aidd_run_preserves_non_zero_exit(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(fake_aidd, exit_code=17)
    scenario = _build_scenario(runtime_targets=("generic-cli",))

    result = invoke_aidd_run(
        scenario=scenario,
        working_copy_path=working_copy_path,
        runtime_id="generic-cli",
        work_item="WI-555",
        aidd_command=(fake_aidd.as_posix(),),
    )

    assert result.exit_code == 17
    assert "stdout from fake aidd" in result.stdout_text
    assert "stderr from fake aidd" in result.stderr_text
    assert result.command_transcript.exit_code == 17


def test_invoke_aidd_run_rejects_unsupported_runtime(tmp_path: Path) -> None:
    working_copy_path = tmp_path / "working-copy"
    working_copy_path.mkdir(parents=True, exist_ok=True)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(fake_aidd, exit_code=0)
    scenario = _build_scenario(runtime_targets=("generic-cli",))

    with pytest.raises(ValueError, match="not allowed by scenario"):
        invoke_aidd_run(
            scenario=scenario,
            working_copy_path=working_copy_path,
            runtime_id="claude-code",
            work_item="WI-999",
            aidd_command=(fake_aidd.as_posix(),),
        )

    assert not (working_copy_path / "invoked-args.txt").exists()

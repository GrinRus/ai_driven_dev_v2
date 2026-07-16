from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aidd.harness.runner import run_setup_steps
from aidd.harness.scenarios import Scenario, load_scenario

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = REPO_ROOT / "harness" / "scenarios"
CI_SCENARIO_PATHS = tuple(
    path
    for path in sorted(SCENARIO_ROOT.rglob("*.yaml"))
    if load_scenario(path).automation_lane == "ci"
)
STAGE_ORDER = (
    "idea",
    "research",
    "plan",
    "review-spec",
    "tasklist",
    "implement",
    "review",
    "qa",
)


def _work_item(scenario: Scenario) -> str:
    invocation = scenario.raw.get("aidd_invocation")
    if isinstance(invocation, dict):
        value = invocation.get("work_item")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"WI-{scenario.scenario_id}"


def _run_cli(*, working_copy: Path, arguments: tuple[str, ...]) -> None:
    completed = subprocess.run(
        (sys.executable, "-m", "aidd.cli.main", *arguments),
        cwd=working_copy,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, (
        f"command failed: {' '.join(arguments)}\n"
        f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )


def _bootstrap_work_item(*, scenario: Scenario, working_copy: Path, work_item: str) -> None:
    user_request_path = working_copy / ".aidd/workitems" / work_item / "context/user-request.md"
    if user_request_path.exists():
        return
    _run_cli(
        working_copy=working_copy,
        arguments=(
            "init",
            "--work-item",
            work_item,
            "--request",
            scenario.task,
        ),
    )


def _execute_scenario(*, scenario: Scenario, working_copy: Path, work_item: str) -> None:
    common = (
        "--work-item",
        work_item,
        "--runtime",
        "generic-cli",
        "--config",
        "aidd.example.toml",
    )
    if scenario.scenario_class == "deterministic-stage":
        stage = scenario.run.stage_start
        stage_index = STAGE_ORDER.index(stage)
        if stage_index:
            _run_cli(
                working_copy=working_copy,
                arguments=(
                    "run",
                    *common,
                    "--from-stage",
                    "idea",
                    "--to-stage",
                    STAGE_ORDER[stage_index - 1],
                ),
            )
        _run_cli(
            working_copy=working_copy,
            arguments=("stage", "run", stage, *common),
        )
        return
    _run_cli(
        working_copy=working_copy,
        arguments=(
            "run",
            *common,
            "--from-stage",
            scenario.run.stage_start,
            "--to-stage",
            scenario.run.stage_end,
        ),
    )


def _verify_scenario(*, scenario: Scenario, working_copy: Path) -> None:
    for command in scenario.verify.commands:
        completed = subprocess.run(
            ("/bin/sh", "-c", command),
            cwd=working_copy,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, (
            f"verification failed: {command}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )


@pytest.mark.parametrize(
    "scenario_path",
    CI_SCENARIO_PATHS,
    ids=lambda path: path.stem,
)
def test_ci_manifest_executes_from_fresh_fixture(
    scenario_path: Path,
    tmp_path: Path,
) -> None:
    scenario = load_scenario(scenario_path, runtime_id="generic-cli")
    assert scenario.feature_source is not None
    fixture_path = REPO_ROOT / str(scenario.feature_source.fixture_path)
    working_copy = tmp_path / scenario.scenario_id
    shutil.copytree(fixture_path, working_copy)

    run_setup_steps(scenario=scenario, working_copy_path=working_copy)
    work_item = _work_item(scenario)
    _bootstrap_work_item(
        scenario=scenario,
        working_copy=working_copy,
        work_item=work_item,
    )
    _execute_scenario(
        scenario=scenario,
        working_copy=working_copy,
        work_item=work_item,
    )
    _verify_scenario(scenario=scenario, working_copy=working_copy)

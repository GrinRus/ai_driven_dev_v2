from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from aidd.harness.ci_scenario_lane import (
    CiScenarioDiscoveryError,
    discover_ci_scenarios,
    execute_ci_scenario_lane,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = REPO_ROOT / "harness/scenarios"
EXPECTED_CI_IDS = (
    "AIDD-DETERMINISTIC-001",
    "AIDD-DETERMINISTIC-003",
    "AIDD-DETERMINISTIC-004",
    "AIDD-SMOKE-001",
    "AIDD-STAGEPACK-PLAN-SMOKE-001",
)


def test_discover_ci_scenarios_returns_all_and_only_ci_manifests() -> None:
    discovered = discover_ci_scenarios(SCENARIO_ROOT)

    assert tuple(item.scenario_id for item in discovered) == EXPECTED_CI_IDS
    assert all(item.path.suffix == ".yaml" for item in discovered)


def test_discover_ci_scenarios_rejects_duplicate_ids(tmp_path: Path) -> None:
    source = SCENARIO_ROOT / "smoke/plan-stage-minimal-fixture.yaml"
    shutil.copy(source, tmp_path / "one.yaml")
    shutil.copy(source, tmp_path / "two.yaml")

    with pytest.raises(CiScenarioDiscoveryError, match="AIDD-SMOKE-001"):
        discover_ci_scenarios(tmp_path)


def test_ci_lane_attempts_every_discovered_scenario_after_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def _run(
        command: tuple[str, ...],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        scenario_path = Path(command[-3])
        exit_code = 1 if scenario_path.stem == "minimal-python-bounded-workflow" else 0
        return subprocess.CompletedProcess(
            command,
            exit_code,
            stdout=f"executed {scenario_path.stem}\n",
            stderr="",
        )

    monkeypatch.setattr("aidd.harness.ci_scenario_lane.subprocess.run", _run)

    result = execute_ci_scenario_lane(
        scenario_root=SCENARIO_ROOT,
        workspace_root=tmp_path / ".aidd-ci",
        aidd_command=("aidd",),
    )

    assert result.discovered_ids == EXPECTED_CI_IDS
    assert result.executed_ids == EXPECTED_CI_IDS
    assert len(calls) == len(EXPECTED_CI_IDS)
    assert not result.succeeded
    assert all(command[1:3] == ("eval", "execute") for command in calls)


def test_ci_workflow_runs_the_standalone_lane() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "deterministic-scenarios:" in workflow
    assert 'python-version: "3.12"' in workflow
    assert "python scripts/run_ci_scenarios.py --root .aidd-ci" in workflow
    assert "timeout-minutes: 20" in workflow


def test_ci_workflow_runs_packaged_javascript_syntax_gate() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "Packaged JavaScript syntax" in workflow
    assert "python scripts/check_packaged_javascript.py" in workflow
    assert "Packaged JavaScript DOM state" in workflow
    assert "node --test tests/frontend/*.test.mjs" in workflow

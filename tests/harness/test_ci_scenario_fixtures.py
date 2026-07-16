from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.deterministic_eval import (
    DeterministicEvalRequest,
    execute_deterministic_eval,
)
from aidd.harness.scenarios import load_scenario

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = REPO_ROOT / "harness" / "scenarios"
CI_SCENARIO_PATHS = tuple(
    path
    for path in sorted(SCENARIO_ROOT.rglob("*.yaml"))
    if load_scenario(path).automation_lane == "ci"
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
    result = execute_deterministic_eval(
        DeterministicEvalRequest(
            scenario_path=scenario_path,
            workspace_root=tmp_path / ".aidd",
        )
    )

    assert result.status == "pass"
    assert result.bundle_root.is_dir()
    assert result.verdict_path.is_file()

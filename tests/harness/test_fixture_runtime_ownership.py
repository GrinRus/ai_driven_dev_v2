from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from aidd.core.stages import STAGES

FIXTURE_RUNTIME = (
    Path(__file__).resolve().parents[2] / "harness/fixtures/minimal-python/aidd_fixture_runtime.py"
)


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("attempt_mode", ("initial", "repair"))
def test_fixture_runtime_preserves_workflow_and_operator_records(
    tmp_path: Path, stage: str, attempt_mode: str
) -> None:
    workspace = tmp_path / ".aidd"
    stage_root = workspace / "workitems/WI-OWNERSHIP/stages" / stage
    stage_root.mkdir(parents=True)
    (tmp_path / "src/minimal_app").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    protected = {
        name: f"Retained {name}; attempt={attempt_mode}\n".encode()
        for name in (
            "stage-result.md",
            "validator-report.md",
            "repair-brief.md",
            "questions.md",
            "answers.md",
        )
    }
    for name, content in protected.items():
        (stage_root / name).write_bytes(content)

    result = subprocess.run(
        [sys.executable, "-B", str(FIXTURE_RUNTIME)],
        cwd=tmp_path,
        env={
            **os.environ,
            "AIDD_STAGE": stage,
            "AIDD_WORKSPACE_ROOT": str(workspace),
            "AIDD_WORK_ITEM": "WI-OWNERSHIP",
            "AIDD_ATTEMPT_MODE": attempt_mode,
        },
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert f"fixture-runtime stage={stage}" in result.stdout
    assert {name: (stage_root / name).read_bytes() for name in protected} == protected
    runtime_outputs = [path for path in stage_root.glob("*.md") if path.name not in protected]
    assert len(runtime_outputs) == 1
    assert runtime_outputs[0].read_text(encoding="utf-8").strip()

from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.run_store import (
    RUN_ATTEMPTS_DIRNAME,
    RUN_STAGES_DIRNAME,
    RunStore,
    format_attempt_directory_name,
    run_attempt_root,
    run_root,
    run_stage_root,
    run_stages_root,
    run_store_root,
    work_item_runs_root,
)
from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME, WORKSPACE_REPORTS_RUNS_DIRNAME


def test_run_store_root_uses_reports_runs_layout(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    assert run_store_root(workspace_root) == (
        workspace_root / WORKSPACE_REPORTS_DIRNAME / WORKSPACE_REPORTS_RUNS_DIRNAME
    )


def test_run_directory_layout_includes_stage_and_attempt_subdirectories(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-001"
    run_id = "run-001"
    stage = "plan"

    expected_work_item_root = run_store_root(workspace_root) / work_item
    expected_run_root = expected_work_item_root / run_id
    expected_stages_root = expected_run_root / RUN_STAGES_DIRNAME
    expected_stage_root = expected_stages_root / stage

    assert work_item_runs_root(workspace_root, work_item) == expected_work_item_root
    assert run_root(workspace_root, work_item, run_id) == expected_run_root
    assert run_stages_root(workspace_root, work_item, run_id) == expected_stages_root
    assert run_stage_root(workspace_root, work_item, run_id, stage) == expected_stage_root
    assert run_attempt_root(workspace_root, work_item, run_id, stage, 3) == (
        expected_stage_root / RUN_ATTEMPTS_DIRNAME / "attempt-0003"
    )


def test_format_attempt_directory_name_rejects_non_positive_numbers() -> None:
    with pytest.raises(ValueError, match=">= 1"):
        format_attempt_directory_name(0)


def test_run_store_dataclass_root_matches_helper(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    store = RunStore(workspace_root=workspace_root, work_item="WI-001", run_id="run-001")

    assert store.root == run_root(workspace_root, "WI-001", "run-001")

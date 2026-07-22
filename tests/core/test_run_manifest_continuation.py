from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.core.run_store import create_run_manifest, persist_stage_status


def _create_unbounded_run(workspace_root: Path) -> Path:
    return create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-STEPWISE",
        run_id="run-stepwise",
        runtime_id="generic-cli",
        stage_target="idea",
        config_snapshot={"runtime_command": "runtime"},
    )


def _mark_succeeded(workspace_root: Path, stage: str) -> None:
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-STEPWISE",
        run_id="run-stepwise",
        stage=stage,
        status="succeeded",
    )


def _continue_manifest(workspace_root: Path, stage: str) -> Path:
    return create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-STEPWISE",
        run_id="run-stepwise",
        runtime_id="generic-cli",
        stage_target=stage,
        config_snapshot={"runtime_command": "runtime"},
    )


def test_unbounded_run_accepts_canonical_stepwise_progression(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    manifest_path = _create_unbounded_run(workspace_root)
    _mark_succeeded(workspace_root, "idea")

    research_manifest = _continue_manifest(workspace_root, "research")
    _mark_succeeded(workspace_root, "research")
    plan_manifest = _continue_manifest(workspace_root, "plan")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert research_manifest == manifest_path
    assert plan_manifest == manifest_path
    assert payload["stage_target"] == "idea"
    assert payload["workflow_bounds"] == {"start": None, "end": None}


@pytest.mark.parametrize("status", ("preparing", "executing", "blocked", "failed"))
def test_unbounded_run_rejects_next_stage_until_current_stage_succeeds(
    tmp_path: Path,
    status: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    manifest_path = _create_unbounded_run(workspace_root)
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-STEPWISE",
        run_id="run-stepwise",
        stage="idea",
        status=status,
    )
    before = manifest_path.read_bytes()

    with pytest.raises(ValueError, match="stage_target"):
        _continue_manifest(workspace_root, "research")

    assert manifest_path.read_bytes() == before


def test_unbounded_run_rejects_skipped_and_backward_stage_reuse(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    manifest_path = _create_unbounded_run(workspace_root)
    _mark_succeeded(workspace_root, "idea")
    before = manifest_path.read_bytes()

    with pytest.raises(ValueError, match="stage_target"):
        _continue_manifest(workspace_root, "plan")

    assert manifest_path.read_bytes() == before

    backward_root = tmp_path / "backward" / ".aidd"
    create_run_manifest(
        workspace_root=backward_root,
        work_item="WI-STEPWISE",
        run_id="run-stepwise",
        runtime_id="generic-cli",
        stage_target="research",
        config_snapshot={"runtime_command": "runtime"},
    )
    with pytest.raises(ValueError, match="stage_target"):
        create_run_manifest(
            workspace_root=backward_root,
            work_item="WI-STEPWISE",
            run_id="run-stepwise",
            runtime_id="generic-cli",
            stage_target="idea",
            config_snapshot={"runtime_command": "runtime"},
        )


@pytest.mark.parametrize(
    ("runtime_id", "runtime_command", "expected"),
    (
        ("codex", "runtime", "runtime_id"),
        ("generic-cli", "other", "config_snapshot.runtime_command"),
    ),
)
def test_unbounded_continuation_preserves_runtime_and_config_identity(
    tmp_path: Path,
    runtime_id: str,
    runtime_command: str,
    expected: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    manifest_path = _create_unbounded_run(workspace_root)
    _mark_succeeded(workspace_root, "idea")
    before = manifest_path.read_bytes()

    with pytest.raises(ValueError, match=expected):
        create_run_manifest(
            workspace_root=workspace_root,
            work_item="WI-STEPWISE",
            run_id="run-stepwise",
            runtime_id=runtime_id,
            stage_target="research",
            config_snapshot={"runtime_command": runtime_command},
        )

    assert manifest_path.read_bytes() == before

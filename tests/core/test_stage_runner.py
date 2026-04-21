from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from aidd.core.run_store import create_run_manifest, run_attempt_artifact_index_path
from aidd.core.stage_runner import persist_execution_state, prepare_stage_bundle


def test_prepare_stage_bundle_resolves_expected_inputs_and_outputs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="implement",
    )

    assert bundle.stage == "implement"
    assert bundle.work_item == "WI-001"
    assert bundle.expected_input_bundle == (
        workspace_root / "workitems" / "WI-001" / "stages" / "tasklist" / "output" / "tasklist.md",
        workspace_root / "workitems" / "WI-001" / "context" / "repository-state.md",
    )
    assert bundle.expected_output_documents == (
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "implement"
        / "implementation-report.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "stage-result.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "validator-report.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "repair-brief.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "questions.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "answers.md",
    )


def test_prepare_stage_bundle_renders_stage_brief_with_relative_paths(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    content = bundle.stage_brief_markdown

    assert "# Stage" in content
    assert "\nplan\n" in content
    assert "# Expected input bundle" in content
    assert "`workitems/WI-001/stages/research/output/research-notes.md`" in content
    assert "# Expected output documents" in content
    assert "`workitems/WI-001/stages/plan/plan.md`" in content


def test_persist_execution_state_creates_attempt_and_sets_executing_status(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )

    assert execution_state.attempt_number == 1
    assert execution_state.attempt_path.name == "attempt-0001"
    assert run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    ).exists()
    stage_metadata_payload = json.loads(
        execution_state.stage_metadata_path.read_text(encoding="utf-8")
    )
    assert stage_metadata_payload["status"] == "executing"
    assert stage_metadata_payload["updated_at_utc"] == "2026-04-22T10:00:00Z"


def test_persist_execution_state_uses_monotonic_attempt_numbers(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    first = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    second = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert first.attempt_number == 1
    assert second.attempt_number == 2

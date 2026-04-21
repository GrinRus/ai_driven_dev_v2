from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aidd.core.run_store import (
    create_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_stage_metadata_path,
)
from aidd.core.stage_runner import (
    PostValidationAction,
    StageValidationState,
    ValidationVerdict,
    decide_post_validation_transition,
    persist_execution_state,
    persist_validation_state,
    prepare_stage_bundle,
)
from aidd.core.state_machine import StageState


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


@pytest.mark.parametrize(
    ("verdict", "expected_state"),
    (
        (ValidationVerdict.PASS, StageState.SUCCEEDED),
        (ValidationVerdict.REPAIR, StageState.REPAIR_NEEDED),
        (ValidationVerdict.BLOCKED, StageState.BLOCKED),
        (ValidationVerdict.FAIL, StageState.FAILED),
    ),
)
def test_persist_validation_state_persists_verdict_transition(
    tmp_path: Path,
    verdict: ValidationVerdict,
    expected_state: StageState,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=verdict,
        changed_at_utc=datetime(2026, 4, 22, 10, 5, tzinfo=UTC),
    )

    assert validation_state.verdict is verdict
    assert validation_state.next_state == expected_state
    stage_metadata_payload = json.loads(
        validation_state.stage_metadata_path.read_text(encoding="utf-8")
    )
    assert stage_metadata_payload["status"] == expected_state.value
    assert stage_metadata_payload["updated_at_utc"] == "2026-04-22T10:05:00Z"
    assert [entry["status"] for entry in stage_metadata_payload["status_history"]] == [
        "validating",
        expected_state.value,
    ]


def test_persist_validation_state_rejects_illegal_transition(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    with pytest.raises(ValueError, match="Illegal stage transition"):
        persist_validation_state(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            verdict=ValidationVerdict.PASS,
            from_state=StageState.PENDING,
        )

    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert not metadata_path.exists()


@pytest.mark.parametrize(
    ("verdict", "expected_state", "expected_action", "expected_terminal"),
    (
        (
            ValidationVerdict.PASS,
            StageState.SUCCEEDED,
            PostValidationAction.ADVANCE,
            True,
        ),
        (
            ValidationVerdict.REPAIR,
            StageState.REPAIR_NEEDED,
            PostValidationAction.REPAIR,
            False,
        ),
        (
            ValidationVerdict.BLOCKED,
            StageState.BLOCKED,
            PostValidationAction.WAIT,
            False,
        ),
        (
            ValidationVerdict.FAIL,
            StageState.FAILED,
            PostValidationAction.STOP,
            True,
        ),
    ),
)
def test_decide_post_validation_transition_maps_supported_outcomes(
    tmp_path: Path,
    verdict: ValidationVerdict,
    expected_state: StageState,
    expected_action: PostValidationAction,
    expected_terminal: bool,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=verdict,
    )

    transition = decide_post_validation_transition(validation_state)

    assert transition.next_state == expected_state
    assert transition.action == expected_action
    assert transition.is_terminal is expected_terminal
    assert transition.stage_metadata_path == validation_state.stage_metadata_path


def test_decide_post_validation_transition_rejects_unsupported_state() -> None:
    with pytest.raises(ValueError, match="Unsupported post-validation state"):
        decide_post_validation_transition(
            StageValidationState(
                stage="plan",
                work_item="WI-001",
                run_id="run-001",
                verdict=ValidationVerdict.PASS,
                next_state=StageState.VALIDATING,
                stage_metadata_path=Path("/tmp/stage-metadata.json"),
            )
        )

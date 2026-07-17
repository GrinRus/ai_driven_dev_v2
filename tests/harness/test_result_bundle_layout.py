from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.eval_preparation import derive_run_id
from aidd.harness.result_bundle import (
    EVENTS_JSONL_FILENAME,
    FEATURE_SELECTION_FILENAME,
    GRADER_FILENAME,
    HARNESS_METADATA_FILENAME,
    LOG_ANALYSIS_FILENAME,
    REPAIR_HISTORY_FILENAME,
    RUN_TRANSCRIPT_FILENAME,
    RUNTIME_JSONL_FILENAME,
    RUNTIME_LOG_FILENAME,
    SETUP_TRANSCRIPT_FILENAME,
    TEARDOWN_TRANSCRIPT_FILENAME,
    VALIDATOR_REPORT_FILENAME,
    VERDICT_FILENAME,
    VERIFY_TRANSCRIPT_FILENAME,
    build_result_bundle_layout,
    ensure_result_bundle_layout,
    ensure_result_bundle_layout_at_report_root,
)


def test_build_result_bundle_layout_uses_stable_artifact_names(tmp_path: Path) -> None:
    layout = build_result_bundle_layout(workspace_root=tmp_path, run_id="eval-run-001")

    expected_root = tmp_path / "reports" / "evals" / "eval-run-001"
    assert layout.run_root == expected_root
    assert layout.harness_metadata_path.name == HARNESS_METADATA_FILENAME
    assert layout.setup_transcript_path.name == SETUP_TRANSCRIPT_FILENAME
    assert layout.run_transcript_path.name == RUN_TRANSCRIPT_FILENAME
    assert layout.verify_transcript_path.name == VERIFY_TRANSCRIPT_FILENAME
    assert layout.teardown_transcript_path.name == TEARDOWN_TRANSCRIPT_FILENAME
    assert layout.feature_selection_path.name == FEATURE_SELECTION_FILENAME
    assert layout.runtime_log_path.name == RUNTIME_LOG_FILENAME
    assert layout.runtime_jsonl_path.name == RUNTIME_JSONL_FILENAME
    assert layout.events_jsonl_path.name == EVENTS_JSONL_FILENAME
    assert layout.validator_report_path.name == VALIDATOR_REPORT_FILENAME
    assert layout.repair_history_path.name == REPAIR_HISTORY_FILENAME
    assert layout.log_analysis_path.name == LOG_ANALYSIS_FILENAME
    assert layout.grader_path.name == GRADER_FILENAME
    assert layout.verdict_path.name == VERDICT_FILENAME


def test_ensure_result_bundle_layout_creates_run_directory(tmp_path: Path) -> None:
    layout = ensure_result_bundle_layout(workspace_root=tmp_path, run_id="eval-run-002")

    assert layout.run_root.exists()
    assert layout.run_root.is_dir()


@pytest.mark.parametrize(
    "run_id",
    ("", " ", ".", "..", "../escape", "/absolute", "nested/run", "nested\\run", "x" * 129),
)
def test_result_bundle_layout_rejects_unsafe_run_ids_without_partial_state(
    tmp_path: Path,
    run_id: str,
) -> None:
    with pytest.raises(ValueError, match="plain path component"):
        ensure_result_bundle_layout(workspace_root=tmp_path, run_id=run_id)

    assert not (tmp_path / "reports").exists()


@pytest.mark.parametrize(
    ("scenario_id", "runtime_id"),
    (("../scenario", "codex"), ("AIDD-SCENARIO", "../runtime"), ("x" * 129, "codex")),
)
def test_derive_run_id_rejects_unsafe_source_identifiers(
    scenario_id: str,
    runtime_id: str,
) -> None:
    with pytest.raises(ValueError, match="plain path component"):
        derive_run_id(scenario_id=scenario_id, runtime_id=runtime_id)


def test_result_bundle_layout_rejects_workspace_symlink_escape(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    outside_root = tmp_path / "outside"
    workspace_root.mkdir()
    outside_root.mkdir()
    (workspace_root / "reports").symlink_to(outside_root, target_is_directory=True)

    with pytest.raises(ValueError, match="owning root must stay inside"):
        ensure_result_bundle_layout(workspace_root=workspace_root, run_id="eval-run")

    assert not (outside_root / "evals" / "eval-run").exists()


def test_explicit_report_root_rejects_run_symlink_escape(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    outside_root = tmp_path / "outside"
    report_root.mkdir()
    outside_root.mkdir()
    (report_root / "eval-run").symlink_to(outside_root, target_is_directory=True)

    with pytest.raises(ValueError, match="resolve directly below"):
        ensure_result_bundle_layout_at_report_root(
            report_root=report_root,
            run_id="eval-run",
        )

    assert tuple(outside_root.iterdir()) == ()

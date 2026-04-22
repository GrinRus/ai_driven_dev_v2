from __future__ import annotations

from pathlib import Path

import pytest

from aidd.harness.result_bundle import (
    EVENTS_JSONL_FILENAME,
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


def test_build_result_bundle_layout_rejects_empty_run_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="run_id must be non-empty"):
        build_result_bundle_layout(workspace_root=tmp_path, run_id="   ")

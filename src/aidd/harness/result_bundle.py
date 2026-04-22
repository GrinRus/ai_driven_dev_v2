from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME, WORKSPACE_REPORTS_EVALS_DIRNAME

RUNTIME_LOG_FILENAME = "runtime.log"
RUNTIME_JSONL_FILENAME = "runtime.jsonl"
EVENTS_JSONL_FILENAME = "events.jsonl"
VALIDATOR_REPORT_FILENAME = "validator-report.md"
REPAIR_HISTORY_FILENAME = "repair-history.md"
LOG_ANALYSIS_FILENAME = "log-analysis.md"
GRADER_FILENAME = "grader.json"
VERDICT_FILENAME = "verdict.md"
HARNESS_METADATA_FILENAME = "harness-metadata.json"
SETUP_TRANSCRIPT_FILENAME = "setup-transcript.json"
RUN_TRANSCRIPT_FILENAME = "run-transcript.json"
VERIFY_TRANSCRIPT_FILENAME = "verify-transcript.json"
TEARDOWN_TRANSCRIPT_FILENAME = "teardown-transcript.json"


@dataclass(frozen=True, slots=True)
class ResultBundleLayout:
    run_root: Path
    harness_metadata_path: Path
    setup_transcript_path: Path
    run_transcript_path: Path
    verify_transcript_path: Path
    teardown_transcript_path: Path
    runtime_log_path: Path
    runtime_jsonl_path: Path
    events_jsonl_path: Path
    validator_report_path: Path
    repair_history_path: Path
    log_analysis_path: Path
    grader_path: Path
    verdict_path: Path


def _validate_run_id(run_id: str) -> str:
    normalized = run_id.strip()
    if not normalized:
        raise ValueError("run_id must be non-empty.")
    return normalized


def build_result_bundle_layout(*, workspace_root: Path, run_id: str) -> ResultBundleLayout:
    normalized_run_id = _validate_run_id(run_id)
    run_root = (
        workspace_root
        / WORKSPACE_REPORTS_DIRNAME
        / WORKSPACE_REPORTS_EVALS_DIRNAME
        / normalized_run_id
    )
    return ResultBundleLayout(
        run_root=run_root,
        harness_metadata_path=run_root / HARNESS_METADATA_FILENAME,
        setup_transcript_path=run_root / SETUP_TRANSCRIPT_FILENAME,
        run_transcript_path=run_root / RUN_TRANSCRIPT_FILENAME,
        verify_transcript_path=run_root / VERIFY_TRANSCRIPT_FILENAME,
        teardown_transcript_path=run_root / TEARDOWN_TRANSCRIPT_FILENAME,
        runtime_log_path=run_root / RUNTIME_LOG_FILENAME,
        runtime_jsonl_path=run_root / RUNTIME_JSONL_FILENAME,
        events_jsonl_path=run_root / EVENTS_JSONL_FILENAME,
        validator_report_path=run_root / VALIDATOR_REPORT_FILENAME,
        repair_history_path=run_root / REPAIR_HISTORY_FILENAME,
        log_analysis_path=run_root / LOG_ANALYSIS_FILENAME,
        grader_path=run_root / GRADER_FILENAME,
        verdict_path=run_root / VERDICT_FILENAME,
    )


def ensure_result_bundle_layout(*, workspace_root: Path, run_id: str) -> ResultBundleLayout:
    layout = build_result_bundle_layout(workspace_root=workspace_root, run_id=run_id)
    layout.run_root.mkdir(parents=True, exist_ok=True)
    return layout

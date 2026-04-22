from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME, WORKSPACE_REPORTS_EVALS_DIRNAME
from aidd.harness.runner import (
    HarnessAiddRunResult,
    HarnessCommandTranscript,
    HarnessSetupResult,
    HarnessTeardownResult,
    HarnessVerificationResult,
)
from aidd.harness.scenarios import Scenario

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


def _format_utc_timestamp(timestamp: datetime | None = None) -> str:
    moment = (timestamp or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    return moment.isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _command_transcript_payload(transcript: HarnessCommandTranscript) -> dict[str, Any]:
    return {
        "command": transcript.command,
        "duration_seconds": transcript.duration_seconds,
        "exit_code": transcript.exit_code,
        "stderr_text": transcript.stderr_text,
        "stdout_text": transcript.stdout_text,
    }


def _step_transcript_payload(
    *,
    step: str,
    command_transcripts: tuple[HarnessCommandTranscript, ...],
    duration_seconds: float,
) -> dict[str, Any]:
    return {
        "command_count": len(command_transcripts),
        "commands": [_command_transcript_payload(item) for item in command_transcripts],
        "duration_seconds": duration_seconds,
        "step": step,
    }


def write_harness_metadata(
    *,
    layout: ResultBundleLayout,
    scenario: Scenario,
    runtime_id: str,
    work_item: str,
    status: str,
    aidd_run_id: str | None = None,
    aidd_run_result: HarnessAiddRunResult | None = None,
    aidd_artifact_references: Mapping[str, str] | None = None,
) -> Path:
    normalized_runtime_id = runtime_id.strip()
    normalized_work_item = work_item.strip()
    normalized_status = status.strip()
    if not normalized_runtime_id:
        raise ValueError("runtime_id must be non-empty.")
    if not normalized_work_item:
        raise ValueError("work_item must be non-empty.")
    if not normalized_status:
        raise ValueError("status must be non-empty.")

    metadata_payload: dict[str, Any] = {
        "created_at_utc": _format_utc_timestamp(),
        "run_id": layout.run_root.name,
        "runtime_id": normalized_runtime_id,
        "scenario_id": scenario.scenario_id,
        "status": normalized_status,
        "task": scenario.task,
        "work_item": normalized_work_item,
        "stage_scope": {
            "start": scenario.run.stage_start,
            "end": scenario.run.stage_end,
        },
        "runtime_targets": list(scenario.runtime_targets),
        "aidd_artifact_references": dict(aidd_artifact_references or {}),
    }
    if aidd_run_id is not None:
        metadata_payload["aidd_run_id"] = aidd_run_id
    if aidd_run_result is not None:
        metadata_payload["aidd_run"] = {
            "command": list(aidd_run_result.command),
            "duration_seconds": aidd_run_result.duration_seconds,
            "exit_code": aidd_run_result.exit_code,
            "runtime_id": aidd_run_result.runtime_id,
            "work_item": aidd_run_result.work_item,
        }
    return _write_json(layout.harness_metadata_path, metadata_payload)


def write_command_transcripts(
    *,
    layout: ResultBundleLayout,
    setup_result: HarnessSetupResult | None = None,
    aidd_run_result: HarnessAiddRunResult | None = None,
    verification_result: HarnessVerificationResult | None = None,
    teardown_result: HarnessTeardownResult | None = None,
) -> tuple[Path, Path, Path, Path]:
    setup_path = _write_json(
        layout.setup_transcript_path,
        _step_transcript_payload(
            step="setup",
            command_transcripts=(
                setup_result.command_transcripts if setup_result is not None else tuple()
            ),
            duration_seconds=setup_result.duration_seconds if setup_result is not None else 0.0,
        ),
    )
    run_path = _write_json(
        layout.run_transcript_path,
        {
            "command_count": 0 if aidd_run_result is None else 1,
            "commands": []
            if aidd_run_result is None
            else [_command_transcript_payload(aidd_run_result.command_transcript)],
            "duration_seconds": (
                0.0 if aidd_run_result is None else aidd_run_result.duration_seconds
            ),
            "exit_code": None if aidd_run_result is None else aidd_run_result.exit_code,
            "runtime_id": None if aidd_run_result is None else aidd_run_result.runtime_id,
            "step": "run",
            "work_item": None if aidd_run_result is None else aidd_run_result.work_item,
        },
    )
    verify_path = _write_json(
        layout.verify_transcript_path,
        _step_transcript_payload(
            step="verify",
            command_transcripts=(
                verification_result.command_transcripts
                if verification_result is not None
                else tuple()
            ),
            duration_seconds=(
                verification_result.duration_seconds if verification_result is not None else 0.0
            ),
        ),
    )
    teardown_path = _write_json(
        layout.teardown_transcript_path,
        _step_transcript_payload(
            step="teardown",
            command_transcripts=(
                teardown_result.command_transcripts if teardown_result is not None else tuple()
            ),
            duration_seconds=(
                teardown_result.duration_seconds if teardown_result is not None else 0.0
            ),
        ),
    )
    return setup_path, run_path, verify_path, teardown_path

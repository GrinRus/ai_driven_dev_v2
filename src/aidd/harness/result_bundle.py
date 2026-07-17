from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from aidd.core.identifiers import SafeIdentifier, contained_component_path
from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME, WORKSPACE_REPORTS_EVALS_DIRNAME
from aidd.harness.install_artifact import HarnessInstallResult
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
STAGE_TIMING_JSON_FILENAME = "stage-timing.json"
STAGE_TIMING_MARKDOWN_FILENAME = "stage-timing.md"
SELF_REPAIR_MATRIX_JSON_FILENAME = "self-repair-matrix.json"
SELF_REPAIR_MATRIX_FILENAME = "self-repair-matrix.md"
GRADER_FILENAME = "grader.json"
VERDICT_FILENAME = "verdict.md"
HARNESS_METADATA_FILENAME = "harness-metadata.json"
FEATURE_SELECTION_FILENAME = "feature-selection.json"
INSTALL_TRANSCRIPT_FILENAME = "install-transcript.json"
SETUP_TRANSCRIPT_FILENAME = "setup-transcript.json"
RUN_TRANSCRIPT_FILENAME = "run-transcript.json"
VERIFY_TRANSCRIPT_FILENAME = "verify-transcript.json"
TEARDOWN_TRANSCRIPT_FILENAME = "teardown-transcript.json"
ARTIFACT_DIGESTS_FILENAME = "artifact-digests.json"


@dataclass(frozen=True, slots=True)
class ResultBundleLayout:
    run_root: Path
    harness_metadata_path: Path
    install_transcript_path: Path
    setup_transcript_path: Path
    run_transcript_path: Path
    verify_transcript_path: Path
    teardown_transcript_path: Path
    feature_selection_path: Path
    runtime_log_path: Path
    runtime_jsonl_path: Path
    events_jsonl_path: Path
    validator_report_path: Path
    repair_history_path: Path
    log_analysis_path: Path
    stage_timing_json_path: Path
    stage_timing_markdown_path: Path
    self_repair_matrix_json_path: Path
    self_repair_matrix_path: Path
    grader_path: Path
    verdict_path: Path
    artifact_digests_path: Path


def _validate_run_id(run_id: str) -> str:
    return SafeIdentifier.parse(run_id, label="run_id").value


def build_result_bundle_layout(*, workspace_root: Path, run_id: str) -> ResultBundleLayout:
    normalized_run_id = _validate_run_id(run_id)
    evals_root = (
        workspace_root
        / WORKSPACE_REPORTS_DIRNAME
        / WORKSPACE_REPORTS_EVALS_DIRNAME
    )
    run_root = contained_component_path(
        evals_root,
        normalized_run_id,
        boundary_root=workspace_root,
        label="run_id",
    )
    return ResultBundleLayout(
        run_root=run_root,
        harness_metadata_path=run_root / HARNESS_METADATA_FILENAME,
        install_transcript_path=run_root / INSTALL_TRANSCRIPT_FILENAME,
        setup_transcript_path=run_root / SETUP_TRANSCRIPT_FILENAME,
        run_transcript_path=run_root / RUN_TRANSCRIPT_FILENAME,
        verify_transcript_path=run_root / VERIFY_TRANSCRIPT_FILENAME,
        teardown_transcript_path=run_root / TEARDOWN_TRANSCRIPT_FILENAME,
        feature_selection_path=run_root / FEATURE_SELECTION_FILENAME,
        runtime_log_path=run_root / RUNTIME_LOG_FILENAME,
        runtime_jsonl_path=run_root / RUNTIME_JSONL_FILENAME,
        events_jsonl_path=run_root / EVENTS_JSONL_FILENAME,
        validator_report_path=run_root / VALIDATOR_REPORT_FILENAME,
        repair_history_path=run_root / REPAIR_HISTORY_FILENAME,
        log_analysis_path=run_root / LOG_ANALYSIS_FILENAME,
        stage_timing_json_path=run_root / STAGE_TIMING_JSON_FILENAME,
        stage_timing_markdown_path=run_root / STAGE_TIMING_MARKDOWN_FILENAME,
        self_repair_matrix_json_path=run_root / SELF_REPAIR_MATRIX_JSON_FILENAME,
        self_repair_matrix_path=run_root / SELF_REPAIR_MATRIX_FILENAME,
        grader_path=run_root / GRADER_FILENAME,
        verdict_path=run_root / VERDICT_FILENAME,
        artifact_digests_path=run_root / ARTIFACT_DIGESTS_FILENAME,
    )


def build_result_bundle_layout_at_run_root(*, run_root: Path) -> ResultBundleLayout:
    normalized_run_root = run_root.resolve(strict=False)
    _validate_run_id(normalized_run_root.name)
    return ResultBundleLayout(
        run_root=normalized_run_root,
        harness_metadata_path=normalized_run_root / HARNESS_METADATA_FILENAME,
        install_transcript_path=normalized_run_root / INSTALL_TRANSCRIPT_FILENAME,
        setup_transcript_path=normalized_run_root / SETUP_TRANSCRIPT_FILENAME,
        run_transcript_path=normalized_run_root / RUN_TRANSCRIPT_FILENAME,
        verify_transcript_path=normalized_run_root / VERIFY_TRANSCRIPT_FILENAME,
        teardown_transcript_path=normalized_run_root / TEARDOWN_TRANSCRIPT_FILENAME,
        feature_selection_path=normalized_run_root / FEATURE_SELECTION_FILENAME,
        runtime_log_path=normalized_run_root / RUNTIME_LOG_FILENAME,
        runtime_jsonl_path=normalized_run_root / RUNTIME_JSONL_FILENAME,
        events_jsonl_path=normalized_run_root / EVENTS_JSONL_FILENAME,
        validator_report_path=normalized_run_root / VALIDATOR_REPORT_FILENAME,
        repair_history_path=normalized_run_root / REPAIR_HISTORY_FILENAME,
        log_analysis_path=normalized_run_root / LOG_ANALYSIS_FILENAME,
        stage_timing_json_path=normalized_run_root / STAGE_TIMING_JSON_FILENAME,
        stage_timing_markdown_path=normalized_run_root / STAGE_TIMING_MARKDOWN_FILENAME,
        self_repair_matrix_json_path=normalized_run_root / SELF_REPAIR_MATRIX_JSON_FILENAME,
        self_repair_matrix_path=normalized_run_root / SELF_REPAIR_MATRIX_FILENAME,
        grader_path=normalized_run_root / GRADER_FILENAME,
        verdict_path=normalized_run_root / VERDICT_FILENAME,
        artifact_digests_path=normalized_run_root / ARTIFACT_DIGESTS_FILENAME,
    )


def ensure_result_bundle_layout(*, workspace_root: Path, run_id: str) -> ResultBundleLayout:
    layout = build_result_bundle_layout(workspace_root=workspace_root, run_id=run_id)
    layout.run_root.mkdir(parents=True, exist_ok=True)
    return layout


def ensure_result_bundle_layout_at_report_root(
    *,
    report_root: Path,
    run_id: str,
) -> ResultBundleLayout:
    normalized_run_id = _validate_run_id(run_id)
    run_root = contained_component_path(
        report_root,
        normalized_run_id,
        boundary_root=report_root,
        label="run_id",
    )
    layout = build_result_bundle_layout_at_run_root(run_root=run_root)
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
        "timed_out": transcript.timed_out,
        "timeout_seconds": transcript.timeout_seconds,
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
    install_result: HarnessInstallResult | None = None,
    target_repository_cwd: Path | None = None,
    workspace_root: Path | None = None,
    resource_source: str | None = None,
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
        "automation_lane": scenario.automation_lane,
        "canonical_runtime": scenario.canonical_runtime,
        "created_at_utc": _format_utc_timestamp(),
        "feature_size": scenario.feature_size,
        "is_live": scenario.is_live,
        "run_id": layout.run_root.name,
        "runtime_id": normalized_runtime_id,
        "scenario_class": scenario.scenario_class,
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
    if install_result is not None:
        metadata_payload["aidd_install"] = {
            "artifact_identity": install_result.artifact_identity,
            "artifact_source": install_result.artifact_source,
            "install_channel": install_result.install_channel,
            "install_home": install_result.install_home.as_posix(),
            "installed_command": list(install_result.installed_command),
            "tool_bin_dir": install_result.tool_bin_dir.as_posix(),
        }
    if (
        target_repository_cwd is not None
        or workspace_root is not None
        or resource_source is not None
    ):
        metadata_payload["execution_context"] = {
            "resource_source": resource_source,
            "target_repository_cwd": (
                None if target_repository_cwd is None else target_repository_cwd.as_posix()
            ),
            "workspace_root": None if workspace_root is None else workspace_root.as_posix(),
        }
    if aidd_run_result is not None:
        metadata_payload["aidd_run"] = {
            "command": list(aidd_run_result.command),
            "duration_seconds": aidd_run_result.duration_seconds,
            "exit_code": aidd_run_result.exit_code,
            "runtime_id": aidd_run_result.runtime_id,
            "timed_out": aidd_run_result.timed_out,
            "timeout_seconds": aidd_run_result.timeout_seconds,
            "work_item": aidd_run_result.work_item,
        }
    return _write_json(layout.harness_metadata_path, metadata_payload)


def write_command_transcripts(
    *,
    layout: ResultBundleLayout,
    install_result: HarnessInstallResult | None = None,
    setup_result: HarnessSetupResult | None = None,
    aidd_run_result: HarnessAiddRunResult | None = None,
    verification_result: HarnessVerificationResult | None = None,
    teardown_result: HarnessTeardownResult | None = None,
) -> tuple[Path, Path, Path, Path, Path]:
    install_path = _write_json(
        layout.install_transcript_path,
        _step_transcript_payload(
            step="install",
            command_transcripts=(
                install_result.command_transcripts if install_result is not None else tuple()
            ),
            duration_seconds=install_result.duration_seconds if install_result is not None else 0.0,
        ),
    )
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
            "timed_out": False if aidd_run_result is None else aidd_run_result.timed_out,
            "timeout_seconds": None if aidd_run_result is None else aidd_run_result.timeout_seconds,
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
    return install_path, setup_path, run_path, verify_path, teardown_path


def write_feature_selection(*, layout: ResultBundleLayout, payload: Mapping[str, Any]) -> Path:
    return _write_json(layout.feature_selection_path, dict(payload))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_artifact_source(source_path: Path) -> None:
    if not source_path.exists() or not source_path.is_file():
        raise ValueError(f"Artifact source file does not exist: {source_path.as_posix()}")


def _atomic_write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return path


def read_artifact_digests(*, layout: ResultBundleLayout) -> dict[str, Any] | None:
    if not layout.artifact_digests_path.is_file():
        warnings.warn(
            "Result bundle has no artifact-digests.json; treating it as a legacy bundle.",
            stacklevel=2,
        )
        return None
    payload = json.loads(layout.artifact_digests_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Result bundle artifact digest manifest is malformed.")
    if payload.get("schema_version") != 1 or not isinstance(payload.get("artifacts"), list):
        raise ValueError("Result bundle artifact digest manifest is malformed.")
    return cast(dict[str, Any], payload)


def copy_or_link_run_artifacts(
    *,
    layout: ResultBundleLayout,
    runtime_log_path: Path,
    validator_report_path: Path,
    verdict_path: Path,
    runtime_jsonl_path: Path | None = None,
    events_jsonl_path: Path | None = None,
) -> dict[str, Path]:
    sources: dict[str, tuple[Path, Path]] = {
        "runtime_log": (runtime_log_path, layout.runtime_log_path),
        "validator_report": (validator_report_path, layout.validator_report_path),
        "verdict": (verdict_path, layout.verdict_path),
    }
    if runtime_jsonl_path is not None:
        sources["runtime_jsonl"] = (runtime_jsonl_path, layout.runtime_jsonl_path)
    if events_jsonl_path is not None:
        sources["events_jsonl"] = (events_jsonl_path, layout.events_jsonl_path)

    for source_path, _destination_path in sources.values():
        _validate_artifact_source(source_path)

    layout.run_root.mkdir(parents=True, exist_ok=True)
    layout.artifact_digests_path.unlink(missing_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=".artifact-materialization-", dir=layout.run_root)
    )
    prepared: list[tuple[str, Path, Path, str, int]] = []
    try:
        for key, (source_path, destination_path) in sources.items():
            staged_path = staging_root / destination_path.name
            shutil.copyfile(source_path, staged_path)
            source_digest = _sha256(source_path)
            staged_digest = _sha256(staged_path)
            if source_digest != staged_digest:
                raise OSError(
                    f"Artifact copy verification failed: {source_path.as_posix()}"
                )
            prepared.append(
                (
                    key,
                    staged_path,
                    destination_path,
                    staged_digest,
                    staged_path.stat().st_size,
                )
            )

        for _key, staged_path, destination_path, _digest, _size in prepared:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            staged_path.replace(destination_path)

        artifacts = [
            {
                "path": destination_path.relative_to(layout.run_root).as_posix(),
                "sha256": digest,
                "size_bytes": size,
            }
            for _key, _staged_path, destination_path, digest, size in sorted(
                prepared,
                key=lambda item: item[2].relative_to(layout.run_root).as_posix(),
            )
        ]
        _atomic_write_json(
            layout.artifact_digests_path,
            {
                "artifacts": artifacts,
                "schema_version": 1,
            },
        )
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    return {
        key: destination_path
        for key, (_source_path, destination_path) in sources.items()
    }

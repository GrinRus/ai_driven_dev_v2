from __future__ import annotations

import hashlib
import json
import shutil
import stat
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aidd.core.identifiers import SafeIdentifier, contained_component_path
from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME, WORKSPACE_REPORTS_EVALS_DIRNAME
from aidd.harness.install_artifact import HarnessInstallResult
from aidd.harness.result_bundle_contract import (
    RESULT_BUNDLE_INVENTORY_FILENAME,
    BundleArtifactRequirement,
    BundleStatus,
    ResultBundleArtifact,
    ResultBundleContractError,
    ResultBundleIdentity,
    ResultBundleInventory,
    dump_result_bundle_inventory,
    validate_result_bundle_inventory,
)
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
AIDD_EVIDENCE_DIRNAME = "canonical-evidence"
RUNTIME_EXIT_METADATA_FILENAME = "runtime-exit.json"
SUMMARY_FILENAME = "summary.md"
BUNDLE_INTEGRITY_FAILURE_FILENAME = "bundle-integrity-failure.md"
_BUNDLE_STATUSES: frozenset[BundleStatus] = frozenset(
    ("pass", "fail", "blocked", "infra-fail")
)
_REQUIRED_BUNDLE_FILENAMES = (
    HARNESS_METADATA_FILENAME,
    INSTALL_TRANSCRIPT_FILENAME,
    SETUP_TRANSCRIPT_FILENAME,
    RUN_TRANSCRIPT_FILENAME,
    VERIFY_TRANSCRIPT_FILENAME,
    TEARDOWN_TRANSCRIPT_FILENAME,
    FEATURE_SELECTION_FILENAME,
    RUNTIME_LOG_FILENAME,
    VALIDATOR_REPORT_FILENAME,
    REPAIR_HISTORY_FILENAME,
    LOG_ANALYSIS_FILENAME,
    STAGE_TIMING_JSON_FILENAME,
    STAGE_TIMING_MARKDOWN_FILENAME,
    SELF_REPAIR_MATRIX_JSON_FILENAME,
    SELF_REPAIR_MATRIX_FILENAME,
    GRADER_FILENAME,
    VERDICT_FILENAME,
    SUMMARY_FILENAME,
)
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
    inventory_path: Path


def _validate_run_id(run_id: str) -> str:
    return SafeIdentifier.parse(run_id, label="run_id").value


def build_result_bundle_layout(*, workspace_root: Path, run_id: str) -> ResultBundleLayout:
    normalized_run_id = _validate_run_id(run_id)
    evals_root = workspace_root / WORKSPACE_REPORTS_DIRNAME / WORKSPACE_REPORTS_EVALS_DIRNAME
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
        inventory_path=run_root / RESULT_BUNDLE_INVENTORY_FILENAME,
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
        inventory_path=normalized_run_root / RESULT_BUNDLE_INVENTORY_FILENAME,
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
    failed_command: str | None = None,
    failed_exit_code: int | None = None,
) -> dict[str, Any]:
    return {
        "command_count": len(command_transcripts),
        "commands": [_command_transcript_payload(item) for item in command_transcripts],
        "duration_seconds": duration_seconds,
        "failed_command": failed_command,
        "failed_exit_code": failed_exit_code,
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
    evaluation_run_id: str | None = None,
    product_run_id: str | None = None,
    phase_metadata: Mapping[str, Any] | None = None,
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
        "expected_exit_code": scenario.run.expected_exit_code,
        "work_item": normalized_work_item,
        "stage_scope": {
            "start": scenario.run.stage_start,
            "end": scenario.run.stage_end,
        },
        "runtime_targets": list(scenario.runtime_targets),
        "aidd_artifact_references": dict(aidd_artifact_references or {}),
    }
    if evaluation_run_id is not None:
        metadata_payload["evaluation_run_id"] = evaluation_run_id
        metadata_payload["product_run_id"] = product_run_id
    if phase_metadata is not None:
        metadata_payload["phase_metadata"] = dict(phase_metadata)
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
            failed_command=(
                setup_result.failed_command if setup_result is not None else None
            ),
            failed_exit_code=(
                setup_result.failed_exit_code if setup_result is not None else None
            ),
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
            failed_command=(
                verification_result.failed_command
                if verification_result is not None
                else None
            ),
            failed_exit_code=(
                verification_result.failed_exit_code
                if verification_result is not None
                else None
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
            failed_command=(
                teardown_result.failed_command
                if teardown_result is not None
                else None
            ),
            failed_exit_code=(
                teardown_result.failed_exit_code
                if teardown_result is not None
                else None
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
    try:
        mode = source_path.lstat().st_mode
    except FileNotFoundError:
        mode = 0
    if not stat.S_ISREG(mode):
        raise ValueError(f"Artifact source file does not exist: {source_path.as_posix()}")


def _relative_destination(*, layout: ResultBundleLayout, destination: Path) -> Path:
    if not destination.is_absolute():
        destination = layout.run_root / destination
    resolved_root = layout.run_root.resolve(strict=False)
    resolved_destination = destination.resolve(strict=False)
    if not resolved_destination.is_relative_to(resolved_root):
        raise ValueError(
            f"Artifact destination must stay inside result bundle: {destination.as_posix()}"
        )
    return resolved_destination.relative_to(resolved_root)


def _iter_evidence_sources(
    *,
    source_root: Path,
    destination_root: Path,
) -> tuple[tuple[Path, Path], ...]:
    """Enumerate trusted regular files from one AIDD evidence tree."""

    if not source_root.exists():
        return tuple()
    if source_root.is_symlink() or not source_root.is_dir():
        raise ValueError(f"AIDD evidence source must be a real directory: {source_root}")
    sources: list[tuple[Path, Path]] = []
    for source in sorted(source_root.rglob("*")):
        mode = source.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ValueError(f"Symlink is not trusted AIDD evidence: {source}")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(f"Unsupported AIDD evidence node: {source}")
        sources.append((source, destination_root / source.relative_to(source_root)))
    return tuple(sources)


def collect_aidd_evidence_sources(
    *,
    layout: ResultBundleLayout,
    source_workspace_root: Path | None,
    work_item: str,
    product_run_id: str | None,
) -> tuple[dict[str, tuple[Path, Path]], dict[str, str]]:
    """Collect raw and canonical AIDD files before an isolated workspace is removed.

    The returned source map is consumed by :func:`copy_or_link_run_artifacts`; all
    destinations are bundle-relative and therefore remain readable after the source
    workspace is cleaned up.
    """

    if source_workspace_root is None:
        return {}, {}
    workspace_root = source_workspace_root.resolve(strict=False)
    normalized_work_item = SafeIdentifier.parse(work_item, label="work_item").value
    sources: list[tuple[str, Path, Path]] = []
    references: dict[str, str] = {}
    roots: list[tuple[str, Path]] = [
        ("work_item", workspace_root / "workitems" / normalized_work_item)
    ]
    if product_run_id is not None:
        roots.append(
            (
                "task_run",
                workspace_root
                / "reports"
                / "runs"
                / normalized_work_item
                / SafeIdentifier.parse(product_run_id, label="product_run_id").value,
            )
        )
    for category, source_root in roots:
        destination_root = layout.run_root / AIDD_EVIDENCE_DIRNAME / category.replace(
            "_", "-"
        )
        enumerated = _iter_evidence_sources(
            source_root=source_root,
            destination_root=destination_root,
        )
        if not enumerated:
            continue
        relative_root = destination_root.relative_to(layout.run_root).as_posix()
        references[f"{category}_root"] = relative_root
        for index, (source, destination) in enumerate(enumerated):
            sources.append((f"{category}:{index}", source, destination))
            filename = source.name
            relative = destination.relative_to(layout.run_root).as_posix()
            if filename == "task-ledger.json":
                references.setdefault("task_ledger", relative)
            elif filename == "finalization-state.json":
                references["finalization_evidence"] = relative
            elif filename == RUNTIME_LOG_FILENAME:
                references.setdefault("runtime_attempt_log", relative)
            elif filename == RUNTIME_EXIT_METADATA_FILENAME:
                references.setdefault("runtime_exit_metadata", relative)
            elif filename == RUNTIME_JSONL_FILENAME:
                references.setdefault("runtime_attempt_jsonl", relative)
            elif filename == EVENTS_JSONL_FILENAME:
                references.setdefault("events_attempt_jsonl", relative)
    return {
        key: (source, destination) for key, source, destination in sources
    }, references


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


def copy_or_link_run_artifacts(
    *,
    layout: ResultBundleLayout,
    runtime_log_path: Path,
    validator_report_path: Path,
    verdict_path: Path,
    runtime_jsonl_path: Path | None = None,
    events_jsonl_path: Path | None = None,
    additional_sources: Mapping[str, tuple[Path, Path]] | None = None,
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
    for key, (source_path, destination_path) in (additional_sources or {}).items():
        if key in sources:
            raise ValueError(f"Duplicate result bundle artifact key: {key}")
        sources[key] = (source_path, destination_path)

    for source_path, _destination_path in sources.values():
        _validate_artifact_source(source_path)

    layout.run_root.mkdir(parents=True, exist_ok=True)
    layout.artifact_digests_path.unlink(missing_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=".artifact-materialization-", dir=layout.run_root))
    prepared: list[tuple[str, Path, Path, str, int]] = []
    try:
        for key, (source_path, destination_path) in sources.items():
            staged_path = staging_root / _relative_destination(
                layout=layout,
                destination=destination_path
            )
            if staged_path.exists():
                raise ValueError(f"Duplicate result bundle artifact path: {destination_path}")
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, staged_path)
            source_digest = _sha256(source_path)
            staged_digest = _sha256(staged_path)
            if source_digest != staged_digest:
                raise OSError(f"Artifact copy verification failed: {source_path.as_posix()}")
            prepared.append(
                (
                    key,
                    staged_path,
                    destination_path,
                    staged_digest,
                    staged_path.stat().st_size,
                )
            )

        if additional_sources:
            evidence_root = layout.run_root / AIDD_EVIDENCE_DIRNAME
            if evidence_root.exists():
                shutil.rmtree(evidence_root)
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

    return {key: destination_path for key, (_source_path, destination_path) in sources.items()}


def _bundle_artifact_files(*, layout: ResultBundleLayout) -> tuple[Path, ...]:
    """Return regular content files, excluding mutable seal indexes."""

    if not layout.run_root.is_dir():
        raise ResultBundleContractError(f"bundle root does not exist: {layout.run_root!s}.")
    files: list[Path] = []
    for path in sorted(layout.run_root.rglob("*")):
        if path.is_symlink():
            raise ResultBundleContractError(
                f"bundle contains an untrusted symlink: {path.relative_to(layout.run_root)}."
            )
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ResultBundleContractError(
                "bundle contains an unsupported artifact node: "
                f"{path.relative_to(layout.run_root)}."
            )
        if path in {layout.inventory_path, layout.artifact_digests_path}:
            continue
        if path.name.startswith(".") and path.name.endswith(".tmp"):
            raise ResultBundleContractError(
                f"bundle contains an unfinished temporary artifact: {path.name!r}."
            )
        files.append(path)
    return tuple(files)


def build_result_bundle_inventory(
    *,
    layout: ResultBundleLayout,
    identity: ResultBundleIdentity,
    status: BundleStatus,
    requirements: tuple[BundleArtifactRequirement, ...] = (),
) -> ResultBundleInventory:
    """Snapshot content files into the versioned bundle inventory contract."""

    artifacts = tuple(
        ResultBundleArtifact(
            path=path.relative_to(layout.run_root).as_posix(),
            sha256=_sha256(path),
            size_bytes=path.stat().st_size,
        )
        for path in _bundle_artifact_files(layout=layout)
    )
    selected_requirements = requirements or tuple(
        BundleArtifactRequirement(
            path=filename,
            required_for=frozenset(_BUNDLE_STATUSES),
        )
        for filename in _REQUIRED_BUNDLE_FILENAMES
    )
    return ResultBundleInventory(
        identity=identity,
        status=status,
        artifacts=artifacts,
        requirements=selected_requirements,
    ).normalized()


def _validate_bundle_metadata_identity(
    *,
    layout: ResultBundleLayout,
    identity: ResultBundleIdentity,
) -> None:
    try:
        payload = json.loads(layout.harness_metadata_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ResultBundleContractError("bundle metadata is missing or invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ResultBundleContractError("bundle metadata must be a JSON object.")
    expected = identity.normalized().to_dict()
    actual = {
        key: payload.get(key)
        for key in ("evaluation_run_id", "product_run_id", "scenario_id", "runtime_id", "work_item")
    }
    if actual != expected:
        raise ResultBundleContractError(
            "bundle metadata identity does not match execution identity."
        )


def seal_result_bundle(
    *,
    layout: ResultBundleLayout,
    identity: ResultBundleIdentity,
    status: BundleStatus,
    requirements: tuple[BundleArtifactRequirement, ...] = (),
) -> ResultBundleInventory:
    """Atomically publish a digest-backed inventory as the bundle commit marker."""

    normalized_identity = identity.normalized()
    layout.run_root.mkdir(parents=True, exist_ok=True)
    _validate_bundle_metadata_identity(layout=layout, identity=normalized_identity)
    if status == "pass" and normalized_identity.product_run_id is not None:
        for category in ("work-item", "task-run"):
            evidence_root = layout.run_root / AIDD_EVIDENCE_DIRNAME / category
            if not evidence_root.is_dir() or not any(
                path.is_file() for path in evidence_root.rglob("*")
            ):
                raise ResultBundleContractError(
                    f"bundle is missing canonical AIDD evidence tree: {category}."
                )

    # An inventory is the final commit marker.  Write the complete digest index first,
    # then re-snapshot and atomically replace the inventory after validation.
    inventory = build_result_bundle_inventory(
        layout=layout,
        identity=normalized_identity,
        status=status,
        requirements=requirements,
    )
    validate_result_bundle_inventory(
        inventory=inventory,
        bundle_root=layout.run_root,
        expected_identity=normalized_identity,
    )
    _atomic_write_json(
        layout.artifact_digests_path,
        {
            "artifacts": [item.to_dict() for item in inventory.artifacts],
            "schema_version": 2,
        },
    )
    inventory = build_result_bundle_inventory(
        layout=layout,
        identity=normalized_identity,
        status=status,
        requirements=requirements,
    )
    validate_result_bundle_inventory(
        inventory=inventory,
        bundle_root=layout.run_root,
        expected_identity=normalized_identity,
    )
    temporary_path = layout.inventory_path.with_name(f".{layout.inventory_path.name}.tmp")
    try:
        temporary_path.write_text(dump_result_bundle_inventory(inventory), encoding="utf-8")
        temporary_path.replace(layout.inventory_path)
    except OSError:
        layout.inventory_path.unlink(missing_ok=True)
        raise
    finally:
        temporary_path.unlink(missing_ok=True)
    try:
        validate_result_bundle_inventory(
            inventory=inventory,
            bundle_root=layout.run_root,
            expected_identity=normalized_identity,
        )
    except ResultBundleContractError:
        layout.inventory_path.unlink(missing_ok=True)
        raise
    return inventory

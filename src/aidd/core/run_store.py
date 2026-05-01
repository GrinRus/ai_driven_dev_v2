from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aidd.core.models.run import RepairHistoryEntry, RunArtifactIndex, StageRunMetadata
from aidd.core.resources import resolve_resource_layout_from_contracts_root
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT, resolve_prompt_pack_paths
from aidd.core.workspace import (
    RESERVED_STAGE_FILENAMES,
    WORKSPACE_REPORTS_DIRNAME,
    WORKSPACE_REPORTS_RUNS_DIRNAME,
)
from aidd.core.workspace import (
    stage_root as work_item_stage_root,
)

RUN_STAGES_DIRNAME = "stages"
RUN_ATTEMPTS_DIRNAME = "attempts"
RUN_ATTEMPT_PREFIX = "attempt-"
RUN_MANIFEST_FILENAME = "run-manifest.json"
RUN_STAGE_METADATA_FILENAME = "stage-metadata.json"
RUN_ARTIFACT_INDEX_FILENAME = "artifact-index.json"
RUN_ATTEMPT_INPUT_BUNDLE_FILENAME = "input-bundle.md"
RUN_ATTEMPT_REPAIR_CONTEXT_FILENAME = "repair-context.md"
RUN_RUNTIME_LOG_FILENAME = "runtime.log"
RUN_RUNTIME_EXIT_METADATA_FILENAME = "runtime-exit.json"
_GIT_SHA_LENGTH = 40


def _format_utc_timestamp(timestamp: datetime | None = None) -> str:
    moment = (timestamp or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    return moment.isoformat().replace("+00:00", "Z")


def _workspace_relative_canonical_path(workspace_root: Path, path: Path) -> str:
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = path.resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_workspace):
        raise ValueError(f"Path must stay inside workspace root: {resolved_path}")
    return resolved_path.relative_to(resolved_workspace).as_posix()


def _resolve_repository_root(
    *,
    contracts_root: Path,
    repository_root: Path | None,
) -> Path:
    if repository_root is not None:
        return repository_root.resolve(strict=False)
    return resolve_resource_layout_from_contracts_root(contracts_root).root


def _classify_resource_source(resource_root: Path) -> str:
    if resource_root.name == "_resources":
        return "packaged"
    if (resource_root / "contracts").is_dir() and (resource_root / "prompt-packs").is_dir():
        if (resource_root / "pyproject.toml").exists():
            return "repository"
        return "custom"
    return "custom"


def _resolve_repository_git_sha(repository_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None

    candidate = completed.stdout.strip()
    if completed.returncode != 0 or len(candidate) != _GIT_SHA_LENGTH:
        return None
    if any(char not in "0123456789abcdef" for char in candidate.lower()):
        return None
    return candidate


def _sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _collect_prompt_pack_provenance(
    *,
    stage_target: str,
    contracts_root: Path,
    resource_root: Path,
) -> tuple[RunArtifactIndex.PromptPackProvenanceEntry, ...]:
    prompt_pack_paths = resolve_prompt_pack_paths(
        stage=stage_target,
        contracts_root=contracts_root,
    )
    return tuple(
        RunArtifactIndex.PromptPackProvenanceEntry(
            path=prompt_path,
            sha256=_sha256_hex((resource_root / prompt_path).resolve(strict=False)),
        )
        for prompt_path in prompt_pack_paths
    )


def run_store_root(workspace_root: Path) -> Path:
    return workspace_root / WORKSPACE_REPORTS_DIRNAME / WORKSPACE_REPORTS_RUNS_DIRNAME


def work_item_runs_root(workspace_root: Path, work_item: str) -> Path:
    return run_store_root(workspace_root=workspace_root) / work_item


def run_root(workspace_root: Path, work_item: str, run_id: str) -> Path:
    return work_item_runs_root(workspace_root=workspace_root, work_item=work_item) / run_id


def run_stages_root(workspace_root: Path, work_item: str, run_id: str) -> Path:
    return (
        run_root(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
        / RUN_STAGES_DIRNAME
    )


def run_stage_root(workspace_root: Path, work_item: str, run_id: str, stage: str) -> Path:
    return run_stages_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    ) / stage


def format_attempt_directory_name(attempt_number: int) -> str:
    if attempt_number < 1:
        raise ValueError("Attempt number must be >= 1.")
    return f"{RUN_ATTEMPT_PREFIX}{attempt_number:04d}"


def run_attempts_root(workspace_root: Path, work_item: str, run_id: str, stage: str) -> Path:
    return (
        run_stage_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        / RUN_ATTEMPTS_DIRNAME
    )


def run_attempt_root(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> Path:
    attempt_dir = format_attempt_directory_name(attempt_number)
    return (
        run_attempts_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        / attempt_dir
    )


def run_attempt_runtime_log_path(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> Path:
    return (
        run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
        / RUN_RUNTIME_LOG_FILENAME
    )


def run_attempt_artifact_index_path(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> Path:
    return (
        run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
        / RUN_ARTIFACT_INDEX_FILENAME
    )


def _parse_attempt_directory_name(name: str) -> int | None:
    if not name.startswith(RUN_ATTEMPT_PREFIX):
        return None

    suffix = name.removeprefix(RUN_ATTEMPT_PREFIX)
    if not suffix.isdigit():
        return None
    return int(suffix)


def next_attempt_number(workspace_root: Path, work_item: str, run_id: str, stage: str) -> int:
    attempts_root = run_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if not attempts_root.exists():
        return 1

    existing_numbers = [
        number
        for child in attempts_root.iterdir()
        if child.is_dir() and (number := _parse_attempt_directory_name(child.name)) is not None
    ]
    return max(existing_numbers, default=0) + 1


def create_next_attempt_directory(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    *,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    repository_root: Path | None = None,
) -> Path:
    attempts_root = run_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    attempts_root.mkdir(parents=True, exist_ok=True)

    attempt_number = next_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    attempt_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    attempt_path.mkdir(parents=False, exist_ok=False)
    resolved_repository_root = _resolve_repository_root(
        contracts_root=contracts_root,
        repository_root=repository_root,
    )
    write_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
        contracts_root=contracts_root,
        repository_root=resolved_repository_root,
    )
    return attempt_path


def run_manifest_path(workspace_root: Path, work_item: str, run_id: str) -> Path:
    return run_root(workspace_root=workspace_root, work_item=work_item, run_id=run_id) / (
        RUN_MANIFEST_FILENAME
    )


def run_stage_metadata_path(workspace_root: Path, work_item: str, run_id: str, stage: str) -> Path:
    return run_stage_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    ) / RUN_STAGE_METADATA_FILENAME


def load_stage_metadata(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> StageRunMetadata | None:
    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if not metadata_path.exists():
        return None
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return StageRunMetadata.from_dict(payload)


def load_attempt_artifact_index(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> RunArtifactIndex | None:
    artifact_index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    if not artifact_index_path.exists():
        return None
    payload = json.loads(artifact_index_path.read_text(encoding="utf-8"))
    return RunArtifactIndex.from_dict(payload)


def _canonical_stage_documents(workspace_root: Path, work_item: str, stage: str) -> dict[str, str]:
    stage_documents_root = work_item_stage_root(
        root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    return {
        filename.removesuffix(".md").replace("-", "_"): _workspace_relative_canonical_path(
            workspace_root=workspace_root,
            path=stage_documents_root / filename,
        )
        for filename in RESERVED_STAGE_FILENAMES
    }


def _canonical_attempt_documents(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> dict[str, str]:
    attempt_root = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    documents = {
        "input_bundle": _workspace_relative_canonical_path(
            workspace_root=workspace_root,
            path=attempt_root / RUN_ATTEMPT_INPUT_BUNDLE_FILENAME,
        )
    }
    repair_context_path = attempt_root / RUN_ATTEMPT_REPAIR_CONTEXT_FILENAME
    if repair_context_path.exists():
        documents["repair_context"] = _workspace_relative_canonical_path(
            workspace_root=workspace_root,
            path=repair_context_path,
        )
    return documents


def _canonical_log_paths(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> dict[str, str]:
    runtime_log = run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    logs = {
        "runtime_log": _workspace_relative_canonical_path(
            workspace_root=workspace_root,
            path=runtime_log,
        )
    }
    runtime_exit_metadata = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    ) / RUN_RUNTIME_EXIT_METADATA_FILENAME
    if runtime_exit_metadata.exists():
        logs["runtime_exit_metadata"] = _workspace_relative_canonical_path(
            workspace_root=workspace_root,
            path=runtime_exit_metadata,
        )
    return logs


def write_attempt_artifact_index(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
    *,
    changed_at_utc: datetime | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    repository_root: Path | None = None,
) -> Path:
    artifact_index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    timestamp = _format_utc_timestamp(changed_at_utc)
    existing_index = load_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    documents = _canonical_stage_documents(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    documents.update(
        _canonical_attempt_documents(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
    )
    logs = _canonical_log_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    resolved_repository_root = _resolve_repository_root(
        contracts_root=contracts_root,
        repository_root=repository_root,
    )
    resource_source = _classify_resource_source(resolved_repository_root)
    prompt_pack_provenance = _collect_prompt_pack_provenance(
        stage_target=stage,
        contracts_root=contracts_root,
        resource_root=resolved_repository_root,
    )

    index = RunArtifactIndex.create(
        run_id=run_id,
        work_item_id=work_item,
        stage=stage,
        attempt_number=attempt_number,
        documents=documents,
        logs=logs,
        prompt_pack_provenance=prompt_pack_provenance,
        resource_source=resource_source,
        resource_root=resolved_repository_root.as_posix(),
        changed_at_utc=timestamp,
    )
    if existing_index is not None:
        index = RunArtifactIndex(
            schema_version=existing_index.schema_version,
            run_id=index.run_id,
            work_item_id=index.work_item_id,
            stage=index.stage,
            attempt_number=index.attempt_number,
            documents=index.documents,
            logs=index.logs,
            prompt_pack_provenance=index.prompt_pack_provenance,
            resource_source=index.resource_source,
            resource_root=index.resource_root,
            created_at_utc=existing_index.created_at_utc,
            updated_at_utc=timestamp,
        )

    _write_json_payload(artifact_index_path, index.to_dict())
    return artifact_index_path


def _write_json_payload(path: Path, payload: dict[str, Any]) -> None:
    serialized_payload = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(serialized_payload, encoding="utf-8")
    try:
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _touch_manifest_timestamp(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    updated_at_utc: str,
) -> None:
    manifest_path = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not manifest_path.exists():
        return

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["updated_at_utc"] = updated_at_utc
    _write_json_payload(manifest_path, payload)


def persist_stage_status(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    status: str,
    *,
    changed_at_utc: datetime | None = None,
) -> Path:
    if not status.strip():
        raise ValueError("Status must be a non-empty string.")

    timestamp = _format_utc_timestamp(changed_at_utc)
    stage_root = run_stage_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    stage_root.mkdir(parents=True, exist_ok=True)
    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )

    existing = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if existing is None:
        metadata = StageRunMetadata.create(
            run_id=run_id,
            work_item_id=work_item,
            stage=stage,
            status=status,
            changed_at_utc=timestamp,
        )
    else:
        metadata = existing.with_status(status=status, changed_at_utc=timestamp)

    _write_json_payload(metadata_path, metadata.to_dict())
    _touch_manifest_timestamp(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        updated_at_utc=timestamp,
    )
    return metadata_path


def _workspace_relative_optional_path(workspace_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    return _workspace_relative_canonical_path(workspace_root=workspace_root, path=path)


def persist_repair_history_entry(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    *,
    attempt_number: int,
    trigger: str,
    outcome: str,
    validator_report_path: Path | None = None,
    repair_brief_path: Path | None = None,
    changed_at_utc: datetime | None = None,
) -> Path:
    existing = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if existing is None:
        raise ValueError(
            "Cannot persist repair history before stage metadata exists: "
            f"run_id={run_id}, work_item={work_item}, stage={stage}"
        )

    timestamp = _format_utc_timestamp(changed_at_utc)
    metadata = existing.with_repair_history_entry(
        entry=RepairHistoryEntry(
            attempt_number=attempt_number,
            trigger=trigger,
            outcome=outcome,
            recorded_at_utc=timestamp,
            validator_report_path=_workspace_relative_optional_path(
                workspace_root=workspace_root,
                path=validator_report_path,
            ),
            repair_brief_path=_workspace_relative_optional_path(
                workspace_root=workspace_root,
                path=repair_brief_path,
            ),
        ),
        changed_at_utc=timestamp,
    )
    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    _write_json_payload(metadata_path, metadata.to_dict())
    _touch_manifest_timestamp(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        updated_at_utc=timestamp,
    )
    return metadata_path


def create_run_manifest(
    workspace_root: Path,
    work_item: str,
    run_id: str,
    runtime_id: str,
    stage_target: str,
    config_snapshot: dict[str, Any],
    *,
    workflow_stage_start: str | None = None,
    workflow_stage_end: str | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    repository_root: Path | None = None,
) -> Path:
    manifest_path = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if manifest_path.exists():
        return manifest_path

    run_stage_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage_target,
    ).mkdir(parents=True, exist_ok=True)

    now = _format_utc_timestamp()
    resolved_repository_root = _resolve_repository_root(
        contracts_root=contracts_root,
        repository_root=repository_root,
    )
    resource_source = _classify_resource_source(resolved_repository_root)
    repository_git_sha = _resolve_repository_git_sha(resolved_repository_root)
    prompt_pack_provenance = _collect_prompt_pack_provenance(
        stage_target=stage_target,
        contracts_root=contracts_root,
        resource_root=resolved_repository_root,
    )
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "work_item_id": work_item,
        "runtime_id": runtime_id,
        "stage_target": stage_target,
        "workflow_bounds": {
            "start": workflow_stage_start,
            "end": workflow_stage_end,
        },
        "config_snapshot": config_snapshot,
        "repository_git_sha": repository_git_sha,
        "resource_source": resource_source,
        "resource_root": resolved_repository_root.as_posix(),
        "prompt_pack_provenance": [entry.to_dict() for entry in prompt_pack_provenance],
        "created_at_utc": now,
        "updated_at_utc": now,
    }
    _write_json_payload(manifest_path, payload)
    return manifest_path


@dataclass(frozen=True)
class RunStore:
    workspace_root: Path
    work_item: str
    run_id: str

    @property
    def root(self) -> Path:
        return run_root(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
        )

    def manifest_path(self) -> Path:
        return run_manifest_path(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
        )

    def create_manifest(
        self,
        runtime_id: str,
        stage_target: str,
        config_snapshot: dict[str, Any],
        *,
        workflow_stage_start: str | None = None,
        workflow_stage_end: str | None = None,
        contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
        repository_root: Path | None = None,
    ) -> Path:
        return create_run_manifest(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            runtime_id=runtime_id,
            stage_target=stage_target,
            config_snapshot=config_snapshot,
            workflow_stage_start=workflow_stage_start,
            workflow_stage_end=workflow_stage_end,
            contracts_root=contracts_root,
            repository_root=repository_root,
        )

    def create_next_attempt(
        self,
        stage: str,
        *,
        contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
        repository_root: Path | None = None,
    ) -> Path:
        return create_next_attempt_directory(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            stage=stage,
            contracts_root=contracts_root,
            repository_root=repository_root,
        )

    def attempt_artifact_index_path(self, stage: str, attempt_number: int) -> Path:
        return run_attempt_artifact_index_path(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            stage=stage,
            attempt_number=attempt_number,
        )

    def write_attempt_artifact_index(
        self,
        stage: str,
        attempt_number: int,
        *,
        changed_at_utc: datetime | None = None,
        contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
        repository_root: Path | None = None,
    ) -> Path:
        return write_attempt_artifact_index(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            stage=stage,
            attempt_number=attempt_number,
            changed_at_utc=changed_at_utc,
            contracts_root=contracts_root,
            repository_root=repository_root,
        )

    def stage_metadata_path(self, stage: str) -> Path:
        return run_stage_metadata_path(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            stage=stage,
        )

    def persist_stage_status(
        self,
        stage: str,
        status: str,
        *,
        changed_at_utc: datetime | None = None,
    ) -> Path:
        return persist_stage_status(
            workspace_root=self.workspace_root,
            work_item=self.work_item,
            run_id=self.run_id,
            stage=stage,
            status=status,
            changed_at_utc=changed_at_utc,
        )

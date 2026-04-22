from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aidd.core.run_lookup import (
    ClosedRunError,
    CorruptedRunError,
    guard_latest_run_resume,
    guard_run_resume,
    latest_attempt_number,
    latest_run_id,
    resolve_attempt_artifact_paths,
)
from aidd.core.run_store import load_stage_metadata, run_attempt_root, run_manifest_path
from aidd.core.run_store import run_stages_root as run_stage_roots_path


@dataclass(frozen=True, slots=True)
class ResolvedCliRunTarget:
    run_id: str
    stage: str
    attempt_number: int
    attempt_path: Path
    documents: dict[str, Path]
    logs: dict[str, Path]


@dataclass(frozen=True, slots=True)
class StageResultSummary:
    run_id: str
    stage: str
    runtime_id: str
    final_state: str
    attempt_count: int
    validator_pass_count: int
    validator_fail_count: int
    validator_report_path: str
    log_artifact_paths: tuple[str, ...]
    document_artifact_paths: tuple[str, ...]
    repair_output_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RunStageMetadataSummary:
    stage: str
    status: str
    updated_at_utc: str
    attempt_count: int


@dataclass(frozen=True, slots=True)
class RunMetadataSummary:
    run_id: str
    work_item: str
    runtime_id: str
    stage_target: str
    created_at_utc: str
    updated_at_utc: str
    stages: tuple[RunStageMetadataSummary, ...]


@dataclass(frozen=True, slots=True)
class RunLogSummary:
    run_id: str
    stage: str
    attempt_number: int
    runtime_log_path: Path


def _load_runtime_id(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> str:
    manifest = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not manifest.exists():
        raise ValueError(
            f"Run manifest is missing for work item '{work_item}', run '{run_id}'."
        )

    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Run manifest is not valid JSON for work item '{work_item}', run '{run_id}'."
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError(
            f"Run manifest must be a JSON object for work item '{work_item}', run '{run_id}'."
        )
    runtime = str(payload.get("runtime_id", "")).strip()
    if not runtime:
        raise ValueError(
            f"Run manifest runtime_id is missing for work item '{work_item}', run '{run_id}'."
        )
    return runtime


def _load_manifest_payload(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> dict[str, Any]:
    manifest = run_manifest_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    if not manifest.exists():
        raise ValueError(
            f"Run manifest is missing for work item '{work_item}', run '{run_id}'."
        )
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Run manifest is not valid JSON for work item '{work_item}', run '{run_id}'."
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"Run manifest must be a JSON object for work item '{work_item}', run '{run_id}'."
        )
    return payload


def resolve_run_metadata_summary(
    workspace_root: Path,
    work_item: str,
    *,
    run_id: str | None = None,
) -> RunMetadataSummary:
    selected_run_id = run_id or latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected_run_id is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")

    manifest_payload = _load_manifest_payload(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
    )
    runtime_id = str(manifest_payload.get("runtime_id", "")).strip()
    if not runtime_id:
        raise ValueError(
            "Run manifest runtime_id is missing for work item "
            f"'{work_item}', run '{selected_run_id}'."
        )
    stage_target = str(manifest_payload.get("stage_target", "")).strip()
    if not stage_target:
        raise ValueError(
            "Run manifest stage_target is missing for work item "
            f"'{work_item}', run '{selected_run_id}'."
        )
    created_at_utc = str(manifest_payload.get("created_at_utc", "")).strip()
    updated_at_utc = str(manifest_payload.get("updated_at_utc", "")).strip()

    stage_roots = run_stage_roots_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
    )
    stage_summaries: list[RunStageMetadataSummary] = []
    if stage_roots.exists():
        for child in sorted(stage_roots.iterdir(), key=lambda path: path.name):
            if not child.is_dir():
                continue
            stage_name = child.name
            stage_metadata = load_stage_metadata(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=selected_run_id,
                stage=stage_name,
            )
            if stage_metadata is None:
                continue
            attempts = latest_attempt_number(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=selected_run_id,
                stage=stage_name,
            )
            stage_summaries.append(
                RunStageMetadataSummary(
                    stage=stage_name,
                    status=stage_metadata.status,
                    updated_at_utc=stage_metadata.updated_at_utc,
                    attempt_count=attempts or 0,
                )
            )

    return RunMetadataSummary(
        run_id=selected_run_id,
        work_item=work_item,
        runtime_id=runtime_id,
        stage_target=stage_target,
        created_at_utc=created_at_utc,
        updated_at_utc=updated_at_utc,
        stages=tuple(stage_summaries),
    )


def resolve_run_log_summary(
    workspace_root: Path,
    work_item: str,
    stage: str,
    *,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunLogSummary:
    selected_run_id = run_id or latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected_run_id is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")

    selected_attempt = attempt_number or latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if selected_attempt is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )

    artifact_paths = resolve_attempt_artifact_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if artifact_paths is None:
        raise ValueError(
            f"Artifact index is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}', attempt {selected_attempt}."
        )

    runtime_log_path = artifact_paths.logs.get("runtime_log")
    if runtime_log_path is None:
        raise ValueError(
            "Runtime log path is missing in artifact index for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}', attempt {selected_attempt}."
        )
    if not runtime_log_path.exists():
        raise ValueError(
            f"Runtime log file does not exist: {runtime_log_path.as_posix()}."
        )

    return RunLogSummary(
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        runtime_log_path=runtime_log_path,
    )


def _workspace_relative_path(workspace_root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def _validator_counts_from_history(*, outcomes: tuple[str, ...]) -> tuple[int, int]:
    pass_count = 0
    fail_count = 0
    for outcome in outcomes:
        normalized = outcome.strip().lower()
        if "fail" in normalized:
            fail_count += 1
            continue
        if "pass" in normalized or "succeed" in normalized:
            pass_count += 1
    return pass_count, fail_count


def _validator_verdict_from_report(report_path: Path) -> str | None:
    if not report_path.exists():
        return None

    for line in report_path.read_text(encoding="utf-8").splitlines():
        matched = re.search(r"- Verdict:\s*`(?P<verdict>pass|fail)`", line)
        if matched is not None:
            return matched.group("verdict")
    return None


def _normalize_repair_output_paths(
    *,
    workspace_root: Path,
    repair_history_paths: tuple[str, ...],
    stage_root: Path,
) -> tuple[str, ...]:
    collected = {path.strip() for path in repair_history_paths if path.strip()}
    repair_brief = stage_root / "repair-brief.md"
    if repair_brief.exists():
        collected.add(_workspace_relative_path(workspace_root, repair_brief))
    return tuple(sorted(collected))


def resolve_stage_result_summary(
    workspace_root: Path,
    work_item: str,
    stage: str,
    *,
    run_id: str | None = None,
) -> StageResultSummary:
    selected_run_id = run_id or latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected_run_id is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")

    stage_metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if stage_metadata is None:
        raise ValueError(
            f"Stage metadata is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}'."
        )

    attempts = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if attempts is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )

    stage_root = workspace_root / "workitems" / work_item / "stages" / stage
    validator_report = stage_root / "validator-report.md"
    pass_count, fail_count = _validator_counts_from_history(
        outcomes=tuple(entry.outcome for entry in stage_metadata.repair_history)
    )
    if pass_count == 0 and fail_count == 0:
        verdict = _validator_verdict_from_report(validator_report)
        if verdict == "pass":
            pass_count = 1
        elif verdict == "fail":
            fail_count = 1

    artifact_paths = resolve_attempt_artifact_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=attempts,
    )
    log_artifact_paths = (
        tuple(
            sorted(
                _workspace_relative_path(workspace_root, path)
                for path in artifact_paths.logs.values()
            )
        )
        if artifact_paths is not None
        else ()
    )
    document_artifact_paths = (
        tuple(
            sorted(
                _workspace_relative_path(workspace_root, path)
                for path in artifact_paths.documents.values()
            )
        )
        if artifact_paths is not None
        else ()
    )
    repair_output_paths = _normalize_repair_output_paths(
        workspace_root=workspace_root,
        repair_history_paths=tuple(
            entry.repair_brief_path or "" for entry in stage_metadata.repair_history
        ),
        stage_root=stage_root,
    )

    return StageResultSummary(
        run_id=selected_run_id,
        stage=stage,
        runtime_id=_load_runtime_id(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=selected_run_id,
        ),
        final_state=stage_metadata.status,
        attempt_count=attempts,
        validator_pass_count=pass_count,
        validator_fail_count=fail_count,
        validator_report_path=_workspace_relative_path(workspace_root, validator_report),
        log_artifact_paths=log_artifact_paths,
        document_artifact_paths=document_artifact_paths,
        repair_output_paths=repair_output_paths,
    )


def resolve_cli_run_target(
    workspace_root: Path,
    work_item: str,
    stage: str,
    *,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> ResolvedCliRunTarget:
    try:
        if run_id is None:
            selected_run_id = guard_latest_run_resume(
                workspace_root=workspace_root,
                work_item=work_item,
                stage=stage,
            )
        else:
            selected_run_id = run_id
            guard_run_resume(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=selected_run_id,
                stage=stage,
            )
    except (ClosedRunError, CorruptedRunError) as exc:
        raise ValueError(str(exc)) from exc

    selected_attempt = attempt_number or latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if selected_attempt is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )

    attempt_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if not attempt_path.exists():
        raise ValueError(
            f"Attempt path does not exist for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}', attempt {selected_attempt}."
        )

    artifact_paths = resolve_attempt_artifact_paths(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if artifact_paths is None:
        raise ValueError(
            f"Artifact index is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}', attempt {selected_attempt}."
        )

    return ResolvedCliRunTarget(
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        attempt_path=attempt_path,
        documents=artifact_paths.documents,
        logs=artifact_paths.logs,
    )

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

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

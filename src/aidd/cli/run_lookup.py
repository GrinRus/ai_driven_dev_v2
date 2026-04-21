from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.core.run_lookup import (
    ClosedRunError,
    CorruptedRunError,
    guard_latest_run_resume,
    guard_run_resume,
    latest_attempt_number,
    resolve_attempt_artifact_paths,
)
from aidd.core.run_store import run_attempt_root


@dataclass(frozen=True, slots=True)
class ResolvedCliRunTarget:
    run_id: str
    stage: str
    attempt_number: int
    attempt_path: Path
    documents: dict[str, Path]
    logs: dict[str, Path]


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

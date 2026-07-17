from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from aidd.core.run_inspection import resolve_run_metadata_summary
from aidd.core.run_lookup import latest_attempt_number
from aidd.core.run_store import (
    RUN_RUNTIME_EXIT_METADATA_FILENAME,
    load_attempt_artifact_index,
    run_attempt_root,
    work_item_runs_root,
)
from aidd.core.stages import STAGES

RuntimeLaunchOutcomeName = Literal[
    "success",
    "runtime_failure",
    "timeout",
    "cancellation",
    "denial",
    "blocked",
    "launch_failure",
    "unknown",
]
_CANONICAL_OUTCOMES = frozenset(
    {
        "success",
        "runtime_failure",
        "timeout",
        "cancellation",
        "denial",
        "blocked",
        "launch_failure",
    }
)
_LEGACY_CLASSIFICATIONS = {
    "success": "success",
    "cancelled": "cancellation",
    "canceled": "cancellation",
    "timeout": "timeout",
    "denied": "denial",
    "blocked": "blocked",
    "launch_failure": "launch_failure",
    "provider_error": "runtime_failure",
    "failed": "runtime_failure",
}


@dataclass(frozen=True, slots=True)
class RuntimeLaunchOutcome:
    runtime_id: str
    outcome: RuntimeLaunchOutcomeName
    recorded_at_utc: str | None
    run_id: str
    stage: str
    attempt_number: int
    evidence_path: str
    warning: str | None = None


def _read_outcome(path: Path) -> tuple[RuntimeLaunchOutcomeName, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "unknown", "runtime-exit.json is unreadable or malformed"
    if not isinstance(payload, dict):
        return "unknown", "runtime-exit.json is not an object"
    adapter_outcome = str(payload.get("adapter_outcome") or "").strip().lower()
    if adapter_outcome in _CANONICAL_OUTCOMES:
        return cast(RuntimeLaunchOutcomeName, adapter_outcome), None
    classification = str(payload.get("exit_classification") or "").strip().lower()
    legacy = _LEGACY_CLASSIFICATIONS.get(classification)
    if legacy is not None:
        return (
            cast(RuntimeLaunchOutcomeName, legacy),
            "legacy runtime evidence has no canonical adapter_outcome",
        )
    return "unknown", "runtime evidence has no recognized canonical outcome"


def resolve_runtime_launch_history(
    *,
    workspace_root: Path,
    work_item: str,
) -> dict[str, RuntimeLaunchOutcome]:
    runs_root = work_item_runs_root(workspace_root=workspace_root, work_item=work_item)
    if not runs_root.exists():
        return {}
    selected: dict[str, tuple[tuple[str, str, int, int], RuntimeLaunchOutcome]] = {}
    for run_candidate in sorted(runs_root.iterdir(), key=lambda path: path.name):
        if not run_candidate.is_dir():
            continue
        try:
            metadata = resolve_run_metadata_summary(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_candidate.name,
            )
        except ValueError:
            continue
        for stage in STAGES:
            attempt_count = latest_attempt_number(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=metadata.run_id,
                stage=stage,
            )
            if attempt_count is None:
                continue
            for attempt_number in range(1, attempt_count + 1):
                attempt_path = run_attempt_root(
                    workspace_root=workspace_root,
                    work_item=work_item,
                    run_id=metadata.run_id,
                    stage=stage,
                    attempt_number=attempt_number,
                )
                exit_path = attempt_path / RUN_RUNTIME_EXIT_METADATA_FILENAME
                if not exit_path.is_file():
                    continue
                outcome, warning = _read_outcome(exit_path)
                try:
                    index = load_attempt_artifact_index(
                        workspace_root=workspace_root,
                        work_item=work_item,
                        run_id=metadata.run_id,
                        stage=stage,
                        attempt_number=attempt_number,
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    index = None
                    warning = "artifact index is malformed; launch timestamp is unavailable"
                recorded_at_utc = None if index is None else index.updated_at_utc
                if index is None and warning is None:
                    warning = "legacy attempt has no artifact index timestamp"
                evidence_path = exit_path.resolve(strict=False).relative_to(
                    workspace_root.resolve(strict=False)
                ).as_posix()
                item = RuntimeLaunchOutcome(
                    runtime_id=metadata.runtime_id,
                    outcome=outcome,
                    recorded_at_utc=recorded_at_utc,
                    run_id=metadata.run_id,
                    stage=stage,
                    attempt_number=attempt_number,
                    evidence_path=evidence_path,
                    warning=warning,
                )
                ordering = (
                    recorded_at_utc or metadata.updated_at_utc,
                    metadata.run_id,
                    STAGES.index(stage),
                    attempt_number,
                )
                current = selected.get(metadata.runtime_id)
                if current is None or ordering > current[0]:
                    selected[metadata.runtime_id] = (ordering, item)
    return {runtime_id: item for runtime_id, (_, item) in selected.items()}


__all__ = ["RuntimeLaunchOutcome", "resolve_runtime_launch_history"]

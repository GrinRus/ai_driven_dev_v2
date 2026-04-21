from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.core.workspace import WORKSPACE_REPORTS_DIRNAME, WORKSPACE_REPORTS_RUNS_DIRNAME

RUN_STAGES_DIRNAME = "stages"
RUN_ATTEMPTS_DIRNAME = "attempts"
RUN_ATTEMPT_PREFIX = "attempt-"


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

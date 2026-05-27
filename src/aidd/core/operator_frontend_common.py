from __future__ import annotations

from pathlib import Path

from aidd.core.stages import STAGES, is_valid_stage


def validate_operator_stage(stage: str) -> None:
    if not is_valid_stage(stage):
        raise ValueError(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}.")


def operator_answers_path(*, workspace_root: Path, work_item: str, stage: str) -> Path:
    return workspace_root / "workitems" / work_item / "stages" / stage / "answers.md"


__all__ = ["operator_answers_path", "validate_operator_stage"]

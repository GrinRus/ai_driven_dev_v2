from __future__ import annotations

from pathlib import Path
from typing import Literal

from aidd.core.bounded_log_reader import (
    DEFAULT_LOG_READ_BYTES,
    MAX_LOG_READ_BYTES,
    read_bounded_log,
)
from aidd.core.operator_frontend_common import validate_operator_stage
from aidd.core.operator_frontend_models import OperatorRunLogView, OperatorRunView
from aidd.core.run_inspection import (
    RunLogSummary,
    resolve_run_log_summary,
    resolve_run_metadata_summary,
)


def resolve_operator_run_view(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str | None = None,
) -> OperatorRunView:
    return OperatorRunView(
        metadata=resolve_run_metadata_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        )
    )


def _bounded_operator_run_log(
    summary: RunLogSummary,
    *,
    tail_bytes: int | None,
    limit_bytes: int | None,
) -> OperatorRunLogView:
    mode: Literal["head", "tail"]
    if tail_bytes is not None:
        mode = "tail"
        requested_bytes = tail_bytes
    elif limit_bytes is not None:
        mode = "head"
        requested_bytes = limit_bytes
    else:
        mode = "tail"
        requested_bytes = DEFAULT_LOG_READ_BYTES
    bounded = read_bounded_log(
        summary.runtime_log_path,
        mode=mode,
        requested_bytes=requested_bytes,
        max_bytes=MAX_LOG_READ_BYTES,
    )
    return OperatorRunLogView(
        summary=summary,
        text=bounded.text,
        byte_size=bounded.byte_size,
        start_byte=bounded.start_byte,
        end_byte=bounded.end_byte,
        retained_bytes=bounded.retained_bytes,
        requested_bytes=bounded.requested_bytes,
        max_bytes=bounded.max_bytes,
        truncated=bounded.truncated,
        truncated_head=bounded.truncated_head,
        truncated_tail=bounded.truncated_tail,
        partial_head_line=bounded.partial_head_line,
        partial_tail_line=bounded.partial_tail_line,
        oversized_line=bounded.oversized_line,
    )


def resolve_operator_run_log_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
    tail_bytes: int | None = None,
    limit_bytes: int | None = None,
) -> OperatorRunLogView:
    validate_operator_stage(stage)
    if tail_bytes is not None and limit_bytes is not None:
        raise ValueError("Provide only one of tail_bytes or limit_bytes.")
    if tail_bytes is not None and tail_bytes <= 0:
        raise ValueError("tail_bytes must be greater than zero.")
    if limit_bytes is not None and limit_bytes <= 0:
        raise ValueError("limit_bytes must be greater than zero.")

    summary = resolve_run_log_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        attempt_number=attempt_number,
    )
    return _bounded_operator_run_log(summary, tail_bytes=tail_bytes, limit_bytes=limit_bytes)

__all__ = ["resolve_operator_run_log_view", "resolve_operator_run_view"]

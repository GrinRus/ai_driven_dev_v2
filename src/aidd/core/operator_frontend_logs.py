from __future__ import annotations

from pathlib import Path

from aidd.core.operator_frontend_common import validate_operator_stage
from aidd.core.operator_frontend_models import OperatorRunLogView, OperatorRunView
from aidd.core.run_inspection import (
    RunLogSummary,
    resolve_run_log_summary,
    resolve_run_metadata_summary,
)

_DEFAULT_LOG_TAIL_BYTES = 64 * 1024
_MAX_LOG_READ_BYTES = 256 * 1024

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
    byte_size = summary.runtime_log_path.stat().st_size
    if tail_bytes is not None:
        requested_bytes = min(tail_bytes, _MAX_LOG_READ_BYTES)
        start_byte = max(0, byte_size - requested_bytes)
        end_byte = byte_size
    elif limit_bytes is not None:
        requested_bytes = min(limit_bytes, _MAX_LOG_READ_BYTES)
        start_byte = 0
        end_byte = min(byte_size, requested_bytes)
    else:
        requested_bytes = _DEFAULT_LOG_TAIL_BYTES
        start_byte = max(0, byte_size - requested_bytes)
        end_byte = byte_size

    with summary.runtime_log_path.open("rb") as file_obj:
        file_obj.seek(start_byte)
        raw_text = file_obj.read(end_byte - start_byte)

    return OperatorRunLogView(
        summary=summary,
        text=raw_text.decode("utf-8", errors="replace"),
        byte_size=byte_size,
        start_byte=start_byte,
        end_byte=end_byte,
        requested_bytes=requested_bytes,
        max_bytes=_MAX_LOG_READ_BYTES,
        truncated=start_byte > 0 or end_byte < byte_size,
        truncated_head=start_byte > 0,
        truncated_tail=end_byte < byte_size,
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

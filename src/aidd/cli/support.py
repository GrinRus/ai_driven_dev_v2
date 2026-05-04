from __future__ import annotations

import shlex
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from rich.console import Console

from aidd.adapters.base import CapabilityReport
from aidd.adapters.runtime_registry import RuntimeExecutionMode, runtime_ids
from aidd.config import AiddConfig
from aidd.core.run_inspection import resolve_run_metadata_summary
from aidd.core.run_store import work_item_runs_root
from aidd.core.stages import STAGES

console = Console(no_color=True)
_STAGE_RUN_SUPPORTED_RUNTIMES: tuple[str, ...] = runtime_ids()
_WORKFLOW_RUN_SUPPORTED_RUNTIMES: tuple[str, ...] = _STAGE_RUN_SUPPORTED_RUNTIMES


def _capability_summary(report: CapabilityReport) -> str:
    capability_pairs = (
        ("raw-log", report.supports_raw_log_stream),
        ("structured-log", report.supports_structured_log_stream),
        ("questions", report.supports_questions),
        ("resume", report.supports_resume),
        ("subagents", report.supports_subagents),
        ("non-interactive", report.supports_non_interactive_mode),
        ("cwd-control", report.supports_working_directory_control),
        ("env-injection", report.supports_env_injection),
    )
    enabled = [name for name, is_enabled in capability_pairs if is_enabled]
    return ", ".join(enabled) if enabled else "none"


def _path_summary(paths: tuple[str, ...]) -> str:
    if not paths:
        return "none"
    return "\n".join(paths)


def _runtime_command_for_runtime(*, runtime: str, cfg: AiddConfig) -> str:
    return cfg.runtime_config(runtime).command


def _runtime_execution_mode_for_runtime(
    *,
    runtime: str,
    cfg: AiddConfig,
) -> RuntimeExecutionMode:
    return cfg.runtime_config(runtime).execution_mode


def _runtime_timeout_for_runtime(
    *,
    runtime: str,
    cfg: AiddConfig,
    stage: str | None = None,
) -> float | None:
    runtime_config = cfg.runtime_config(runtime)
    if stage is not None and stage in runtime_config.stage_timeout_seconds:
        return runtime_config.stage_timeout_seconds[stage]
    return runtime_config.timeout_seconds


def _active_prompt_pack_paths(
    *,
    prompt_pack_paths: tuple[Path, ...],
    repair_mode: bool,
) -> tuple[Path, ...]:
    if repair_mode:
        return prompt_pack_paths
    return tuple(path for path in prompt_pack_paths if path.name != "repair.md")


def _execution_command_available(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    return bool(tokens) and shutil.which(tokens[0]) is not None


def _tail_lines(text: str, *, line_count: int) -> str:
    lines = text.splitlines()
    if line_count >= len(lines):
        return text
    return "\n".join(lines[-line_count:]) + "\n"


def _stream_prefix(*, runtime: str, stage: str, stream: Literal["stdout", "stderr"]) -> str:
    return f"[{runtime}:{stage}:{stream}]"


def _prefix_stream_chunk(
    *,
    runtime: str,
    stage: str,
    stream: Literal["stdout", "stderr"],
    chunk: str,
    multi_stream: bool,
) -> str:
    if not multi_stream:
        return chunk

    prefix = _stream_prefix(runtime=runtime, stage=stage, stream=stream)
    lines = chunk.splitlines(keepends=True)
    if not lines:
        return f"{prefix} "
    return "".join(f"{prefix} {line}" for line in lines)


def _allocate_stage_run_id(*, workspace_root: Path, work_item: str) -> str:
    base_run_id = f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    runs_root = work_item_runs_root(workspace_root=workspace_root, work_item=work_item)
    candidate = base_run_id
    suffix = 2
    while (runs_root / candidate).exists():
        candidate = f"{base_run_id}-{suffix:02d}"
        suffix += 1
    return candidate


def _print_workflow_run_summary(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage_start: str | None = None,
    stage_end: str | None = None,
) -> None:
    summary = resolve_run_metadata_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    normalized_stage_start = stage_start or summary.workflow_stage_start or STAGES[0]
    normalized_stage_end = stage_end or summary.workflow_stage_end or summary.stage_target
    console.print(
        "Workflow summary: "
        f"run_id={summary.run_id} runtime={summary.runtime_id} "
        f"stage_bounds={normalized_stage_start}->{normalized_stage_end}"
    )
    if not summary.stages:
        console.print("- no stage metadata recorded")
        return
    for stage_summary in summary.stages:
        console.print(
            f"- {stage_summary.stage}: "
            f"status={stage_summary.status} attempts={stage_summary.attempt_count}"
        )

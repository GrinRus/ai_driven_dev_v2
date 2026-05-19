from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import typer

from aidd.adapters.runtime_execution import StageRuntimeRequest
from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.cli.support import (
    _STAGE_RUN_SUPPORTED_RUNTIMES,
    _active_prompt_pack_paths,
    _allocate_stage_run_id,
    _prefix_stream_chunk,
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    _runtime_timeout_for_runtime,
    console,
)
from aidd.config import load_config
from aidd.core.project_set import ResolvedProjectSet, resolve_project_set
from aidd.core.repair import (
    RepairBudgetPolicy,
    generate_repair_brief,
    persist_repair_history_snapshot,
    write_repair_brief,
)
from aidd.core.run_lookup import latest_run_id
from aidd.core.run_store import (
    RUN_RUNTIME_LOG_FILENAME,
    create_run_manifest,
    load_stage_metadata,
)
from aidd.core.stage_registry import resolve_prompt_pack_file_paths
from aidd.core.stage_runner import (
    AdapterExecutionOutcome,
    AdapterInvocationBundle,
    PostValidationAction,
    StageExecutionState,
    StageOrchestrationResult,
    run_single_stage_orchestration,
    update_stage_unblock_state,
)
from aidd.core.stages import STAGES, is_valid_stage
from aidd.core.state_machine import StageState
from aidd.core.workspace import stage_root as workspace_stage_root


@dataclass(frozen=True, slots=True)
class StageRunOptions:
    stage: str
    work_item: str
    runtime: str
    run_id: str | None
    root: Path | None
    config: Path
    log_follow: bool


@dataclass(frozen=True, slots=True)
class StageRunRuntimeConfig:
    workspace_root: Path
    repository_root: Path
    runtime_command: str
    runtime_execution_mode: RuntimeExecutionMode
    runtime_timeout_seconds: float | None
    repair_policy: RepairBudgetPolicy
    project_set: ResolvedProjectSet | None


def _validate_stage_run_options(options: StageRunOptions) -> None:
    if not is_valid_stage(options.stage):
        raise typer.BadParameter(
            f"Unknown stage '{options.stage}'. Expected one of: {', '.join(STAGES)}"
        )
    if options.runtime not in _STAGE_RUN_SUPPORTED_RUNTIMES:
        supported = ", ".join(_STAGE_RUN_SUPPORTED_RUNTIMES)
        raise typer.BadParameter(
            f"Unsupported runtime '{options.runtime}'. Supported runtimes: {supported}."
        )


def _resolve_stage_run_config(options: StageRunOptions) -> StageRunRuntimeConfig:
    cfg = load_config(options.config)
    workspace_root = (
        options.root if options.root is not None else cfg.workspace_root
    ).resolve(strict=False)
    repository_root = Path.cwd().resolve(strict=True)
    project_set = (
        resolve_project_set(
            repository_root=repository_root,
            project_set=cfg.project_set,
        )
        if cfg.project_set.projects
        else None
    )
    return StageRunRuntimeConfig(
        workspace_root=workspace_root,
        repository_root=repository_root,
        runtime_command=_runtime_command_for_runtime(runtime=options.runtime, cfg=cfg),
        runtime_execution_mode=_runtime_execution_mode_for_runtime(
            runtime=options.runtime,
            cfg=cfg,
        ),
        runtime_timeout_seconds=_runtime_timeout_for_runtime(
            runtime=options.runtime,
            cfg=cfg,
            stage=options.stage,
        ),
        repair_policy=RepairBudgetPolicy(default_max_repair_attempts=cfg.max_repair_attempts),
        project_set=project_set,
    )


def _selected_or_new_run_id(
    *,
    options: StageRunOptions,
    runtime_config: StageRunRuntimeConfig,
) -> tuple[str, bool]:
    selected_run_id: str | None = None
    if options.run_id is not None:
        normalized_run_id = options.run_id.strip()
        if not normalized_run_id:
            raise typer.BadParameter("Option '--run-id' must not be empty.")
        selected_run_id = normalized_run_id
    else:
        latest_existing_run = latest_run_id(
            workspace_root=runtime_config.workspace_root,
            work_item=options.work_item,
        )
        if latest_existing_run is not None:
            latest_stage_metadata = load_stage_metadata(
                workspace_root=runtime_config.workspace_root,
                work_item=options.work_item,
                run_id=latest_existing_run,
                stage=options.stage,
            )
            if (
                latest_stage_metadata is not None
                and latest_stage_metadata.status.lower() == StageState.BLOCKED.value
            ):
                selected_run_id = latest_existing_run

    is_resume_candidate = False
    if selected_run_id is not None:
        selected_stage_metadata = load_stage_metadata(
            workspace_root=runtime_config.workspace_root,
            work_item=options.work_item,
            run_id=selected_run_id,
            stage=options.stage,
        )
        is_resume_candidate = (
            selected_stage_metadata is not None
            and selected_stage_metadata.status.lower() == StageState.BLOCKED.value
        )

    run_id = selected_run_id or _allocate_stage_run_id(
        workspace_root=runtime_config.workspace_root,
        work_item=options.work_item,
    )
    return run_id, is_resume_candidate


def _stream_runtime_chunk(
    *,
    options: StageRunOptions,
    stream: Literal["stdout", "stderr"],
    chunk: str,
) -> None:
    if not options.log_follow:
        return
    prefixed_chunk = _prefix_stream_chunk(
        runtime=options.runtime,
        stage=options.stage,
        stream=stream,
        chunk=chunk,
        multi_stream=True,
    )
    console.print(prefixed_chunk, end="", markup=False, highlight=False)


def _execute_adapter_invocation(
    *,
    options: StageRunOptions,
    runtime_config: StageRunRuntimeConfig,
    prompt_pack_file_paths: tuple[Path, ...],
    invocation: AdapterInvocationBundle,
    execution_state: StageExecutionState,
) -> AdapterExecutionOutcome:
    stage_documents_root = workspace_stage_root(
        root=runtime_config.workspace_root,
        work_item=invocation.work_item,
        stage=invocation.stage,
    )
    stage_documents_root.mkdir(parents=True, exist_ok=True)
    stage_brief_path = stage_documents_root / "stage-brief.md"
    stage_brief_path.write_text(invocation.stage_brief_markdown, encoding="utf-8")
    prompt_pack_paths_for_runtime = _active_prompt_pack_paths(
        prompt_pack_paths=tuple(prompt_pack_file_paths),
        repair_mode=invocation.repair_mode,
    )
    runtime_request = StageRuntimeRequest(
        runtime_id=options.runtime,
        execution_mode=runtime_config.runtime_execution_mode,
        timeout_seconds=runtime_config.runtime_timeout_seconds,
        stage=invocation.stage,
        work_item=invocation.work_item,
        run_id=invocation.run_id,
        workspace_root=runtime_config.workspace_root,
        stage_brief_path=stage_brief_path,
        prompt_pack_paths=prompt_pack_paths_for_runtime,
        repository_root=runtime_config.repository_root,
        expected_output_documents=invocation.expected_output_documents,
        attempt_number=invocation.attempt_number,
        repair_mode=invocation.repair_mode,
        input_bundle_path=invocation.input_bundle_path,
        repair_brief_path=invocation.repair_brief_path,
        repair_context_markdown=invocation.repair_context_markdown,
    )

    def _on_stdout(chunk: str) -> None:
        _stream_runtime_chunk(options=options, stream="stdout", chunk=chunk)

    def _on_stderr(chunk: str) -> None:
        _stream_runtime_chunk(options=options, stream="stderr", chunk=chunk)

    on_stdout = _on_stdout if options.log_follow else None
    on_stderr = _on_stderr if options.log_follow else None
    try:
        adapter_result = get_runtime_adapter_surface(options.runtime).execute_stage_request(
            configured_command=runtime_config.runtime_command,
            request=runtime_request,
            attempt_path=execution_state.attempt_path,
            base_env=dict(os.environ),
            on_stdout=on_stdout,
            on_stderr=on_stderr,
        )
        return AdapterExecutionOutcome(
            succeeded=adapter_result.succeeded,
            details=adapter_result.details,
        )
    except ValueError:
        if options.runtime not in _STAGE_RUN_SUPPORTED_RUNTIMES:
            return AdapterExecutionOutcome(
                succeeded=False,
                details=f"unsupported-runtime: {options.runtime}",
            )
        raise
    except OSError as exc:
        return AdapterExecutionOutcome(
            succeeded=False,
            details=f"runtime-launch-error: {exc}",
        )


def _write_repair_brief_for_retry(
    *,
    orchestration: StageOrchestrationResult,
    runtime_config: StageRunRuntimeConfig,
) -> Path:
    if orchestration.validation_result is None:
        raise ValueError("Repair retry requires validator findings from the previous attempt.")

    validator_report_path = orchestration.validation_result.validator_report_path
    repair_brief_path = validator_report_path.parent / "repair-brief.md"
    repair_brief = generate_repair_brief(
        validator_report_path=validator_report_path,
        prior_stage_artifacts=orchestration.adapter_invocation.expected_input_bundle,
        stage_attempt_count=orchestration.execution_state.attempt_number,
        max_repair_attempts=runtime_config.repair_policy.default_max_repair_attempts,
        workspace_root=runtime_config.workspace_root,
    )
    write_repair_brief(path=repair_brief_path, repair_brief_markdown=repair_brief)
    persist_repair_history_snapshot(
        workspace_root=runtime_config.workspace_root,
        work_item=orchestration.work_item,
        run_id=orchestration.run_id,
        stage=orchestration.stage,
        attempt_number=orchestration.execution_state.attempt_number,
        trigger=(
            "initial"
            if orchestration.execution_state.attempt_number == 1
            else "repair"
        ),
        outcome="failed validation",
        stage_status=orchestration.transition.next_state.value,
        validator_report_path=validator_report_path,
        repair_brief_path=repair_brief_path,
    )
    return repair_brief_path


def _run_stage_attempts(
    *,
    options: StageRunOptions,
    runtime_config: StageRunRuntimeConfig,
    run_id: str,
    prompt_pack_file_paths: tuple[Path, ...],
) -> tuple[StageOrchestrationResult, int]:
    orchestration: StageOrchestrationResult | None = None
    stage_attempt_count = 0
    while True:
        unblock_state = update_stage_unblock_state(
            workspace_root=runtime_config.workspace_root,
            work_item=options.work_item,
            run_id=run_id,
            stage=options.stage,
        )
        if unblock_state.was_blocked and not unblock_state.unblocked:
            stage_documents_root = (
                runtime_config.workspace_root
                / "workitems"
                / options.work_item
                / "stages"
                / options.stage
            )
            console.print("Stage run result: action=wait state=blocked")
            if unblock_state.stage_metadata_path is not None:
                console.print(f"Stage metadata: {unblock_state.stage_metadata_path.as_posix()}")
            console.print("Blocking questions are unresolved.")
            console.print(f"Questions: {(stage_documents_root / 'questions.md').as_posix()}")
            console.print(f"Answers: {(stage_documents_root / 'answers.md').as_posix()}")
            raise typer.Exit(code=1)
        if unblock_state.unblocked:
            console.print("Resuming blocked stage after answers were detected.")

        try:
            orchestration = run_single_stage_orchestration(
                workspace_root=runtime_config.workspace_root,
                work_item=options.work_item,
                run_id=run_id,
                stage=options.stage,
                adapter_executor=lambda invocation, execution_state: _execute_adapter_invocation(
                    options=options,
                    runtime_config=runtime_config,
                    prompt_pack_file_paths=prompt_pack_file_paths,
                    invocation=invocation,
                    execution_state=execution_state,
                ),
                repair_policy=runtime_config.repair_policy,
                project_set=runtime_config.project_set,
            )
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"Error: {exc}")
            raise typer.Exit(code=2) from exc

        stage_attempt_count += 1
        if orchestration.transition.action is not PostValidationAction.REPAIR:
            break
        repair_brief_path = _write_repair_brief_for_retry(
            orchestration=orchestration,
            runtime_config=runtime_config,
        )
        console.print(f"Repair brief prepared: {repair_brief_path.as_posix()}")
        console.print(
            "Repair retry scheduled: "
            f"attempt={orchestration.execution_state.attempt_number + 1}"
        )

    assert orchestration is not None
    return orchestration, stage_attempt_count


def _write_run_manifest(
    *,
    options: StageRunOptions,
    runtime_config: StageRunRuntimeConfig,
    run_id: str,
) -> None:
    create_run_manifest(
        workspace_root=runtime_config.workspace_root,
        work_item=options.work_item,
        run_id=run_id,
        runtime_id=options.runtime,
        stage_target=options.stage,
        config_snapshot={
            "config_path": options.config.as_posix(),
            "workspace_root": runtime_config.workspace_root.as_posix(),
            "runtime_command": runtime_config.runtime_command,
            "runtime_execution_mode": runtime_config.runtime_execution_mode.value,
            "runtime_timeout_seconds": runtime_config.runtime_timeout_seconds,
            "log_follow": options.log_follow,
        },
    )


def _print_stage_run_start(
    *,
    options: StageRunOptions,
    run_id: str,
    is_resume_candidate: bool,
) -> None:
    console.print(
        "AIDD stage run: "
        f"stage={options.stage} work_item={options.work_item} runtime={options.runtime} "
        f"log_follow={options.log_follow} run_id={run_id}"
    )
    if is_resume_candidate:
        console.print("Detected blocked stage metadata on the latest run; attempting resume.")
    if options.log_follow:
        console.print("Live-log follow mode enabled for runtime stream output.")


def _print_stage_run_result(
    *,
    orchestration: StageOrchestrationResult,
    stage_attempt_count: int,
) -> None:
    runtime_log_path = orchestration.execution_state.attempt_path / RUN_RUNTIME_LOG_FILENAME
    console.print(
        "Stage run result: "
        f"action={orchestration.transition.action.value} "
        f"state={orchestration.transition.next_state.value}"
    )
    console.print(f"Stage attempts: {stage_attempt_count}")
    console.print(f"Stage metadata: {orchestration.transition.stage_metadata_path.as_posix()}")
    console.print(f"Runtime log: {runtime_log_path.as_posix()}")
    if orchestration.validation_result is not None:
        console.print(
            "Validator report: "
            f"{orchestration.validation_result.validator_report_path.as_posix()}"
        )
    if orchestration.adapter_outcome.details:
        console.print(f"Adapter outcome: {orchestration.adapter_outcome.details}")
    if orchestration.transition.next_state is StageState.BLOCKED:
        questions_path = _expected_stage_document_path(
            orchestration=orchestration,
            document_name="questions.md",
        )
        answers_path = _expected_stage_document_path(
            orchestration=orchestration,
            document_name="answers.md",
        )
        console.print("Blocking questions are unresolved.")
        if questions_path is not None:
            console.print(f"Questions: {questions_path.as_posix()}")
        if answers_path is not None:
            console.print(f"Answers: {answers_path.as_posix()}")


def _expected_stage_document_path(
    *,
    orchestration: StageOrchestrationResult,
    document_name: str,
) -> Path | None:
    for path in orchestration.adapter_invocation.expected_output_documents:
        if path.name == document_name:
            return path
    return None


def run_stage_command(options: StageRunOptions) -> None:
    _validate_stage_run_options(options)
    runtime_config = _resolve_stage_run_config(options)
    run_id, is_resume_candidate = _selected_or_new_run_id(
        options=options,
        runtime_config=runtime_config,
    )
    _write_run_manifest(options=options, runtime_config=runtime_config, run_id=run_id)
    prompt_pack_file_paths = resolve_prompt_pack_file_paths(stage=options.stage)

    _print_stage_run_start(
        options=options,
        run_id=run_id,
        is_resume_candidate=is_resume_candidate,
    )
    orchestration, stage_attempt_count = _run_stage_attempts(
        options=options,
        runtime_config=runtime_config,
        run_id=run_id,
        prompt_pack_file_paths=tuple(prompt_pack_file_paths),
    )
    _print_stage_run_result(
        orchestration=orchestration,
        stage_attempt_count=stage_attempt_count,
    )
    if orchestration.transition.action is not PostValidationAction.ADVANCE:
        raise typer.Exit(code=1)


__all__ = [
    "StageRunOptions",
    "run_stage_command",
]

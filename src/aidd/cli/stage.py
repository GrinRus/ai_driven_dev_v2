from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.table import Table

from aidd.adapters.runtime_execution import StageRuntimeRequest
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.cli.run_lookup import resolve_stage_result_summary
from aidd.cli.support import (
    _STAGE_RUN_SUPPORTED_RUNTIMES,
    _active_prompt_pack_paths,
    _allocate_stage_run_id,
    _path_summary,
    _prefix_stream_chunk,
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    _runtime_timeout_for_runtime,
    console,
)
from aidd.config import load_config
from aidd.core.interview import (
    load_answers_document,
    load_questions_document,
    resolved_question_ids,
    stage_has_unresolved_blocking_questions,
)
from aidd.core.repair import RepairBudgetPolicy, generate_repair_brief, write_repair_brief
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


def stage_run(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    runtime: Annotated[str, typer.Option("--runtime", help="Runtime id")] = "generic-cli",
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional run id; defaults to latest blocked or new run."),
    ] = None,
    root: Annotated[
        Path | None,
        typer.Option("--root", help="Root AIDD storage directory. Defaults to config value."),
    ] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to an AIDD TOML config file."),
    ] = Path("aidd.example.toml"),
    log_follow: Annotated[
        bool,
        typer.Option(
            "--log-follow/--no-log-follow",
            help="Enable explicit live-log follow mode during stage execution.",
        ),
    ] = False,
) -> None:
    """Run a single AIDD stage."""
    if not is_valid_stage(stage):
        raise typer.BadParameter(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}")
    if runtime not in _STAGE_RUN_SUPPORTED_RUNTIMES:
        supported = ", ".join(_STAGE_RUN_SUPPORTED_RUNTIMES)
        raise typer.BadParameter(
            f"Unsupported runtime '{runtime}'. Supported runtimes: {supported}."
        )

    cfg = load_config(config)
    workspace_root = (root if root is not None else cfg.workspace_root).resolve(strict=False)
    runtime_command = _runtime_command_for_runtime(runtime=runtime, cfg=cfg)
    runtime_execution_mode = _runtime_execution_mode_for_runtime(runtime=runtime, cfg=cfg)
    runtime_timeout_seconds = _runtime_timeout_for_runtime(
        runtime=runtime,
        cfg=cfg,
        stage=stage,
    )
    repair_policy = RepairBudgetPolicy(default_max_repair_attempts=cfg.max_repair_attempts)
    selected_run_id: str | None = None
    if run_id is not None:
        normalized_run_id = run_id.strip()
        if not normalized_run_id:
            raise typer.BadParameter("Option '--run-id' must not be empty.")
        selected_run_id = normalized_run_id
    else:
        latest_existing_run = latest_run_id(workspace_root=workspace_root, work_item=work_item)
        if latest_existing_run is not None:
            latest_stage_metadata = load_stage_metadata(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=latest_existing_run,
                stage=stage,
            )
            if (
                latest_stage_metadata is not None
                and latest_stage_metadata.status.lower() == StageState.BLOCKED.value
            ):
                selected_run_id = latest_existing_run

    is_resume_candidate = False
    if selected_run_id is not None:
        selected_stage_metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=selected_run_id,
            stage=stage,
        )
        is_resume_candidate = (
            selected_stage_metadata is not None
            and selected_stage_metadata.status.lower() == StageState.BLOCKED.value
        )

    run_id = selected_run_id or _allocate_stage_run_id(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id=runtime,
        stage_target=stage,
        config_snapshot={
            "config_path": config.as_posix(),
            "workspace_root": workspace_root.as_posix(),
            "runtime_command": runtime_command,
            "runtime_execution_mode": runtime_execution_mode.value,
            "runtime_timeout_seconds": runtime_timeout_seconds,
            "log_follow": log_follow,
        },
    )
    prompt_pack_file_paths = resolve_prompt_pack_file_paths(stage=stage)

    console.print(
        "AIDD stage run: "
        f"stage={stage} work_item={work_item} runtime={runtime} "
        f"log_follow={log_follow} run_id={run_id}"
    )
    if is_resume_candidate:
        console.print("Detected blocked stage metadata on the latest run; attempting resume.")
    if log_follow:
        console.print("Live-log follow mode enabled for runtime stream output.")

    def _stream_runtime_chunk(
        *,
        stream: Literal["stdout", "stderr"],
        chunk: str,
    ) -> None:
        if not log_follow:
            return
        prefixed_chunk = _prefix_stream_chunk(
            runtime=runtime,
            stage=stage,
            stream=stream,
            chunk=chunk,
            multi_stream=True,
        )
        console.print(prefixed_chunk, end="", markup=False, highlight=False)

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        stage_documents_root = workspace_stage_root(
            root=workspace_root,
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
            runtime_id=runtime,
            execution_mode=runtime_execution_mode,
            timeout_seconds=runtime_timeout_seconds,
            stage=invocation.stage,
            work_item=invocation.work_item,
            run_id=invocation.run_id,
            workspace_root=workspace_root,
            stage_brief_path=stage_brief_path,
            prompt_pack_paths=prompt_pack_paths_for_runtime,
            repository_root=Path.cwd().resolve(strict=False),
            attempt_number=invocation.attempt_number,
            repair_mode=invocation.repair_mode,
            input_bundle_path=invocation.input_bundle_path,
            repair_brief_path=invocation.repair_brief_path,
            repair_context_markdown=invocation.repair_context_markdown,
        )

        def _on_stdout(chunk: str) -> None:
            _stream_runtime_chunk(stream="stdout", chunk=chunk)

        def _on_stderr(chunk: str) -> None:
            _stream_runtime_chunk(stream="stderr", chunk=chunk)

        on_stdout = _on_stdout if log_follow else None
        on_stderr = _on_stderr if log_follow else None
        try:
            adapter_result = get_runtime_adapter_surface(runtime).execute_stage_request(
                configured_command=runtime_command,
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
            if runtime not in _STAGE_RUN_SUPPORTED_RUNTIMES:
                return AdapterExecutionOutcome(
                    succeeded=False,
                    details=f"unsupported-runtime: {runtime}",
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
    ) -> Path:
        if orchestration.validation_result is None:
            raise ValueError("Repair retry requires validator findings from the previous attempt.")

        validator_report_path = orchestration.validation_result.validator_report_path
        repair_brief_path = validator_report_path.parent / "repair-brief.md"
        repair_brief = generate_repair_brief(
            validator_report_path=validator_report_path,
            prior_stage_artifacts=orchestration.adapter_invocation.expected_input_bundle,
            stage_attempt_count=orchestration.execution_state.attempt_number,
            max_repair_attempts=repair_policy.default_max_repair_attempts,
            workspace_root=workspace_root,
        )
        write_repair_brief(path=repair_brief_path, repair_brief_markdown=repair_brief)
        return repair_brief_path

    orchestration: StageOrchestrationResult | None = None
    stage_attempt_count = 0
    while True:
        unblock_state = update_stage_unblock_state(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        if unblock_state.was_blocked and not unblock_state.unblocked:
            stage_documents_root = workspace_root / "workitems" / work_item / "stages" / stage
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
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                adapter_executor=_adapter_executor,
                repair_policy=repair_policy,
            )
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

        stage_attempt_count += 1
        if orchestration.transition.action is not PostValidationAction.REPAIR:
            break
        repair_brief_path = _write_repair_brief_for_retry(orchestration=orchestration)
        console.print(f"Repair brief prepared: {repair_brief_path.as_posix()}")
        console.print(
            "Repair retry scheduled: "
            f"attempt={orchestration.execution_state.attempt_number + 1}"
        )

    assert orchestration is not None

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
    if orchestration.transition.action is not PostValidationAction.ADVANCE:
        raise typer.Exit(code=1)


def stage_questions(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    """Show pending stage questions and answer guidance."""
    if not is_valid_stage(stage):
        raise typer.BadParameter(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}")

    questions = load_questions_document(
        workspace_root=root,
        work_item=work_item,
        stage=stage,
    )
    if not questions:
        console.print("No stage questions recorded.")
        return

    resolved_ids: set[str] = set()
    answers_path = root / "workitems" / work_item / "stages" / stage / "answers.md"
    if answers_path.exists():
        resolved_ids = set(
            resolved_question_ids(
                answers=load_answers_document(
                    workspace_root=root,
                    work_item=work_item,
                    stage=stage,
                )
            )
        )

    table = Table(title=f"Stage questions: {stage} / {work_item}")
    table.add_column("Question id")
    table.add_column("Policy")
    table.add_column("Status")
    table.add_column("Text")
    for question in questions:
        if question.question_id in resolved_ids:
            status = "resolved"
        elif question.policy.value == "blocking":
            status = "pending-blocking"
        else:
            status = "pending-non-blocking"
        table.add_row(question.question_id, question.policy.value, status, question.text)
    console.print(table)

    if stage_has_unresolved_blocking_questions(
        workspace_root=root,
        work_item=work_item,
        stage=stage,
    ):
        console.print(
            "Blocking questions are unresolved. Add `[resolved]` answers in "
            f"`{answers_path.as_posix()}` before progressing this stage."
        )
        return

    console.print("No unresolved blocking questions. Stage can proceed if other checks pass.")


def stage_summary(
    stage: Annotated[str, typer.Argument(help="Stage name")],
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Optional run id; defaults to the latest run."),
    ] = None,
) -> None:
    """Show a stage result summary for one work item run."""
    if not is_valid_stage(stage):
        raise typer.BadParameter(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}")

    try:
        summary = resolve_stage_result_summary(
            workspace_root=root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    table = Table(title=f"Stage summary: {stage} / {work_item}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("run id", summary.run_id)
    table.add_row("runtime", summary.runtime_id)
    table.add_row("final state", summary.final_state)
    table.add_row("attempt count", str(summary.attempt_count))
    table.add_row("validator pass count", str(summary.validator_pass_count))
    table.add_row("validator fail count", str(summary.validator_fail_count))
    table.add_row("validator report", summary.validator_report_path)
    table.add_row("log artifacts", _path_summary(summary.log_artifact_paths))
    table.add_row("document artifacts", _path_summary(summary.document_artifact_paths))
    table.add_row("repair outputs", _path_summary(summary.repair_output_paths))
    console.print(table)

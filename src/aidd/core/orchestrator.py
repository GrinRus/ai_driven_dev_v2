from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aidd.adapters.base import RuntimeStartRequest, RuntimeStream
from aidd.adapters.executor import (
    RuntimeExecutionContext,
    execute_runtime_stage,
    is_runtime_available,
    resolve_runtime_command,
)
from aidd.config import AiddConfig
from aidd.core.repair import (
    RepairBudgetPolicy,
    generate_repair_brief,
    persist_repair_history_snapshot,
    write_repair_brief,
)
from aidd.core.run_store import (
    create_run_manifest,
    persist_stage_status,
    write_attempt_artifact_index,
)
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT, resolve_prompt_pack_paths
from aidd.core.stage_runner import (
    PostValidationAction,
    ValidationVerdict,
    decide_post_validation_transition,
    discover_stage_markdown_outputs,
    persist_execution_state,
    persist_validation_state_with_repair_budget,
    prepare_adapter_invocation,
    prepare_stage_bundle,
    route_stage_questions_to_interview,
    run_structural_validation_after_output_discovery,
)
from aidd.core.stages import STAGES, is_valid_stage, stage_index
from aidd.core.state_machine import StageState
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.evals.grader_pipeline import build_stage_grader_payload, write_grader_payload
from aidd.validators.cross_document import validate_cross_document_consistency
from aidd.validators.reports import write_validator_report
from aidd.validators.semantic import validate_semantic_outputs

RuntimeStreamCallback = Callable[[RuntimeStream, str], None]


@dataclass(frozen=True, slots=True)
class StageAttemptOutcome:
    attempt_number: int
    requested_verdict: ValidationVerdict
    resolved_verdict: ValidationVerdict
    next_state: StageState
    action: PostValidationAction
    runtime_exit_classification: str
    runtime_log_path: Path
    normalized_events_path: Path | None
    finding_count: int
    unresolved_blocking_question_ids: tuple[str, ...]
    validator_report_path: Path
    grader_path: Path
    repair_brief_path: Path | None


@dataclass(frozen=True, slots=True)
class StageRunOutcome:
    run_id: str
    runtime_id: str
    work_item: str
    stage: str
    final_state: StageState
    final_action: PostValidationAction
    attempts: tuple[StageAttemptOutcome, ...]

    @property
    def succeeded(self) -> bool:
        return self.final_state is StageState.SUCCEEDED


@dataclass(frozen=True, slots=True)
class WorkflowRunOutcome:
    run_id: str
    runtime_id: str
    work_item: str
    stage_start: str
    stage_target: str
    stage_outcomes: tuple[StageRunOutcome, ...]
    final_state: StageState

    @property
    def succeeded(self) -> bool:
        return self.final_state is StageState.SUCCEEDED


@dataclass(frozen=True, slots=True)
class RunOrchestrator:
    workspace_root: Path
    config: AiddConfig
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT
    repository_root: Path | None = None
    timeout_seconds: float | None = None
    on_runtime_stream: RuntimeStreamCallback | None = None

    def run_stage(
        self,
        *,
        work_item: str,
        stage: str,
        runtime_id: str,
        run_id: str | None = None,
        stage_target: str | None = None,
    ) -> StageRunOutcome:
        return run_stage(
            workspace_root=self.workspace_root,
            config=self.config,
            work_item=work_item,
            stage=stage,
            runtime_id=runtime_id,
            run_id=run_id,
            stage_target=stage_target,
            contracts_root=self.contracts_root,
            repository_root=self.repository_root,
            timeout_seconds=self.timeout_seconds,
            on_runtime_stream=self.on_runtime_stream,
        )

    def run_workflow(
        self,
        *,
        work_item: str,
        runtime_id: str,
        stage_start: str = STAGES[0],
        stage_target: str = STAGES[-1],
    ) -> WorkflowRunOutcome:
        return run_workflow(
            workspace_root=self.workspace_root,
            config=self.config,
            work_item=work_item,
            runtime_id=runtime_id,
            stage_start=stage_start,
            stage_target=stage_target,
            contracts_root=self.contracts_root,
            repository_root=self.repository_root,
            timeout_seconds=self.timeout_seconds,
            on_runtime_stream=self.on_runtime_stream,
        )


def _generate_run_id(*, prefix: str = "run") -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{timestamp}-{uuid4().hex[:8]}"


def _workspace_relative_path(workspace_root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def _assert_valid_stage(stage: str, *, field_name: str) -> None:
    if is_valid_stage(stage):
        return
    raise ValueError(f"Unknown {field_name} '{stage}'. Expected one of: {', '.join(STAGES)}")


def _assert_workspace_ready(*, workspace_root: Path, work_item: str) -> None:
    work_item_root = workspace_root / "workitems" / work_item
    if work_item_root.exists():
        return
    raise ValueError(
        "Workspace for work item "
        f"'{work_item}' was not found at '{work_item_root.as_posix()}'. "
        "Run `aidd init --work-item ...` first."
    )


def _repair_policy_from_config(config: AiddConfig) -> RepairBudgetPolicy:
    return RepairBudgetPolicy(default_max_repair_attempts=config.max_repair_attempts)


def _is_runtime_success(exit_classification: str) -> bool:
    return exit_classification.strip().lower() == "success"


def _requested_validation_verdict(
    *,
    runtime_exit_classification: str,
    findings_count: int,
    unresolved_blocking_question_ids: tuple[str, ...],
) -> ValidationVerdict:
    if not _is_runtime_success(runtime_exit_classification):
        return ValidationVerdict.FAIL
    if unresolved_blocking_question_ids:
        return ValidationVerdict.BLOCKED
    if findings_count > 0:
        return ValidationVerdict.REPAIR
    return ValidationVerdict.PASS


def _config_snapshot(
    *,
    config: AiddConfig,
    runtime_id: str,
    runtime_command: str,
) -> dict[str, object]:
    return {
        "runtime_id": runtime_id,
        "runtime_command": runtime_command,
        "workspace_root": config.workspace_root.as_posix(),
        "log_mode": config.log_mode,
        "max_repair_attempts": config.max_repair_attempts,
    }


def run_stage(
    *,
    workspace_root: Path,
    config: AiddConfig,
    work_item: str,
    stage: str,
    runtime_id: str,
    run_id: str | None = None,
    stage_target: str | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    repository_root: Path | None = None,
    timeout_seconds: float | None = None,
    on_runtime_stream: RuntimeStreamCallback | None = None,
) -> StageRunOutcome:
    _assert_valid_stage(stage, field_name="stage")
    _assert_workspace_ready(workspace_root=workspace_root, work_item=work_item)

    runtime_command = resolve_runtime_command(runtime_id=runtime_id, config=config)
    if not is_runtime_available(runtime_id=runtime_id, command=runtime_command):
        raise ValueError(
            f"Runtime '{runtime_id}' is not available for command '{runtime_command}'."
        )

    resolved_run_id = run_id or _generate_run_id(prefix="run")
    resolved_stage_target = stage_target or stage
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=resolved_run_id,
        runtime_id=runtime_id,
        stage_target=resolved_stage_target,
        config_snapshot=_config_snapshot(
            config=config,
            runtime_id=runtime_id,
            runtime_command=runtime_command,
        ),
    )

    repair_policy = _repair_policy_from_config(config)
    attempt_outcomes: list[StageAttemptOutcome] = []

    while True:
        persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=resolved_run_id,
            stage=stage,
            status=StageState.PREPARING.value,
        )
        preparation_bundle = prepare_stage_bundle(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            contracts_root=contracts_root,
        )
        stage_documents_root = workspace_stage_root(
            root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        stage_brief_path = stage_documents_root / "stage-brief.md"
        stage_brief_path.parent.mkdir(parents=True, exist_ok=True)
        stage_brief_path.write_text(preparation_bundle.stage_brief_markdown, encoding="utf-8")

        execution_state = persist_execution_state(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=resolved_run_id,
            stage=stage,
        )
        invocation = prepare_adapter_invocation(
            workspace_root=workspace_root,
            preparation_bundle=preparation_bundle,
            execution_state=execution_state,
        )
        prompt_pack_paths = resolve_prompt_pack_paths(stage=stage, contracts_root=contracts_root)
        runtime_start_request = RuntimeStartRequest(
            stage=stage,
            work_item=work_item,
            run_id=resolved_run_id,
            workspace_root=workspace_root,
            attempt_path=execution_state.attempt_path,
            stage_brief_path=stage_brief_path,
            prompt_pack_paths=prompt_pack_paths,
            timeout_seconds=timeout_seconds,
            repository_root=repository_root,
        )
        runtime_result = execute_runtime_stage(
            RuntimeExecutionContext(
                runtime_id=runtime_id,
                configured_command=runtime_command,
                request=runtime_start_request,
                on_stream=on_runtime_stream,
            )
        )
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=resolved_run_id,
            stage=stage,
            attempt_number=execution_state.attempt_number,
        )

        output_discovery = discover_stage_markdown_outputs(
            execution_state=execution_state,
            invocation_bundle=invocation,
        )
        structural_validation = run_structural_validation_after_output_discovery(
            workspace_root=workspace_root,
            discovery=output_discovery,
            contracts_root=contracts_root,
        )
        semantic_findings = validate_semantic_outputs(
            stage=stage,
            work_item=work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
        cross_findings = validate_cross_document_consistency(
            stage=stage,
            work_item=work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
        all_findings = tuple((*structural_validation.findings, *semantic_findings, *cross_findings))
        write_validator_report(
            path=structural_validation.validator_report_path,
            findings=all_findings,
        )

        unresolved_blocking_question_ids = runtime_result.unresolved_blocking_question_ids
        if not unresolved_blocking_question_ids:
            interview_routing = route_stage_questions_to_interview(
                workspace_root=workspace_root,
                discovery=output_discovery,
            )
            unresolved_blocking_question_ids = interview_routing.unresolved_blocking_question_ids

        persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=resolved_run_id,
            stage=stage,
            status=StageState.VALIDATING.value,
        )
        requested_verdict = _requested_validation_verdict(
            runtime_exit_classification=runtime_result.exit_classification,
            findings_count=len(all_findings),
            unresolved_blocking_question_ids=unresolved_blocking_question_ids,
        )
        budget_transition = persist_validation_state_with_repair_budget(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=resolved_run_id,
            stage=stage,
            verdict=requested_verdict,
            repair_policy=repair_policy,
        )
        post_validation = decide_post_validation_transition(
            budget_transition.validation_state,
            workspace_root=workspace_root,
        )

        repair_brief_path: Path | None = None
        if requested_verdict is ValidationVerdict.REPAIR:
            repair_brief_path = stage_documents_root / "repair-brief.md"
            repair_brief_markdown = generate_repair_brief(
                validator_report_path=structural_validation.validator_report_path,
                prior_stage_artifacts=(runtime_result.runtime_log_path,),
                stage_attempt_count=execution_state.attempt_number,
                max_repair_attempts=repair_policy.default_max_repair_attempts,
                workspace_root=workspace_root,
            )
            write_repair_brief(path=repair_brief_path, repair_brief_markdown=repair_brief_markdown)

        persist_repair_history_snapshot(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=resolved_run_id,
            stage=stage,
            attempt_number=execution_state.attempt_number,
            trigger="initial" if execution_state.attempt_number == 1 else "repair",
            outcome=post_validation.next_state.value,
            stage_status=post_validation.next_state.value,
            validator_report_path=structural_validation.validator_report_path,
            repair_brief_path=repair_brief_path,
        )
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=resolved_run_id,
            stage=stage,
            attempt_number=execution_state.attempt_number,
        )
        grader_path = execution_state.attempt_path / "grader.json"
        write_grader_payload(
            path=grader_path,
            payload=build_stage_grader_payload(
                run_id=resolved_run_id,
                work_item=work_item,
                runtime_id=runtime_id,
                stage=stage,
                attempt_number=execution_state.attempt_number,
                runtime_exit_classification=runtime_result.exit_classification,
                validator_finding_count=len(all_findings),
                unresolved_blocking_question_ids=unresolved_blocking_question_ids,
                resolved_verdict=budget_transition.resolved_verdict.value,
                next_state=post_validation.next_state.value,
                action=post_validation.action.value,
            ),
        )
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=resolved_run_id,
            stage=stage,
            attempt_number=execution_state.attempt_number,
        )

        attempt_outcomes.append(
            StageAttemptOutcome(
                attempt_number=execution_state.attempt_number,
                requested_verdict=requested_verdict,
                resolved_verdict=budget_transition.resolved_verdict,
                next_state=post_validation.next_state,
                action=post_validation.action,
                runtime_exit_classification=runtime_result.exit_classification,
                runtime_log_path=runtime_result.runtime_log_path,
                normalized_events_path=runtime_result.normalized_events_path,
                finding_count=len(all_findings),
                unresolved_blocking_question_ids=unresolved_blocking_question_ids,
                validator_report_path=structural_validation.validator_report_path,
                grader_path=grader_path,
                repair_brief_path=repair_brief_path,
            )
        )

        if post_validation.action is PostValidationAction.REPAIR:
            continue

        return StageRunOutcome(
            run_id=resolved_run_id,
            runtime_id=runtime_id,
            work_item=work_item,
            stage=stage,
            final_state=post_validation.next_state,
            final_action=post_validation.action,
            attempts=tuple(attempt_outcomes),
        )


def run_workflow(
    *,
    workspace_root: Path,
    config: AiddConfig,
    work_item: str,
    runtime_id: str,
    stage_start: str = STAGES[0],
    stage_target: str = STAGES[-1],
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    repository_root: Path | None = None,
    timeout_seconds: float | None = None,
    on_runtime_stream: RuntimeStreamCallback | None = None,
) -> WorkflowRunOutcome:
    _assert_valid_stage(stage_start, field_name="stage_start")
    _assert_valid_stage(stage_target, field_name="stage_target")
    start_index = stage_index(stage_start)
    target_index = stage_index(stage_target)
    if start_index > target_index:
        raise ValueError(
            f"stage_start '{stage_start}' must not be after stage_target '{stage_target}'."
        )

    resolved_run_id = _generate_run_id(prefix="run")
    stage_outcomes: list[StageRunOutcome] = []
    final_state = StageState.SUCCEEDED
    for stage in STAGES[start_index : target_index + 1]:
        outcome = run_stage(
            workspace_root=workspace_root,
            config=config,
            work_item=work_item,
            stage=stage,
            runtime_id=runtime_id,
            run_id=resolved_run_id,
            stage_target=stage_target,
            contracts_root=contracts_root,
            repository_root=repository_root,
            timeout_seconds=timeout_seconds,
            on_runtime_stream=on_runtime_stream,
        )
        stage_outcomes.append(outcome)
        final_state = outcome.final_state
        if not outcome.succeeded:
            break

    return WorkflowRunOutcome(
        run_id=resolved_run_id,
        runtime_id=runtime_id,
        work_item=work_item,
        stage_start=stage_start,
        stage_target=stage_target,
        stage_outcomes=tuple(stage_outcomes),
        final_state=final_state,
    )

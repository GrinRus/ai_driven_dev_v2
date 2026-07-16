from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from aidd.core.contracts import repo_root_from
from aidd.core.workspace import WorkspaceBootstrapService
from aidd.evals.verdicts import VerdictStatus
from aidd.harness.eval_models import (
    EvalClassification,
    EvalExecutionState,
    EvalReportPersistenceContext,
    EvalScenarioRunResult,
)
from aidd.harness.eval_preparation import prepare_eval_run
from aidd.harness.eval_reports import persist_eval_reports
from aidd.harness.process_lifecycle import HarnessLifecycleBudget
from aidd.harness.repo_prep import prepare_scenario_repository, prepare_working_copy
from aidd.harness.runner import (
    HarnessAiddRunResult,
    invoke_aidd_run,
    invoke_aidd_stage,
    run_setup_steps,
    run_teardown_steps,
    run_verification_steps,
)
from aidd.harness.scenarios import Scenario, load_scenario

DETERMINISTIC_RUNTIME_ID = "generic-cli"
_STAGE_ORDER = (
    "idea",
    "research",
    "plan",
    "review-spec",
    "tasklist",
    "implement",
    "review",
    "qa",
)


@dataclass(frozen=True, slots=True)
class DeterministicEvalRequest:
    scenario_path: Path
    workspace_root: Path


class DeterministicEvalInputError(ValueError):
    """Raised when a scenario is not eligible for local deterministic execution."""


def _local_fixture_path(*, scenario_path: Path, scenario: Scenario) -> Path:
    try:
        repository_root = repo_root_from(scenario_path.resolve(strict=False))
    except FileNotFoundError as exc:
        raise DeterministicEvalInputError(
            "Deterministic eval execution requires a scenario inside an AIDD source tree."
        ) from exc
    candidate = Path(scenario.repo.url).expanduser()
    if not candidate.is_absolute():
        candidate = repository_root / candidate
    resolved = candidate.resolve(strict=False)
    if not resolved.is_dir():
        raise DeterministicEvalInputError(
            "Deterministic eval execution requires a local fixture repository."
        )
    return resolved


def validate_deterministic_scenario(
    *,
    scenario_path: Path,
    scenario: Scenario,
) -> None:
    if scenario.is_live:
        raise DeterministicEvalInputError(
            "Live scenarios are not supported by `aidd eval execute`."
        )
    if DETERMINISTIC_RUNTIME_ID not in scenario.runtime_targets:
        raise DeterministicEvalInputError(
            "Deterministic scenarios must allow the `generic-cli` runtime."
        )
    if scenario.feature_source is None or scenario.feature_source.mode != "fixture-seed":
        raise DeterministicEvalInputError(
            "Deterministic scenarios must use `feature_source.mode: fixture-seed`."
        )
    _local_fixture_path(scenario_path=scenario_path, scenario=scenario)


def _bootstrap_work_item(
    *,
    working_copy: Path,
    work_item: str,
    request_text: str,
) -> None:
    workspace_root = working_copy / ".aidd"
    user_request_path = workspace_root / "workitems" / work_item / "context/user-request.md"
    if user_request_path.exists():
        return
    bootstrap = WorkspaceBootstrapService(root=workspace_root)
    bootstrap.bootstrap_work_item(work_item=work_item)
    bootstrap.seed_request_context(
        work_item=work_item,
        request_text=request_text,
        project_root=working_copy,
    )


def _config_path(working_copy: Path) -> Path:
    path = working_copy / "aidd.example.toml"
    if not path.is_file():
        raise RuntimeError(
            "Deterministic scenario setup must create `aidd.example.toml`."
        )
    return path


def _execute(
    *,
    scenario: Scenario,
    working_copy: Path,
    work_item: str,
    aidd_command: tuple[str, ...],
    lifecycle_budget: HarnessLifecycleBudget,
) -> HarnessAiddRunResult:
    config_path = _config_path(working_copy)
    if scenario.scenario_class == "deterministic-stage":
        stage = scenario.run.stage_start
        if stage is None:
            raise RuntimeError("Deterministic stage scenario is missing its stage.")
        stage_index = _STAGE_ORDER.index(stage)
        if stage_index:
            prerequisite = invoke_aidd_run(
                scenario=scenario,
                working_copy_path=working_copy,
                runtime_id=DETERMINISTIC_RUNTIME_ID,
                work_item=work_item,
                aidd_command=aidd_command,
                stage_start="idea",
                stage_end=_STAGE_ORDER[stage_index - 1],
                config_path=config_path,
                lifecycle_budget=lifecycle_budget,
            )
            if prerequisite.exit_code != 0:
                return prerequisite
        return invoke_aidd_stage(
            scenario=scenario,
            working_copy_path=working_copy,
            runtime_id=DETERMINISTIC_RUNTIME_ID,
            work_item=work_item,
            stage=stage,
            aidd_command=aidd_command,
            config_path=config_path,
            lifecycle_budget=lifecycle_budget,
        )
    return invoke_aidd_run(
        scenario=scenario,
        working_copy_path=working_copy,
        runtime_id=DETERMINISTIC_RUNTIME_ID,
        work_item=work_item,
        aidd_command=aidd_command,
        stage_start=scenario.run.stage_start,
        stage_end=scenario.run.stage_end,
        config_path=config_path,
        lifecycle_budget=lifecycle_budget,
    )


def _classification(state: EvalExecutionState) -> EvalClassification:
    infrastructure_error = next(
        (
            error
            for error in (
                state.prep_error,
                state.setup_error,
                state.run_error,
                state.teardown_error,
            )
            if error is not None
        ),
        None,
    )
    if infrastructure_error is not None:
        return EvalClassification(
            status="infra-fail",
            summary=f"Deterministic eval infrastructure failed: {infrastructure_error}",
            blocked_by_questions=False,
            infrastructure_failure=True,
            verification_failed=state.verification_error is not None,
        )
    if state.verification_error is not None:
        return EvalClassification(
            status="fail",
            summary=f"Scenario verification failed: {state.verification_error}",
            blocked_by_questions=False,
            infrastructure_failure=False,
            verification_failed=True,
        )
    if state.aidd_run_result is None or state.aidd_run_result.exit_code != 0:
        exit_code = (
            "missing"
            if state.aidd_run_result is None
            else str(state.aidd_run_result.exit_code)
        )
        return EvalClassification(
            status="fail",
            summary=f"AIDD execution failed with exit code {exit_code}.",
            blocked_by_questions=False,
            infrastructure_failure=False,
            verification_failed=False,
        )
    return EvalClassification(
        status="pass",
        summary="Deterministic scenario completed and verification passed.",
        blocked_by_questions=False,
        infrastructure_failure=False,
        verification_failed=False,
    )


def execute_deterministic_eval(
    request: DeterministicEvalRequest,
) -> EvalScenarioRunResult:
    scenario_path = request.scenario_path.resolve(strict=False)
    scenario = load_scenario(
        scenario_path,
        runtime_id=DETERMINISTIC_RUNTIME_ID,
        workspace_root=request.workspace_root,
    )
    validate_deterministic_scenario(
        scenario_path=scenario_path,
        scenario=scenario,
    )
    prep = prepare_eval_run(
        scenario_path=scenario_path,
        runtime_id=DETERMINISTIC_RUNTIME_ID,
        workspace_root=request.workspace_root,
    )
    state = EvalExecutionState()
    started = monotonic()
    lifecycle_budget = HarnessLifecycleBudget.start(
        None
        if prep.scenario.run.timeout_minutes is None
        else float(prep.scenario.run.timeout_minutes * 60),
        now=started,
    )
    try:
        state.prepared_repository = prepare_scenario_repository(
            cache_root=prep.cache_root,
            scenario=prep.scenario,
        )
        state.prepared_working_copy = prepare_working_copy(
            cache_root=prep.cache_root,
            scenario=prep.scenario,
            prepared_repository=state.prepared_repository,
            run_id=prep.run_id,
        )
    except BaseException as exc:
        state.prep_error = exc

    working_copy = (
        None
        if state.prepared_working_copy is None
        else state.prepared_working_copy.working_copy_path
    )
    if working_copy is not None:
        try:
            state.setup_result = run_setup_steps(
                scenario=prep.scenario,
                working_copy_path=working_copy,
                lifecycle_budget=lifecycle_budget,
            )
            _bootstrap_work_item(
                working_copy=working_copy,
                work_item=prep.work_item,
                request_text=prep.scenario.task,
            )
        except BaseException as exc:
            state.setup_error = exc

        if state.setup_error is None:
            try:
                if prep.aidd_command is None:
                    raise RuntimeError("Deterministic execution command is unavailable.")
                state.aidd_run_result = _execute(
                    scenario=prep.scenario,
                    working_copy=working_copy,
                    work_item=prep.work_item,
                    aidd_command=prep.aidd_command,
                    lifecycle_budget=lifecycle_budget,
                )
            except BaseException as exc:
                state.run_error = exc

        if state.aidd_run_result is not None:
            try:
                state.verification_result = run_verification_steps(
                    scenario=prep.scenario,
                    working_copy_path=working_copy,
                    aidd_run_result=state.aidd_run_result,
                    lifecycle_budget=lifecycle_budget,
                )
            except BaseException as exc:
                state.verification_error = exc

        try:
            state.teardown_result = run_teardown_steps(
                teardown_commands=prep.teardown_commands,
                working_copy_path=working_copy,
                lifecycle_budget=lifecycle_budget,
            )
        except BaseException as exc:
            state.teardown_error = exc

    return persist_eval_reports(
        EvalReportPersistenceContext(
            prep=prep,
            state=state,
            classification=_classification(state),
            started=started,
        )
    )


def successful_status(status: VerdictStatus) -> bool:
    return status == "pass"


__all__ = [
    "DETERMINISTIC_RUNTIME_ID",
    "DeterministicEvalInputError",
    "DeterministicEvalRequest",
    "execute_deterministic_eval",
    "successful_status",
    "validate_deterministic_scenario",
]

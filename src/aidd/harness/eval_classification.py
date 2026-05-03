from __future__ import annotations

from pathlib import Path

from aidd.core.stages import STAGES
from aidd.core.workspace import stage_output_root as workspace_stage_output_root
from aidd.evals.verdicts import VerdictStatus
from aidd.harness.eval_models import (
    EvalClassification,
    EvalExecutionState,
    EvalRunPreparation,
)
from aidd.harness.runner import HarnessAiddRunResult
from aidd.harness.scenarios import Scenario

PASS_GUARD_REQUIRED_OUTPUT_FILES: tuple[str, ...] = (
    "stage-result.md",
    "validator-report.md",
)


def is_missing_answers_failure(error: BaseException | None) -> bool:
    if error is None:
        return False
    text = str(error).lower()
    return "answers.md" in text and ("test -f" in text or "no such file" in text)


def combined_run_output(aidd_run_result: HarnessAiddRunResult | None) -> str:
    if aidd_run_result is None:
        return ""
    return f"{aidd_run_result.stdout_text}\n{aidd_run_result.stderr_text}".lower()


def has_unsupported_runtime_signal(
    aidd_run_result: HarnessAiddRunResult | None,
) -> bool:
    output = combined_run_output(aidd_run_result)
    if not output:
        return False
    return (
        "failure classification: unsupported-runtime" in output
        or "implemented for runtime 'generic-cli' only" in output
    )


def has_noop_execution_signal(aidd_run_result: HarnessAiddRunResult | None) -> bool:
    output = combined_run_output(aidd_run_result)
    if not output:
        return False
    return "workflow run completed: no runnable stages found." in output


def resolve_stage_scope_for_pass_guard(scenario: Scenario) -> tuple[str, ...]:
    start = scenario.run.stage_start or STAGES[0]
    end = scenario.run.stage_end or STAGES[-1]
    if start not in STAGES or end not in STAGES:
        return STAGES

    start_index = STAGES.index(start)
    end_index = STAGES.index(end)
    if start_index > end_index:
        return STAGES
    return STAGES[start_index : end_index + 1]


def missing_required_pass_artifacts(
    *,
    scenario: Scenario,
    workspace_root: Path,
    work_item: str,
) -> tuple[Path, ...]:
    missing: list[Path] = []
    for stage in resolve_stage_scope_for_pass_guard(scenario):
        output_root = workspace_stage_output_root(
            root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        for filename in PASS_GUARD_REQUIRED_OUTPUT_FILES:
            candidate = output_root / filename
            if not candidate.exists():
                missing.append(candidate)
    return tuple(missing)


def classify_status(
    *,
    scenario: Scenario,
    prep_error: BaseException | None,
    install_error: BaseException | None,
    setup_error: BaseException | None,
    run_error: BaseException | None,
    verification_error: BaseException | None,
    teardown_error: BaseException | None,
    aidd_run_result: HarnessAiddRunResult | None,
) -> tuple[VerdictStatus, str, bool, bool, bool]:
    infrastructure_failure = any(
        error is not None for error in (prep_error, setup_error, teardown_error)
    )
    if infrastructure_failure:
        return (
            "infra-fail",
            "Harness infrastructure failure during repository/setup/teardown lifecycle.",
            False,
            True,
            verification_error is not None,
        )

    if install_error is not None:
        return (
            "fail",
            f"AIDD install preparation failed before scenario execution: {install_error}",
            False,
            False,
            False,
        )

    blocked_by_questions = scenario.run.interview_required and is_missing_answers_failure(
        verification_error
    )
    if blocked_by_questions:
        return (
            "blocked",
            "Interview scenario blocked waiting for required answers.md evidence.",
            True,
            False,
            True,
        )

    if has_unsupported_runtime_signal(aidd_run_result):
        return (
            "fail",
            "AIDD run reported unsupported-runtime classification; execution path is non-pass.",
            False,
            False,
            True,
        )

    if has_noop_execution_signal(aidd_run_result):
        return (
            "fail",
            "AIDD run completed with no runnable stages; no-op execution is non-pass.",
            False,
            False,
            True,
        )

    if aidd_run_result is not None and aidd_run_result.timed_out:
        timeout = (
            f"{aidd_run_result.timeout_seconds:.3f}s"
            if aidd_run_result.timeout_seconds is not None
            else "the configured timeout"
        )
        return (
            "fail",
            f"Installed AIDD run timed out after {timeout}.",
            False,
            False,
            False,
        )

    if verification_error is not None:
        return (
            "fail",
            "Scenario verification step returned non-zero status.",
            False,
            False,
            True,
        )

    if run_error is not None:
        return (
            "fail",
            f"AIDD run failed before verification: {run_error}",
            False,
            False,
            False,
        )

    if aidd_run_result is not None and aidd_run_result.exit_code != 0:
        return (
            "fail",
            f"AIDD run exited with non-zero status {aidd_run_result.exit_code}.",
            False,
            False,
            False,
        )

    return (
        "pass",
        "Setup, run, verification, and teardown completed successfully.",
        False,
        False,
        False,
    )


def classify_eval_execution(
    *,
    prep: EvalRunPreparation,
    state: EvalExecutionState,
) -> EvalClassification:
    status, summary, blocked_by_questions, infrastructure_failure, verification_failed = (
        classify_status(
            scenario=prep.scenario,
            prep_error=state.prep_error,
            install_error=state.install_error,
            setup_error=state.setup_error,
            run_error=state.run_error,
            verification_error=state.verification_error,
            teardown_error=state.teardown_error,
            aidd_run_result=state.aidd_run_result,
        )
    )

    if status == "pass" and state.prepared_working_copy is not None:
        missing_pass_artifacts = missing_required_pass_artifacts(
            scenario=prep.scenario,
            workspace_root=state.prepared_working_copy.working_copy_path / ".aidd",
            work_item=prep.work_item,
        )
        if missing_pass_artifacts:
            missing_preview = ", ".join(
                path.as_posix() for path in missing_pass_artifacts[:4]
            )
            extra_count = len(missing_pass_artifacts) - 4
            suffix = f" (+{extra_count} more)" if extra_count > 0 else ""
            status = "fail"
            summary = (
                "Required stage output artifacts are missing; pass verdict is disallowed. "
                f"Missing: {missing_preview}{suffix}"
            )
            verification_failed = True

    return EvalClassification(
        status=status,
        summary=summary,
        blocked_by_questions=blocked_by_questions,
        infrastructure_failure=infrastructure_failure,
        verification_failed=verification_failed,
    )


__all__ = [
    "PASS_GUARD_REQUIRED_OUTPUT_FILES",
    "classify_eval_execution",
    "classify_status",
    "combined_run_output",
    "has_noop_execution_signal",
    "has_unsupported_runtime_signal",
    "is_missing_answers_failure",
    "missing_required_pass_artifacts",
    "resolve_stage_scope_for_pass_guard",
]

from __future__ import annotations

from aidd.harness.eval_models import EvalExecutionState, EvalRunPreparation
from aidd.harness.install_artifact import (
    HarnessInstallError,
    prepare_local_wheel_install,
    prepare_published_package_install,
)
from aidd.harness.live_runtime_config import (
    validate_live_runtime_command,
    write_live_runtime_config,
)
from aidd.harness.live_workspace_bootstrap import bootstrap_live_work_item
from aidd.harness.repo_prep import prepare_scenario_repository, prepare_working_copy
from aidd.harness.result_bundle import write_issue_selection
from aidd.harness.runner import (
    HarnessAiddRunResult,
    HarnessCommandTranscript,
    HarnessQualityError,
    HarnessQualityResult,
    HarnessSetupError,
    HarnessSetupResult,
    HarnessTeardownError,
    HarnessTeardownResult,
    HarnessVerificationError,
    HarnessVerificationResult,
    invoke_aidd_run,
    run_quality_steps,
    run_setup_steps,
    run_teardown_steps,
    run_verification_steps,
)


def command_transcripts_from_error(
    error: BaseException,
) -> tuple[HarnessCommandTranscript, ...]:
    raw_transcripts = getattr(error, "command_transcripts", ())
    if not isinstance(raw_transcripts, tuple):
        return tuple()
    return tuple(
        transcript
        for transcript in raw_transcripts
        if isinstance(transcript, HarnessCommandTranscript)
    )


def transcript_duration(
    transcripts: tuple[HarnessCommandTranscript, ...],
) -> float:
    return sum(transcript.duration_seconds for transcript in transcripts)


def partial_setup_result(error: BaseException) -> HarnessSetupResult | None:
    transcripts = command_transcripts_from_error(error)
    if not transcripts:
        return None
    return HarnessSetupResult(
        executed_commands=tuple(transcript.command for transcript in transcripts),
        command_transcripts=transcripts,
        duration_seconds=transcript_duration(transcripts),
    )


def partial_verification_result(
    *,
    error: BaseException,
    aidd_run_result: HarnessAiddRunResult | None,
) -> HarnessVerificationResult | None:
    transcripts = command_transcripts_from_error(error)
    if not transcripts:
        return None
    return HarnessVerificationResult(
        executed_commands=tuple(transcript.command for transcript in transcripts),
        aidd_exit_code=-1 if aidd_run_result is None else aidd_run_result.exit_code,
        command_transcripts=transcripts,
        duration_seconds=transcript_duration(transcripts),
    )


def partial_quality_result(error: BaseException) -> HarnessQualityResult | None:
    transcripts = command_transcripts_from_error(error)
    if not transcripts:
        return None
    return HarnessQualityResult(
        executed_commands=tuple(transcript.command for transcript in transcripts),
        command_transcripts=transcripts,
        duration_seconds=transcript_duration(transcripts),
    )


def partial_teardown_result(error: BaseException) -> HarnessTeardownResult | None:
    transcripts = command_transcripts_from_error(error)
    if not transcripts:
        return None
    return HarnessTeardownResult(
        executed_commands=tuple(transcript.command for transcript in transcripts),
        command_transcripts=transcripts,
        duration_seconds=transcript_duration(transcripts),
    )


def execute_eval_scenario(prep: EvalRunPreparation) -> EvalExecutionState:
    state = EvalExecutionState()
    write_issue_selection(layout=prep.layout, payload=prep.issue_selection_payload)
    aidd_command = prep.aidd_command

    if prep.live_scenario:
        try:
            validate_live_runtime_command(
                runtime_id=prep.runtime_id,
                scenario=prep.scenario,
                source_repository_root=prep.source_repository_root,
            )
        except RuntimeError as exc:
            state.run_error = exc

    if state.run_error is not None:
        return state

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
        return state

    assert state.prepared_working_copy is not None
    try:
        if prep.live_scenario:
            if prep.selected_issue is None:
                raise RuntimeError(
                    "Live scenario is missing a selected issue even though "
                    "the manifest loaded."
                )
            bootstrap_live_work_item(
                working_copy_path=state.prepared_working_copy.working_copy_path,
                scenario=prep.scenario,
                work_item=prep.work_item,
                selected_issue=prep.selected_issue,
                resolved_revision=state.prepared_working_copy.resolved_revision,
            )
            state.live_runtime_config_path = write_live_runtime_config(
                working_copy_path=state.prepared_working_copy.working_copy_path,
                runtime_id=prep.runtime_id,
                scenario=prep.scenario,
                source_repository_root=prep.source_repository_root,
            )
            if prep.published_package_spec is not None:
                state.install_result = prepare_published_package_install(
                    workspace_root=prep.workspace_root,
                    run_id=prep.run_id,
                    package_spec=prep.published_package_spec,
                )
            else:
                state.install_result = prepare_local_wheel_install(
                    workspace_root=prep.workspace_root,
                    run_id=prep.run_id,
                    repository_root=prep.source_repository_root,
                )
            aidd_command = state.install_result.installed_command

        if aidd_command is None:
            raise RuntimeError("Failed to derive an AIDD command for harness execution.")

        state.setup_result = run_setup_steps(
            scenario=prep.scenario,
            working_copy_path=state.prepared_working_copy.working_copy_path,
        )
        state.aidd_run_result = invoke_aidd_run(
            scenario=prep.scenario,
            working_copy_path=state.prepared_working_copy.working_copy_path,
            runtime_id=prep.runtime_id,
            work_item=prep.work_item,
            aidd_command=aidd_command,
            stage_start=prep.scenario.run.stage_start,
            stage_end=prep.scenario.run.stage_end,
            config_path=state.live_runtime_config_path,
        )
        state.verification_result = run_verification_steps(
            scenario=prep.scenario,
            working_copy_path=state.prepared_working_copy.working_copy_path,
            aidd_run_result=state.aidd_run_result,
        )
        state.quality_result = run_quality_steps(
            scenario=prep.scenario,
            working_copy_path=state.prepared_working_copy.working_copy_path,
        )
    except HarnessInstallError as exc:
        state.install_error = exc
    except HarnessSetupError as exc:
        state.setup_error = exc
        state.setup_result = partial_setup_result(exc)
    except HarnessVerificationError as exc:
        state.verification_error = exc
        state.verification_result = partial_verification_result(
            error=exc,
            aidd_run_result=state.aidd_run_result,
        )
    except HarnessQualityError as exc:
        state.quality_error = exc
        state.quality_result = partial_quality_result(exc)
    except RuntimeError as exc:
        state.run_error = exc
    finally:
        try:
            state.teardown_result = run_teardown_steps(
                teardown_commands=prep.teardown_commands,
                working_copy_path=state.prepared_working_copy.working_copy_path,
            )
        except HarnessTeardownError as exc:
            state.teardown_error = exc
            state.teardown_result = partial_teardown_result(exc)

    return state

from __future__ import annotations

from pathlib import Path
from time import monotonic

import aidd.harness.eval_execution as _eval_execution
import aidd.harness.eval_preparation as _eval_preparation
import aidd.harness.eval_reports as _eval_reports
from aidd.core.resources import resolve_resource_layout
from aidd.evals.log_analysis import (
    parse_runtime_log_text,
    parse_validator_report_failures_text,
    select_first_failure_boundary,
)
from aidd.evals.quality import (
    build_live_quality_assessment,
    write_live_quality_report_markdown,
)
from aidd.evals.reporting import build_scenario_summary_row, write_eval_summary_markdown
from aidd.evals.stage_timing import (
    build_stage_timing_payload,
    render_repair_history_markdown,
    render_stage_timing_markdown,
    write_stage_timing_artifacts,
)
from aidd.evals.verdicts import (
    build_scenario_verdict_from_harness_outcome,
    write_scenario_verdict_markdown,
)
from aidd.harness.eval_classification import (
    PASS_GUARD_REQUIRED_OUTPUT_FILES,
    classify_eval_execution,
    classify_status,
    combined_run_output,
    has_noop_execution_signal,
    has_unsupported_runtime_signal,
    is_missing_answers_failure,
    missing_required_pass_artifacts,
    resolve_stage_scope_for_pass_guard,
)
from aidd.harness.eval_execution import (
    command_transcripts_from_error,
    execute_eval_scenario,
    partial_quality_result,
    partial_setup_result,
    partial_teardown_result,
    partial_verification_result,
    transcript_duration,
)
from aidd.harness.eval_models import (
    EvalClassification,
    EvalExecutionState,
    EvalReportPersistenceContext,
    EvalRunPreparation,
    EvalRuntimeLogSourceContext,
    EvalScenarioRunResult,
)
from aidd.harness.eval_preparation import (
    build_feature_selection_payload,
    derive_aidd_command,
    derive_run_id,
    derive_teardown_commands,
    derive_work_item,
    prepare_eval_run,
    select_authored_task,
)
from aidd.harness.eval_reports import (
    EXIT_CODE_PATTERN,
    extract_exit_code,
    grader_payload,
    persist_eval_reports,
    render_log_analysis_markdown,
    render_runtime_log_source,
    render_validator_report_source,
    stage_failure_events_from_timing_payload,
    workspace_root_for_quality,
    write_source_artifacts,
)
from aidd.harness.eval_runner_compat import patch_module_values
from aidd.harness.install_artifact import (
    prepare_local_wheel_install,
    prepare_published_package_install,
)
from aidd.harness.live_runtime_config import (
    validate_live_runtime_command,
    write_live_runtime_config,
)
from aidd.harness.live_workspace_bootstrap import bootstrap_live_work_item
from aidd.harness.repo_prep import (
    prepare_scenario_repository,
    prepare_working_copy,
    prepare_workspace,
)
from aidd.harness.result_bundle import (
    copy_or_link_run_artifacts,
    ensure_result_bundle_layout,
    write_command_transcripts,
    write_feature_selection,
    write_harness_metadata,
)
from aidd.harness.runner import (
    invoke_aidd_run,
    run_quality_steps,
    run_setup_steps,
    run_teardown_steps,
    run_verification_steps,
)
from aidd.harness.scenarios import load_scenario


def _sync_legacy_patch_points() -> None:
    patch_module_values(
        _eval_preparation,
        (
            ("ensure_result_bundle_layout", ensure_result_bundle_layout),
            ("load_scenario", load_scenario),
            ("prepare_workspace", prepare_workspace),
            ("resolve_resource_layout", resolve_resource_layout),
        ),
    )
    patch_module_values(
        _eval_execution,
        (
            ("bootstrap_live_work_item", bootstrap_live_work_item),
            ("invoke_aidd_run", invoke_aidd_run),
            ("prepare_local_wheel_install", prepare_local_wheel_install),
            ("prepare_published_package_install", prepare_published_package_install),
            ("prepare_scenario_repository", prepare_scenario_repository),
            ("prepare_working_copy", prepare_working_copy),
            ("run_quality_steps", run_quality_steps),
            ("run_setup_steps", run_setup_steps),
            ("run_teardown_steps", run_teardown_steps),
            ("run_verification_steps", run_verification_steps),
            ("validate_live_runtime_command", validate_live_runtime_command),
            ("write_feature_selection", write_feature_selection),
            ("write_live_runtime_config", write_live_runtime_config),
        ),
    )
    patch_module_values(
        _eval_reports,
        (
            ("build_live_quality_assessment", build_live_quality_assessment),
            ("build_scenario_summary_row", build_scenario_summary_row),
            (
                "build_scenario_verdict_from_harness_outcome",
                build_scenario_verdict_from_harness_outcome,
            ),
            ("build_stage_timing_payload", build_stage_timing_payload),
            ("copy_or_link_run_artifacts", copy_or_link_run_artifacts),
            ("parse_runtime_log_text", parse_runtime_log_text),
            (
                "parse_validator_report_failures_text",
                parse_validator_report_failures_text,
            ),
            ("render_repair_history_markdown", render_repair_history_markdown),
            ("render_stage_timing_markdown", render_stage_timing_markdown),
            ("select_first_failure_boundary", select_first_failure_boundary),
            ("write_command_transcripts", write_command_transcripts),
            ("write_eval_summary_markdown", write_eval_summary_markdown),
            ("write_harness_metadata", write_harness_metadata),
            ("write_live_quality_report_markdown", write_live_quality_report_markdown),
            ("write_scenario_verdict_markdown", write_scenario_verdict_markdown),
            ("write_stage_timing_artifacts", write_stage_timing_artifacts),
        ),
    )


def run_eval_scenario(
    *,
    scenario_path: Path,
    runtime_id: str,
    workspace_root: Path = Path(".aidd"),
) -> EvalScenarioRunResult:
    started = monotonic()
    _sync_legacy_patch_points()
    prep = prepare_eval_run(
        scenario_path=scenario_path,
        runtime_id=runtime_id,
        workspace_root=workspace_root,
    )
    state = execute_eval_scenario(prep)
    classification = classify_eval_execution(prep=prep, state=state)
    return persist_eval_reports(
        EvalReportPersistenceContext(
            prep=prep,
            state=state,
            classification=classification,
            started=started,
        )
    )


# Compatibility aliases for older white-box tests and local debug scripts.
_EXIT_CODE_PATTERN = EXIT_CODE_PATTERN
_PASS_GUARD_REQUIRED_OUTPUT_FILES = PASS_GUARD_REQUIRED_OUTPUT_FILES
_build_feature_selection_payload = build_feature_selection_payload
_classify_eval_execution = classify_eval_execution
_classify_status = classify_status
_combined_run_output = combined_run_output
_command_transcripts_from_error = command_transcripts_from_error
_derive_aidd_command = derive_aidd_command
_derive_run_id = derive_run_id
_derive_teardown_commands = derive_teardown_commands
_derive_work_item = derive_work_item
_extract_exit_code = extract_exit_code
_grader_payload = grader_payload
_has_noop_execution_signal = has_noop_execution_signal
_has_unsupported_runtime_signal = has_unsupported_runtime_signal
_is_missing_answers_failure = is_missing_answers_failure
_missing_required_pass_artifacts = missing_required_pass_artifacts
_partial_quality_result = partial_quality_result
_partial_setup_result = partial_setup_result
_partial_teardown_result = partial_teardown_result
_partial_verification_result = partial_verification_result
_persist_eval_reports = persist_eval_reports
_prepare_eval_run = prepare_eval_run
_render_log_analysis_markdown = render_log_analysis_markdown
_render_runtime_log_source = render_runtime_log_source
_render_validator_report_source = render_validator_report_source
_resolve_stage_scope_for_pass_guard = resolve_stage_scope_for_pass_guard
_select_authored_task = select_authored_task
_stage_failure_events_from_timing_payload = stage_failure_events_from_timing_payload
_transcript_duration = transcript_duration
_workspace_root_for_quality = workspace_root_for_quality
_write_source_artifacts = write_source_artifacts


__all__ = [
    "EvalClassification",
    "EvalExecutionState",
    "EvalReportPersistenceContext",
    "EvalRunPreparation",
    "EvalRuntimeLogSourceContext",
    "EvalScenarioRunResult",
    "run_eval_scenario",
]

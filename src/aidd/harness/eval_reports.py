from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from aidd.core.run_store import (
    RUN_EVENTS_JSONL_FILENAME,
    RUN_RUNTIME_JSONL_FILENAME,
    work_item_runs_root,
)
from aidd.evals.log_analysis import (
    CoarseRuntimeEvent,
    FailureBoundarySelection,
    NormalizedRuntimeEvent,
    parse_events_jsonl_text,
    parse_runtime_log_text,
    parse_validator_report_failures_text,
    select_first_failure_boundary,
    summarize_runtime_provider_diagnostics,
)
from aidd.evals.reporting import (
    SUMMARY_REPORT_FILENAME,
    build_scenario_summary_row,
    write_eval_summary_markdown,
)
from aidd.evals.stage_timing import (
    build_stage_timing_payload,
    render_repair_history_markdown,
    render_stage_timing_markdown,
    write_stage_timing_artifacts,
)
from aidd.evals.verdicts import (
    HarnessOutcome,
    ScenarioVerdict,
    VerdictStatus,
    build_scenario_verdict_from_harness_outcome,
)
from aidd.harness.eval_models import (
    EvalReportPersistenceContext,
    EvalRuntimeLogSourceContext,
    EvalScenarioRunResult,
)
from aidd.harness.eval_report_writers import write_eval_source_artifacts
from aidd.harness.result_bundle import (
    ResultBundleLayout,
    copy_or_link_run_artifacts,
    write_command_transcripts,
    write_harness_metadata,
)
from aidd.harness.scenarios import Scenario
from aidd.runtime_catalog import get_runtime_definition

EXIT_CODE_PATTERN = re.compile(r"non-zero exit \((?P<code>\d+)\)")


@dataclass(frozen=True, slots=True)
class RuntimeTimeoutAttempt:
    stage: str
    attempt: str
    runtime_exit_classification: str
    runtime_exit_code: str


@dataclass(frozen=True, slots=True)
class RuntimeTimeoutConfig:
    default_timeout_seconds: float | None
    stage_timeout_seconds: dict[str, float]


def _collect_attempt_jsonl_artifacts(
    *,
    workspace_root: Path | None,
    work_item: str,
    filename: str,
) -> tuple[Path, ...]:
    if workspace_root is None:
        return tuple()
    runs_root = work_item_runs_root(workspace_root=workspace_root, work_item=work_item)
    if not runs_root.exists():
        return tuple()
    return tuple(
        sorted(
            path
            for path in runs_root.glob(f"*/stages/*/attempts/attempt-*/{filename}")
            if path.is_file()
        )
    )


def _write_concatenated_jsonl_source(
    *,
    layout: ResultBundleLayout,
    filename: str,
    source_paths: tuple[Path, ...],
) -> Path | None:
    if not source_paths:
        return None
    sources_root = layout.run_root / "_sources"
    sources_root.mkdir(parents=True, exist_ok=True)
    destination_path = sources_root / filename
    lines: list[str] = []
    for source_path in source_paths:
        source_text = source_path.read_text(encoding="utf-8").strip()
        if source_text:
            lines.extend(source_text.splitlines())
    if not lines:
        return None
    destination_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination_path


def extract_exit_code(error: BaseException | None) -> int | None:
    if error is None:
        return None
    failed_exit_code = getattr(error, "failed_exit_code", None)
    if isinstance(failed_exit_code, int):
        return failed_exit_code
    if match := EXIT_CODE_PATTERN.search(str(error)):
        return int(match.group("code"))
    return None


def stage_failure_events_from_timing_payload(
    payload: dict[str, object],
) -> tuple[CoarseRuntimeEvent, ...]:
    raw_stages = payload.get("stages", [])
    if not isinstance(raw_stages, list):
        return tuple()

    events: list[CoarseRuntimeEvent] = []
    for stage_index, raw_stage in enumerate(raw_stages, start=1):
        if not isinstance(raw_stage, dict):
            continue
        stage = str(raw_stage.get("stage") or "unknown")
        stage_status = str(raw_stage.get("status") or "unknown")
        if stage_status not in {"failed", "blocked"}:
            continue
        final_failure_code = str(raw_stage.get("final_failure_code") or "").strip()
        raw_attempts = raw_stage.get("attempts")
        attempts = raw_attempts if isinstance(raw_attempts, list) else []
        for attempt_index, raw_attempt in enumerate(attempts, start=1):
            if not isinstance(raw_attempt, dict):
                continue
            validation_result = str(raw_attempt.get("validation_result") or "unknown")
            terminal_status = str(raw_attempt.get("terminal_status") or stage_status)
            runtime_exit = raw_attempt.get("runtime_exit_classification")
            failed_validation = validation_result in {"failed", "blocked"}
            failed_terminal = (
                attempt_index == len(attempts)
                and terminal_status in {"failed", "blocked"}
            )
            failed_runtime = runtime_exit not in (None, "success")
            if not (failed_validation or failed_terminal or failed_runtime):
                continue
            attempt_number = raw_attempt.get("attempt", attempt_index)
            repair_reason = str(raw_attempt.get("repair_reason") or "n/a")
            failure_detail = f"repair reason: {repair_reason}"
            if attempt_index == len(attempts) and final_failure_code:
                failure_detail = f"final failure code `{final_failure_code}`"
                if repair_reason != "n/a":
                    failure_detail = (
                        f"{failure_detail}; preceding repair reason: {repair_reason}"
                    )
            events.append(
                CoarseRuntimeEvent(
                    line_number=(stage_index * 100) + attempt_index,
                    category="validator",
                    message=(
                        f"stage `{stage}` attempt `{attempt_number}` validator "
                        f"`{validation_result}`; terminal status `{terminal_status}`; "
                        f"runtime exit `{runtime_exit or 'unknown'}`; "
                        f"{failure_detail}"
                    ),
                )
            )
    return tuple(events)


def render_runtime_log_source(context: EvalRuntimeLogSourceContext) -> str:
    prep = context.prep
    state = context.state
    scenario = prep.scenario
    lines = [
        f"run_id={prep.run_id}",
        f"scenario_id={scenario.scenario_id}",
        f"runtime_id={prep.runtime_id}",
    ]

    if state.prepared_repository is not None:
        lines.append(
            f"prepared_repository={state.prepared_repository.repo_path.as_posix()}"
        )
        lines.append(f"resolved_revision={state.prepared_repository.resolved_revision}")
    if state.prepared_working_copy is not None:
        lines.append(
            f"working_copy={state.prepared_working_copy.working_copy_path.as_posix()}"
        )
    if state.install_result is not None:
        lines.append(f"install_channel={state.install_result.install_channel}")
        lines.append(f"artifact_source={state.install_result.artifact_source}")
        lines.append(f"artifact_identity={state.install_result.artifact_identity}")
        lines.append(f"install_home={state.install_result.install_home.as_posix()}")
        lines.append(
            f"installed_command={' '.join(state.install_result.installed_command)}"
        )
        lines.append(f"install_commands={len(state.install_result.command_transcripts)}")
        for transcript in state.install_result.command_transcripts:
            lines.append(f"install_command={transcript.command}")
            lines.append(f"install_command_exit_code={transcript.exit_code}")
            if transcript.stdout_text.strip():
                lines.append("install_stdout:")
                lines.extend(transcript.stdout_text.rstrip().splitlines())
            if transcript.stderr_text.strip():
                lines.append("install_stderr:")
                lines.extend(transcript.stderr_text.rstrip().splitlines())

    if state.setup_result is not None:
        lines.append(f"setup_commands={len(state.setup_result.command_transcripts)}")
    if state.aidd_run_result is not None:
        lines.append(f"aidd_exit_code={state.aidd_run_result.exit_code}")
        if state.aidd_run_result.stdout_text.strip():
            lines.append("aidd_stdout:")
            lines.extend(state.aidd_run_result.stdout_text.rstrip().splitlines())
        if state.aidd_run_result.stderr_text.strip():
            lines.append("aidd_stderr:")
            lines.extend(state.aidd_run_result.stderr_text.rstrip().splitlines())
    if state.verification_result is not None:
        lines.append(
            f"verification_commands={len(state.verification_result.command_transcripts)}"
        )
    if state.teardown_result is not None:
        lines.append(f"teardown_commands={len(state.teardown_result.command_transcripts)}")

    for error in (
        state.prep_error,
        state.install_error,
        state.setup_error,
        state.run_error,
        state.verification_error,
        state.teardown_error,
    ):
        if error is not None:
            lines.append(f"error={error}")

    return "\n".join(lines).rstrip() + "\n"


def render_validator_report_source(
    *,
    status: VerdictStatus,
    summary: str,
    prep_error: BaseException | None,
    install_error: BaseException | None,
    setup_error: BaseException | None,
    run_error: BaseException | None,
    verification_error: BaseException | None,
    teardown_error: BaseException | None,
) -> str:
    verdict = "pass" if status == "pass" else "fail"
    lines = [
        "# Validator report",
        "",
        "## Verdict",
        f"- Verdict: `{verdict}`",
    ]
    if status == "pass":
        lines.extend(("", "## Findings", "- none", ""))
        return "\n".join(lines)

    if status == "blocked":
        code = "HARNESS_INTERVIEW_BLOCKED"
        message = summary
        location = "verify"
    elif install_error is not None:
        code = "HARNESS_INSTALL_FAILURE"
        message = str(install_error)
        location = "install"
    elif status == "infra-fail":
        code = "HARNESS_INFRA_FAILURE"
        error = prep_error or setup_error or teardown_error
        message = str(error) if error is not None else summary
        location = "harness"
    else:
        code = "HARNESS_SCENARIO_FAILURE"
        error = verification_error or run_error or setup_error
        message = str(error) if error is not None else summary
        location = "verify"

    lines.extend(
        (
            "",
            "## Findings",
            f"- `{code}` (`error`) in {location}: {message}",
            "",
        )
    )
    return "\n".join(lines)


def render_log_analysis_markdown(
    *,
    status: VerdictStatus,
    boundary: FailureBoundarySelection,
    runtime_diagnostics_markdown: str | None = None,
    stage_timing_markdown: str | None = None,
) -> str:
    signal_line = (
        str(boundary.signal_line_number)
        if boundary.signal_line_number is not None
        else "n/a"
    )
    base = (
        "# Log Analysis\n\n"
        f"- Status: `{status}`\n"
        f"- First Failure Boundary: `{boundary.category}`\n"
        f"- Signal Source: `{boundary.signal_source}`\n"
        f"- Signal Line: `{signal_line}`\n"
        f"- Reason: {boundary.reason}\n"
    )
    sections = [base.rstrip()]
    if runtime_diagnostics_markdown is not None:
        sections.append(runtime_diagnostics_markdown.rstrip())
    if stage_timing_markdown is not None:
        sections.append(stage_timing_markdown.rstrip())
    return "\n\n".join(sections) + "\n"


def _format_timeout_seconds(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}s"


def _float_config_value(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _runtime_timeout_config(
    *,
    runtime_id: str,
    runtime_config_path: Path | None,
) -> RuntimeTimeoutConfig:
    if runtime_config_path is None or not runtime_config_path.exists():
        return RuntimeTimeoutConfig(
            default_timeout_seconds=None,
            stage_timeout_seconds={},
        )

    try:
        data = tomllib.loads(runtime_config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return RuntimeTimeoutConfig(
            default_timeout_seconds=None,
            stage_timeout_seconds={},
        )

    runtime_section = data.get("runtime")
    if not isinstance(runtime_section, dict):
        return RuntimeTimeoutConfig(
            default_timeout_seconds=None,
            stage_timeout_seconds={},
        )

    runtime_definition = get_runtime_definition(runtime_id)
    raw_runtime_config = runtime_section.get(runtime_definition.config_section)
    if not isinstance(raw_runtime_config, dict):
        return RuntimeTimeoutConfig(
            default_timeout_seconds=None,
            stage_timeout_seconds={},
        )

    raw_stage_timeouts = raw_runtime_config.get("stage_timeouts")
    stage_timeouts: dict[str, float] = {}
    if isinstance(raw_stage_timeouts, dict):
        for raw_stage, raw_value in raw_stage_timeouts.items():
            if not isinstance(raw_stage, str):
                continue
            timeout_seconds = _float_config_value(raw_value)
            if timeout_seconds is not None:
                stage_timeouts[raw_stage] = timeout_seconds

    return RuntimeTimeoutConfig(
        default_timeout_seconds=_float_config_value(raw_runtime_config.get("timeout_seconds")),
        stage_timeout_seconds=stage_timeouts,
    )


def _timed_out_stage_attempts(
    stage_timing_payload: dict[str, object],
) -> tuple[RuntimeTimeoutAttempt, ...]:
    raw_stages = stage_timing_payload.get("stages", [])
    stage_items = raw_stages if isinstance(raw_stages, list) else []
    attempts: list[RuntimeTimeoutAttempt] = []
    for raw_stage in stage_items:
        if not isinstance(raw_stage, dict):
            continue
        stage = str(raw_stage.get("stage") or "unknown")
        raw_attempts = raw_stage.get("attempts")
        attempt_items = raw_attempts if isinstance(raw_attempts, list) else []
        for raw_attempt in attempt_items:
            if not isinstance(raw_attempt, dict):
                continue
            runtime_exit_classification = str(
                raw_attempt.get("runtime_exit_classification") or "unknown"
            )
            timed_out = (
                bool(raw_attempt.get("timed_out"))
                or runtime_exit_classification == "timeout"
            )
            if not timed_out:
                continue
            attempts.append(
                RuntimeTimeoutAttempt(
                    stage=stage,
                    attempt=str(raw_attempt.get("attempt") or "n/a"),
                    runtime_exit_classification=runtime_exit_classification,
                    runtime_exit_code=str(raw_attempt.get("runtime_exit_code") or "n/a"),
                )
            )
    return tuple(attempts)


def _signal_summary(items: tuple[str, ...]) -> str:
    if not items:
        return "`none`"
    first = items[0].replace("`", "'")
    if len(items) == 1:
        return first
    return f"{first} ({len(items)} total; first shown)"


def _stage_timeout_summary(stage_timeouts: dict[str, float]) -> str:
    if not stage_timeouts:
        return "`none`"
    return ", ".join(
        f"`{stage}`={_format_timeout_seconds(timeout_seconds)}"
        for stage, timeout_seconds in stage_timeouts.items()
    )


def render_runtime_diagnostics_markdown(
    *,
    normalized_events: tuple[NormalizedRuntimeEvent, ...],
    stage_timing_payload: dict[str, object],
    runtime_id: str,
    runtime_config_path: Path | None,
    harness_timeout_seconds: float | None,
) -> str:
    provider_diagnostics = summarize_runtime_provider_diagnostics(normalized_events)
    timeout_config = _runtime_timeout_config(
        runtime_id=runtime_id,
        runtime_config_path=runtime_config_path,
    )
    timed_out_attempts = _timed_out_stage_attempts(stage_timing_payload)
    if timed_out_attempts:
        timeout_attempt_lines = []
        for attempt in timed_out_attempts:
            stage_budget = timeout_config.stage_timeout_seconds.get(
                attempt.stage,
                timeout_config.default_timeout_seconds,
            )
            timeout_attempt_lines.append(
                "`"
                f"{attempt.stage}` attempt `{attempt.attempt}` "
                f"runtime exit `{attempt.runtime_exit_classification}`/"
                f"`{attempt.runtime_exit_code}`, stage budget "
                f"`{_format_timeout_seconds(stage_budget)}`"
            )
        timeout_stage_budget = "; ".join(timeout_attempt_lines)
    else:
        timeout_stage_budget = "`none`"

    config_source = (
        "`n/a`"
        if runtime_config_path is None
        else f"`{runtime_config_path.as_posix()}`"
    )
    default_timeout = _format_timeout_seconds(timeout_config.default_timeout_seconds)
    stage_timeout_profile = _stage_timeout_summary(timeout_config.stage_timeout_seconds)
    return "\n".join(
        (
            "## Runtime Diagnostics",
            "",
            f"- Runtime ID: `{runtime_id}`",
            f"- Model/Profile Evidence: {_signal_summary(provider_diagnostics.model_profiles)}",
            f"- Retry Signals: {_signal_summary(provider_diagnostics.retry_signals)}",
            f"- Rate-Limit Signals: {_signal_summary(provider_diagnostics.rate_limit_signals)}",
            f"- Timeout Stage/Budget: {timeout_stage_budget}",
            f"- Default Runtime Timeout: `{default_timeout}`",
            f"- Stage Timeout Profile: {stage_timeout_profile}",
            f"- Harness Run Timeout: `{_format_timeout_seconds(harness_timeout_seconds)}`",
            f"- Timeout Config Source: {config_source}",
        )
    )


def write_source_artifacts(
    *,
    layout: ResultBundleLayout,
    runtime_log_source: str,
    validator_report_source: str,
    verdict: ScenarioVerdict,
) -> tuple[Path, Path, Path]:
    return write_eval_source_artifacts(
        layout=layout,
        runtime_log_source=runtime_log_source,
        validator_report_source=validator_report_source,
        verdict=verdict,
    )


def grader_payload(
    *,
    scenario: Scenario,
    run_id: str,
    runtime_id: str,
    status: VerdictStatus,
    summary: str,
    first_failure_boundary: FailureBoundarySelection,
    feature_selection_payload: dict[str, object],
) -> dict[str, object]:
    return {
        "execution": {
            "first_failure_boundary": {
                "category": first_failure_boundary.category,
                "reason": first_failure_boundary.reason,
                "signal_line_number": first_failure_boundary.signal_line_number,
                "signal_source": first_failure_boundary.signal_source,
            },
            "status": status,
            "summary": summary,
        },
        "run_id": run_id,
        "runtime_id": runtime_id,
        "scenario_id": scenario.scenario_id,
        "selected_task": feature_selection_payload.get("selected_task"),
    }


def persist_eval_reports(
    context: EvalReportPersistenceContext,
) -> EvalScenarioRunResult:
    prep = context.prep
    state = context.state
    classification = context.classification
    started = context.started
    scenario = prep.scenario
    layout = prep.layout
    run_id = prep.run_id
    runtime_id = prep.runtime_id
    work_item = prep.work_item
    status = classification.status
    summary = classification.summary

    runtime_log_source = render_runtime_log_source(
        EvalRuntimeLogSourceContext(prep=prep, state=state)
    )
    validator_report_source = render_validator_report_source(
        status=status,
        summary=summary,
        prep_error=state.prep_error,
        install_error=state.install_error,
        setup_error=state.setup_error,
        run_error=state.run_error,
        verification_error=state.verification_error,
        teardown_error=state.teardown_error,
    )
    stage_timing_payload = build_stage_timing_payload(
        scenario=scenario,
        run_id=run_id,
        runtime_id=runtime_id,
        work_item=work_item,
        workspace_root=(
            None
            if state.prepared_working_copy is None
            else state.prepared_working_copy.working_copy_path / ".aidd"
        ),
        total_duration_seconds=max(monotonic() - started, 0.0),
        install_result=state.install_result,
        setup_result=state.setup_result,
        aidd_run_result=state.aidd_run_result,
        verification_result=state.verification_result,
        teardown_result=state.teardown_result,
    )
    aidd_workspace_root = (
        None
        if state.prepared_working_copy is None
        else state.prepared_working_copy.working_copy_path / ".aidd"
    )
    runtime_jsonl_source_path = _write_concatenated_jsonl_source(
        layout=layout,
        filename=RUN_RUNTIME_JSONL_FILENAME,
        source_paths=_collect_attempt_jsonl_artifacts(
            workspace_root=aidd_workspace_root,
            work_item=work_item,
            filename=RUN_RUNTIME_JSONL_FILENAME,
        ),
    )
    events_jsonl_source_path = _write_concatenated_jsonl_source(
        layout=layout,
        filename=RUN_EVENTS_JSONL_FILENAME,
        source_paths=_collect_attempt_jsonl_artifacts(
            workspace_root=aidd_workspace_root,
            work_item=work_item,
            filename=RUN_EVENTS_JSONL_FILENAME,
        ),
    )
    normalized_events = (
        tuple()
        if events_jsonl_source_path is None
        else parse_events_jsonl_text(events_jsonl_source_path.read_text(encoding="utf-8"))
    )

    verification_exit_code = extract_exit_code(state.verification_error)
    first_failure_boundary = select_first_failure_boundary(
        runtime_events=parse_runtime_log_text(runtime_log_source),
        normalized_events=normalized_events,
        validator_failures=parse_validator_report_failures_text(
            validator_report_source
        ),
        stage_metadata_failures=stage_failure_events_from_timing_payload(
            stage_timing_payload
        ),
        aidd_exit_code=(
            None
            if state.aidd_run_result is None
            else state.aidd_run_result.exit_code
        ),
        verification_exit_code=verification_exit_code,
    )
    first_failure_note = (
        None
        if first_failure_boundary.category == "none"
        else f"{first_failure_boundary.signal_source}: {first_failure_boundary.reason}"
    )

    outcome = HarnessOutcome(
        aidd_exit_code=(
            None
            if state.aidd_run_result is None
            else state.aidd_run_result.exit_code
        ),
        verification_failed=classification.verification_failed,
        blocked_by_questions=classification.blocked_by_questions,
        infrastructure_failure=classification.infrastructure_failure,
    )
    verdict = build_scenario_verdict_from_harness_outcome(
        scenario_id=scenario.scenario_id,
        run_id=run_id,
        runtime_id=runtime_id,
        outcome=outcome,
        summary=summary,
        artifact_links=(
            layout.runtime_log_path.as_posix(),
            layout.validator_report_path.as_posix(),
            layout.verdict_path.as_posix(),
        ),
        first_failure_note=first_failure_note,
        verification_summary=(
            "verification command(s) passed"
            if state.verification_result is not None
            and state.verification_error is None
            else "verification command returned non-zero status"
            if state.verification_error is not None
            else None
        ),
    )

    runtime_log_source_path, validator_report_source_path, verdict_source_path = (
        write_source_artifacts(
            layout=layout,
            runtime_log_source=runtime_log_source,
            validator_report_source=validator_report_source,
            verdict=verdict,
        )
    )

    write_harness_metadata(
        layout=layout,
        scenario=scenario,
        runtime_id=runtime_id,
        work_item=work_item,
        status=status,
        install_result=state.install_result,
        target_repository_cwd=(
            None
            if state.prepared_working_copy is None
            else state.prepared_working_copy.working_copy_path
        ),
        workspace_root=(
            None
            if state.prepared_working_copy is None
            else state.prepared_working_copy.working_copy_path / ".aidd"
        ),
        resource_source=(
            "packaged" if state.install_result is not None else prep.resource_layout.source
        ),
        aidd_run_id=None if state.aidd_run_result is None else run_id,
        aidd_run_result=state.aidd_run_result,
        aidd_artifact_references={
            "scenario_path": prep.scenario_path.as_posix(),
            "runtime_log_source": runtime_log_source_path.as_posix(),
            "validator_report_source": validator_report_source_path.as_posix(),
            "verdict_source": verdict_source_path.as_posix(),
            "runtime_jsonl_source": (
                "n/a"
                if runtime_jsonl_source_path is None
                else runtime_jsonl_source_path.as_posix()
            ),
            "events_jsonl_source": (
                "n/a" if events_jsonl_source_path is None else events_jsonl_source_path.as_posix()
            ),
            "resource_source": (
                "packaged"
                if state.install_result is not None
                else prep.resource_layout.source
            ),
            "artifact_path": (
                "n/a"
                if state.install_result is None
                else (
                    state.install_result.artifact_identity
                    if state.install_result.artifact_path is None
                    else state.install_result.artifact_path.as_posix()
                )
            ),
            "feature_selection_path": layout.feature_selection_path.as_posix(),
            "working_copy_path": (
                state.prepared_working_copy.working_copy_path.as_posix()
                if state.prepared_working_copy is not None
                else "n/a"
            ),
            "live_runtime_config_path": (
                state.live_runtime_config_path.as_posix()
                if state.live_runtime_config_path is not None
                else "n/a"
            ),
        },
    )
    write_command_transcripts(
        layout=layout,
        install_result=state.install_result,
        setup_result=state.setup_result,
        aidd_run_result=state.aidd_run_result,
        verification_result=state.verification_result,
        teardown_result=state.teardown_result,
    )
    copy_or_link_run_artifacts(
        layout=layout,
        runtime_log_path=runtime_log_source_path,
        validator_report_path=validator_report_source_path,
        verdict_path=verdict_source_path,
        runtime_jsonl_path=runtime_jsonl_source_path,
        events_jsonl_path=events_jsonl_source_path,
    )

    write_stage_timing_artifacts(layout=layout, payload=stage_timing_payload)
    rendered_stage_timing = render_stage_timing_markdown(stage_timing_payload)
    layout.log_analysis_path.write_text(
        render_log_analysis_markdown(
            status=status,
            boundary=first_failure_boundary,
            runtime_diagnostics_markdown=render_runtime_diagnostics_markdown(
                normalized_events=normalized_events,
                stage_timing_payload=stage_timing_payload,
                runtime_id=runtime_id,
                runtime_config_path=state.live_runtime_config_path,
                harness_timeout_seconds=(
                    None
                    if state.aidd_run_result is None
                    else state.aidd_run_result.timeout_seconds
                ),
            ),
            stage_timing_markdown=rendered_stage_timing,
        ),
        encoding="utf-8",
    )
    layout.grader_path.write_text(
        json.dumps(
            grader_payload(
                scenario=scenario,
                run_id=run_id,
                runtime_id=runtime_id,
                status=status,
                summary=summary,
                first_failure_boundary=first_failure_boundary,
                feature_selection_payload=prep.feature_selection_payload,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    layout.repair_history_path.write_text(
        render_repair_history_markdown(stage_timing_payload),
        encoding="utf-8",
    )

    duration_seconds = max(monotonic() - started, 0.0)
    scenario_row = build_scenario_summary_row(
        verdict=verdict,
        duration_seconds=duration_seconds,
        failure_boundary=first_failure_boundary.category,
    )
    summary_path = write_eval_summary_markdown(
        path=layout.run_root / SUMMARY_REPORT_FILENAME,
        scenario_rows=(scenario_row,),
    )
    summary_path.write_text(
        summary_path.read_text(encoding="utf-8") + "\n" + rendered_stage_timing,
        encoding="utf-8",
    )

    return EvalScenarioRunResult(
        scenario_id=scenario.scenario_id,
        run_id=run_id,
        runtime_id=runtime_id,
        status=status,
        bundle_root=layout.run_root,
        verdict_path=layout.verdict_path,
        summary_path=summary_path,
        feature_selection_path=layout.feature_selection_path,
        first_failure_boundary=first_failure_boundary,
        first_failure_note=first_failure_note,
    )

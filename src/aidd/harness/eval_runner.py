from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from aidd.evals.log_analysis import (
    FailureBoundarySelection,
    parse_runtime_log_text,
    parse_validator_report_failures_text,
    select_first_failure_boundary,
)
from aidd.evals.reporting import (
    SUMMARY_REPORT_FILENAME,
    build_scenario_summary_row,
    write_eval_summary_markdown,
)
from aidd.evals.verdicts import (
    HarnessOutcome,
    ScenarioVerdict,
    VerdictStatus,
    build_scenario_verdict_from_harness_outcome,
    write_scenario_verdict_markdown,
)
from aidd.harness.repo_prep import (
    PreparedRepository,
    PreparedWorkingCopy,
    prepare_scenario_repository,
    prepare_working_copy,
    prepare_workspace,
)
from aidd.harness.result_bundle import (
    ResultBundleLayout,
    copy_or_link_run_artifacts,
    ensure_result_bundle_layout,
    write_command_transcripts,
    write_harness_metadata,
)
from aidd.harness.runner import (
    HarnessAiddRunResult,
    HarnessSetupError,
    HarnessSetupResult,
    HarnessTeardownError,
    HarnessTeardownResult,
    HarnessVerificationError,
    HarnessVerificationResult,
    invoke_aidd_run,
    run_setup_steps,
    run_teardown_steps,
    run_verification_steps,
)
from aidd.harness.scenarios import Scenario, load_scenario

_EXIT_CODE_PATTERN = re.compile(r"non-zero exit \((?P<code>\d+)\)")


@dataclass(frozen=True, slots=True)
class EvalScenarioRunResult:
    scenario_id: str
    run_id: str
    runtime_id: str
    status: VerdictStatus
    bundle_root: Path
    verdict_path: Path
    summary_path: Path
    first_failure_boundary: FailureBoundarySelection
    first_failure_note: str | None


def _derive_run_id(*, scenario_id: str, runtime_id: str) -> str:
    suffix = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    normalized_scenario = scenario_id.strip().lower().replace("aidd-", "")
    normalized_scenario = normalized_scenario.replace("_", "-")
    return f"eval-{normalized_scenario}-{runtime_id}-{suffix}"


def _derive_aidd_command(scenario: Scenario) -> tuple[str, ...]:
    raw_invocation = scenario.raw.get("aidd_invocation")
    if isinstance(raw_invocation, dict):
        raw_command = raw_invocation.get("command")
        if isinstance(raw_command, list):
            command_tokens = tuple(
                str(token).strip() for token in raw_command if str(token).strip()
            )
            if command_tokens:
                if command_tokens[-1] == "run":
                    command_tokens = command_tokens[:-1]
                if command_tokens:
                    return command_tokens

    return (sys.executable, "-m", "aidd.cli.main")


def _derive_work_item(scenario: Scenario) -> str:
    raw_invocation = scenario.raw.get("aidd_invocation")
    if isinstance(raw_invocation, dict):
        raw_work_item = raw_invocation.get("work_item")
        if isinstance(raw_work_item, str) and raw_work_item.strip():
            return raw_work_item.strip()

    normalized = scenario.scenario_id.strip().upper().replace("-", "_")
    return f"WI-EVAL-{normalized}"


def _derive_teardown_commands(scenario: Scenario) -> tuple[str, ...]:
    raw_teardown = scenario.raw.get("teardown")
    if not isinstance(raw_teardown, dict):
        return tuple()

    raw_commands = raw_teardown.get("commands")
    if not isinstance(raw_commands, list):
        return tuple()

    commands = tuple(str(command).strip() for command in raw_commands if str(command).strip())
    return commands


def _extract_exit_code(error: BaseException | None) -> int | None:
    if error is None:
        return None
    if match := _EXIT_CODE_PATTERN.search(str(error)):
        return int(match.group("code"))
    return None


def _is_missing_answers_failure(error: BaseException | None) -> bool:
    if error is None:
        return False
    text = str(error).lower()
    return "answers.md" in text and ("test -f" in text or "no such file" in text)


def _classify_status(
    *,
    scenario: Scenario,
    prep_error: BaseException | None,
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

    blocked_by_questions = scenario.run.interview_required and _is_missing_answers_failure(
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


def _render_runtime_log_source(
    *,
    scenario: Scenario,
    runtime_id: str,
    run_id: str,
    prepared_repository: PreparedRepository | None,
    prepared_working_copy: PreparedWorkingCopy | None,
    setup_result: HarnessSetupResult | None,
    aidd_run_result: HarnessAiddRunResult | None,
    verification_result: HarnessVerificationResult | None,
    teardown_result: HarnessTeardownResult | None,
    prep_error: BaseException | None,
    setup_error: BaseException | None,
    run_error: BaseException | None,
    verification_error: BaseException | None,
    teardown_error: BaseException | None,
) -> str:
    lines = [
        f"run_id={run_id}",
        f"scenario_id={scenario.scenario_id}",
        f"runtime_id={runtime_id}",
    ]

    if prepared_repository is not None:
        lines.append(f"prepared_repository={prepared_repository.repo_path.as_posix()}")
        lines.append(f"resolved_revision={prepared_repository.resolved_revision}")
    if prepared_working_copy is not None:
        lines.append(f"working_copy={prepared_working_copy.working_copy_path.as_posix()}")

    if setup_result is not None:
        lines.append(f"setup_commands={len(setup_result.command_transcripts)}")
    if aidd_run_result is not None:
        lines.append(f"aidd_exit_code={aidd_run_result.exit_code}")
        if aidd_run_result.stdout_text.strip():
            lines.append("aidd_stdout:")
            lines.extend(aidd_run_result.stdout_text.rstrip().splitlines())
        if aidd_run_result.stderr_text.strip():
            lines.append("aidd_stderr:")
            lines.extend(aidd_run_result.stderr_text.rstrip().splitlines())
    if verification_result is not None:
        lines.append(f"verification_commands={len(verification_result.command_transcripts)}")
    if teardown_result is not None:
        lines.append(f"teardown_commands={len(teardown_result.command_transcripts)}")

    for error in (prep_error, setup_error, run_error, verification_error, teardown_error):
        if error is not None:
            lines.append(f"error={error}")

    return "\n".join(lines).rstrip() + "\n"


def _render_validator_report_source(
    *,
    status: VerdictStatus,
    summary: str,
    prep_error: BaseException | None,
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


def _render_log_analysis_markdown(
    *,
    status: VerdictStatus,
    boundary: FailureBoundarySelection,
) -> str:
    signal_line = (
        str(boundary.signal_line_number)
        if boundary.signal_line_number is not None
        else "n/a"
    )
    return (
        "# Log Analysis\n\n"
        f"- Status: `{status}`\n"
        f"- First Failure Boundary: `{boundary.category}`\n"
        f"- Signal Source: `{boundary.signal_source}`\n"
        f"- Signal Line: `{signal_line}`\n"
        f"- Reason: {boundary.reason}\n"
    )


def _write_source_artifacts(
    *,
    layout: ResultBundleLayout,
    runtime_log_source: str,
    validator_report_source: str,
    verdict: ScenarioVerdict,
) -> tuple[Path, Path, Path]:
    sources_root = layout.run_root / "_sources"
    sources_root.mkdir(parents=True, exist_ok=True)
    runtime_log_source_path = sources_root / "runtime.log"
    validator_report_source_path = sources_root / "validator-report.md"
    verdict_source_path = sources_root / "verdict.md"

    runtime_log_source_path.write_text(runtime_log_source, encoding="utf-8")
    validator_report_source_path.write_text(validator_report_source, encoding="utf-8")
    write_scenario_verdict_markdown(path=verdict_source_path, verdict=verdict)
    return runtime_log_source_path, validator_report_source_path, verdict_source_path


def run_eval_scenario(
    *,
    scenario_path: Path,
    runtime_id: str,
    workspace_root: Path = Path(".aidd"),
) -> EvalScenarioRunResult:
    scenario = load_scenario(scenario_path, runtime_id=runtime_id, workspace_root=workspace_root)
    run_id = _derive_run_id(scenario_id=scenario.scenario_id, runtime_id=runtime_id)
    layout = ensure_result_bundle_layout(workspace_root=workspace_root, run_id=run_id)
    prepare_workspace(workspace_root)

    cache_root = workspace_root / "harness-cache"
    aidd_command = _derive_aidd_command(scenario)
    work_item = _derive_work_item(scenario)
    teardown_commands = _derive_teardown_commands(scenario)

    prep_error: BaseException | None = None
    setup_error: BaseException | None = None
    run_error: BaseException | None = None
    verification_error: BaseException | None = None
    teardown_error: BaseException | None = None

    prepared_repository: PreparedRepository | None = None
    prepared_working_copy: PreparedWorkingCopy | None = None
    setup_result: HarnessSetupResult | None = None
    aidd_run_result: HarnessAiddRunResult | None = None
    verification_result: HarnessVerificationResult | None = None
    teardown_result: HarnessTeardownResult | None = None

    started = monotonic()
    try:
        prepared_repository = prepare_scenario_repository(cache_root=cache_root, scenario=scenario)
        prepared_working_copy = prepare_working_copy(
            cache_root=cache_root,
            scenario=scenario,
            prepared_repository=prepared_repository,
            run_id=run_id,
        )
    except BaseException as exc:
        prep_error = exc
    else:
        try:
            setup_result = run_setup_steps(
                scenario=scenario,
                working_copy_path=prepared_working_copy.working_copy_path,
            )
            aidd_run_result = invoke_aidd_run(
                scenario=scenario,
                working_copy_path=prepared_working_copy.working_copy_path,
                runtime_id=runtime_id,
                work_item=work_item,
                aidd_command=aidd_command,
            )
            verification_result = run_verification_steps(
                scenario=scenario,
                working_copy_path=prepared_working_copy.working_copy_path,
                aidd_run_result=aidd_run_result,
            )
        except HarnessSetupError as exc:
            setup_error = exc
        except HarnessVerificationError as exc:
            verification_error = exc
        except RuntimeError as exc:
            run_error = exc
        finally:
            try:
                teardown_result = run_teardown_steps(
                    teardown_commands=teardown_commands,
                    working_copy_path=prepared_working_copy.working_copy_path,
                )
            except HarnessTeardownError as exc:
                teardown_error = exc

    status, summary, blocked_by_questions, infrastructure_failure, verification_failed = (
        _classify_status(
            scenario=scenario,
            prep_error=prep_error,
            setup_error=setup_error,
            run_error=run_error,
            verification_error=verification_error,
            teardown_error=teardown_error,
            aidd_run_result=aidd_run_result,
        )
    )

    runtime_log_source = _render_runtime_log_source(
        scenario=scenario,
        runtime_id=runtime_id,
        run_id=run_id,
        prepared_repository=prepared_repository,
        prepared_working_copy=prepared_working_copy,
        setup_result=setup_result,
        aidd_run_result=aidd_run_result,
        verification_result=verification_result,
        teardown_result=teardown_result,
        prep_error=prep_error,
        setup_error=setup_error,
        run_error=run_error,
        verification_error=verification_error,
        teardown_error=teardown_error,
    )
    validator_report_source = _render_validator_report_source(
        status=status,
        summary=summary,
        prep_error=prep_error,
        setup_error=setup_error,
        run_error=run_error,
        verification_error=verification_error,
        teardown_error=teardown_error,
    )

    verification_exit_code = _extract_exit_code(verification_error)
    first_failure_boundary = select_first_failure_boundary(
        runtime_events=parse_runtime_log_text(runtime_log_source),
        validator_failures=parse_validator_report_failures_text(validator_report_source),
        aidd_exit_code=None if aidd_run_result is None else aidd_run_result.exit_code,
        verification_exit_code=verification_exit_code,
    )
    first_failure_note = (
        None
        if first_failure_boundary.category == "none"
        else (
            f"{first_failure_boundary.signal_source}: "
            f"{first_failure_boundary.reason}"
        )
    )

    outcome = HarnessOutcome(
        aidd_exit_code=None if aidd_run_result is None else aidd_run_result.exit_code,
        verification_failed=verification_failed,
        blocked_by_questions=blocked_by_questions,
        infrastructure_failure=infrastructure_failure,
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
            if verification_result is not None and verification_error is None
            else "verification command returned non-zero status"
            if verification_error is not None
            else None
        ),
    )

    runtime_log_source_path, validator_report_source_path, verdict_source_path = (
        _write_source_artifacts(
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
        aidd_run_id=None if aidd_run_result is None else run_id,
        aidd_run_result=aidd_run_result,
        aidd_artifact_references={
            "scenario_path": scenario_path.as_posix(),
            "runtime_log_source": runtime_log_source_path.as_posix(),
            "validator_report_source": validator_report_source_path.as_posix(),
            "verdict_source": verdict_source_path.as_posix(),
            "working_copy_path": (
                prepared_working_copy.working_copy_path.as_posix()
                if prepared_working_copy is not None
                else "n/a"
            ),
        },
    )
    write_command_transcripts(
        layout=layout,
        setup_result=setup_result,
        aidd_run_result=aidd_run_result,
        verification_result=verification_result,
        teardown_result=teardown_result,
    )
    copy_or_link_run_artifacts(
        layout=layout,
        runtime_log_path=runtime_log_source_path,
        validator_report_path=validator_report_source_path,
        verdict_path=verdict_source_path,
    )

    layout.log_analysis_path.write_text(
        _render_log_analysis_markdown(status=status, boundary=first_failure_boundary),
        encoding="utf-8",
    )
    layout.grader_path.write_text(
        json.dumps(
            {
                "scenario_id": scenario.scenario_id,
                "run_id": run_id,
                "runtime_id": runtime_id,
                "status": status,
                "first_failure_boundary": {
                    "category": first_failure_boundary.category,
                    "signal_source": first_failure_boundary.signal_source,
                    "signal_line_number": first_failure_boundary.signal_line_number,
                    "reason": first_failure_boundary.reason,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    layout.repair_history_path.write_text(
        "# Repair history\n\n- No repair loop executed by harness eval runner.\n",
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

    return EvalScenarioRunResult(
        scenario_id=scenario.scenario_id,
        run_id=run_id,
        runtime_id=runtime_id,
        status=status,
        bundle_root=layout.run_root,
        verdict_path=layout.verdict_path,
        summary_path=summary_path,
        first_failure_boundary=first_failure_boundary,
        first_failure_note=first_failure_note,
    )


__all__ = [
    "EvalScenarioRunResult",
    "run_eval_scenario",
]

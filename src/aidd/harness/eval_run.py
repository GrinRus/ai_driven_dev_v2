from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from shutil import copy2
from uuid import uuid4

from aidd.core.run_lookup import (
    latest_attempt_number,
    latest_run_id,
    resolve_attempt_artifact_paths,
)
from aidd.core.run_store import run_stage_metadata_path
from aidd.core.stages import STAGES
from aidd.evals.grader_pipeline import build_eval_grader_payload, write_grader_payload
from aidd.evals.log_analysis import (
    classify_failure_taxonomy,
    parse_events_jsonl,
    parse_runtime_log_text,
    parse_stage_metadata_validation_failures,
    parse_validator_report_failures,
    select_first_failure_boundary,
)
from aidd.evals.reporting import (
    aggregate_runtime_summary_rows,
    build_scenario_summary_row,
    write_eval_summary_markdown,
)
from aidd.evals.verdicts import (
    HarnessOutcome,
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


@dataclass(frozen=True, slots=True)
class EvalRunOutcome:
    eval_run_id: str
    scenario_id: str
    runtime_id: str
    verdict_status: str
    summary_path: Path
    verdict_path: Path
    bundle_root: Path
    aidd_exit_code: int | None
    failure_boundary: str


@dataclass(frozen=True, slots=True)
class _LatestStageArtifact:
    run_id: str
    stage: str
    attempt_number: int
    runtime_log_path: Path | None
    events_jsonl_path: Path | None
    validator_report_path: Path | None
    stage_metadata_path: Path


def _generate_eval_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"eval-{timestamp}-{uuid4().hex[:8]}"


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def _scenario_cache_root(*, workspace_root: Path) -> Path:
    return workspace_root / "traces" / "harness-cache"


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _copy_optional_file(
    *,
    source: Path | None,
    destination: Path,
    fallback: str | None = None,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source is not None and source.exists():
        copy2(source, destination)
        return destination
    destination.write_text(fallback or "", encoding="utf-8")
    return destination


def _find_latest_stage_artifact(
    *,
    workspace_root: Path,
    work_item: str,
) -> _LatestStageArtifact | None:
    run_id = latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if run_id is None:
        return None

    for stage in reversed(STAGES):
        attempt_number = latest_attempt_number(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        if attempt_number is None:
            continue
        artifact_paths = resolve_attempt_artifact_paths(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
        if artifact_paths is None:
            continue
        return _LatestStageArtifact(
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
            runtime_log_path=artifact_paths.logs.get("runtime_log"),
            events_jsonl_path=artifact_paths.logs.get("events_jsonl"),
            validator_report_path=artifact_paths.documents.get("validator_report"),
            stage_metadata_path=run_stage_metadata_path(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            ),
        )
    return None


def _detect_blocked_stage(*, workspace_root: Path, work_item: str) -> bool:
    run_id = latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if run_id is None:
        return False
    for stage in STAGES:
        metadata_path = run_stage_metadata_path(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        metadata_text = _read_optional(metadata_path)
        if metadata_text is None:
            continue
        try:
            payload = json.loads(metadata_text)
        except json.JSONDecodeError:
            continue
        if str(payload.get("status", "")).strip().lower() == "blocked":
            return True
    return False


def _build_log_analysis_markdown(
    *,
    category: str,
    reason: str,
    boundary_category: str,
    boundary_signal_source: str,
    boundary_signal_line_number: int | None,
    boundary_reason: str,
) -> str:
    lines = [
        "# Log Analysis",
        "",
        "## Failure taxonomy",
        f"- Category: `{category}`",
        f"- Reason: {reason}",
        "",
        "## First failure boundary",
        f"- Category: `{boundary_category}`",
        f"- Signal source: `{boundary_signal_source}`",
        (
            f"- Signal line: `{boundary_signal_line_number}`"
            if boundary_signal_line_number is not None
            else "- Signal line: `none`"
        ),
        f"- Reason: {boundary_reason}",
        "",
    ]
    return "\n".join(lines)


def _build_verification_summary(
    *,
    verification_result: HarnessVerificationResult | None,
    verification_failed: bool,
    infrastructure_failure: bool,
) -> str:
    if infrastructure_failure:
        return "Verification did not complete due to infrastructure failure."
    if verification_result is None:
        return "Verification did not run."
    if verification_failed:
        return "Verification ran and failed."
    return "Verification commands completed successfully."


def _build_status_summary(
    *,
    scenario_id: str,
    runtime_id: str,
    aidd_exit_code: int | None,
    verification_failed: bool,
    blocked_by_questions: bool,
    infrastructure_failure: bool,
) -> str:
    return (
        f"Scenario `{scenario_id}` on runtime `{runtime_id}` finished. "
        f"aidd_exit_code={aidd_exit_code}, "
        f"verification_failed={verification_failed}, "
        f"blocked_by_questions={blocked_by_questions}, "
        f"infrastructure_failure={infrastructure_failure}."
    )


def _scenario_teardown_commands(scenario: Scenario) -> tuple[str, ...]:
    teardown_payload = scenario.raw.get("teardown")
    if not isinstance(teardown_payload, dict):
        return tuple()
    commands = teardown_payload.get("commands")
    if not isinstance(commands, list):
        return tuple()
    normalized = tuple(str(command).strip() for command in commands if str(command).strip())
    return normalized


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def run_eval_scenario(
    *,
    scenario_path: Path,
    runtime_id: str,
    workspace_root: Path,
    aidd_command: tuple[str, ...] = ("uv", "run", "aidd"),
) -> EvalRunOutcome:
    scenario = load_scenario(
        scenario_path,
        runtime_id=runtime_id,
        workspace_root=workspace_root,
    )
    if runtime_id not in scenario.runtime_targets:
        supported = ", ".join(scenario.runtime_targets)
        raise ValueError(
            f"Runtime '{runtime_id}' is not allowed by scenario '{scenario.scenario_id}'. "
            f"Supported runtime targets: {supported}."
        )

    eval_run_id = _generate_eval_run_id()
    layout = ensure_result_bundle_layout(workspace_root=workspace_root, run_id=eval_run_id)
    cache_root = _scenario_cache_root(workspace_root=workspace_root)
    prepare_workspace(cache_root)

    prepared_repository: PreparedRepository | None = None
    prepared_working_copy: PreparedWorkingCopy | None = None
    setup_result: HarnessSetupResult | None = None
    aidd_run_result: HarnessAiddRunResult | None = None
    verification_result: HarnessVerificationResult | None = None
    teardown_result: HarnessTeardownResult | None = None
    infrastructure_failure = False
    verification_failed = False
    blocked_by_questions = False
    failure_note: str | None = None
    work_item = f"EVAL-{scenario.scenario_id}".replace("/", "-")

    try:
        prepared_repository = prepare_scenario_repository(
            cache_root=cache_root,
            scenario=scenario,
        )
        prepared_working_copy = prepare_working_copy(
            cache_root=cache_root,
            scenario=scenario,
            prepared_repository=prepared_repository,
        )

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
        blocked_by_questions = _detect_blocked_stage(
            workspace_root=prepared_working_copy.working_copy_path / ".aidd",
            work_item=work_item,
        )
        verification_result = run_verification_steps(
            scenario=scenario,
            working_copy_path=prepared_working_copy.working_copy_path,
            aidd_run_result=aidd_run_result,
        )
    except HarnessSetupError as exc:
        infrastructure_failure = True
        failure_note = str(exc)
    except HarnessVerificationError as exc:
        verification_failed = True
        failure_note = str(exc)
    except Exception as exc:  # pragma: no cover - defensive classification boundary.
        infrastructure_failure = True
        failure_note = str(exc)
    finally:
        if prepared_working_copy is not None:
            try:
                teardown_result = run_teardown_steps(
                    teardown_commands=_scenario_teardown_commands(scenario),
                    working_copy_path=prepared_working_copy.working_copy_path,
                )
            except HarnessTeardownError as exc:
                infrastructure_failure = True
                failure_note = (
                    f"{failure_note}\n{exc}" if failure_note is not None else str(exc)
                )

    write_command_transcripts(
        layout=layout,
        setup_result=setup_result,
        aidd_run_result=aidd_run_result,
        verification_result=verification_result,
        teardown_result=teardown_result,
    )

    latest_stage_artifact: _LatestStageArtifact | None = None
    runtime_log_fallback = ""
    validator_fallback = "# Validator Report\n\n- none\n"
    if aidd_run_result is not None:
        runtime_log_fallback = f"{aidd_run_result.stdout_text}{aidd_run_result.stderr_text}"
    if failure_note is not None:
        runtime_log_fallback += f"\n[harness-note] {failure_note}\n"
        validator_fallback = (
            "# Validator Report\n\n"
            "## Summary\n\n"
            "- Total issues: 1\n"
            "- Blocking issues: yes\n\n"
            "## Structural checks\n\n"
            f"- `STRUCT-HARNESS-FAIL` (`critical`) in `harness`: {failure_note}\n\n"
            "## Semantic checks\n\n- none\n\n"
            "## Cross-document checks\n\n- none\n\n"
            "## Result\n\n- Verdict: `fail`\n"
        )

    if prepared_working_copy is not None:
        latest_stage_artifact = _find_latest_stage_artifact(
            workspace_root=prepared_working_copy.working_copy_path / ".aidd",
            work_item=work_item,
        )

    _copy_optional_file(
        source=(latest_stage_artifact.runtime_log_path if latest_stage_artifact else None),
        destination=layout.runtime_log_path,
        fallback=runtime_log_fallback,
    )
    _copy_optional_file(
        source=(latest_stage_artifact.validator_report_path if latest_stage_artifact else None),
        destination=layout.validator_report_path,
        fallback=validator_fallback,
    )
    if latest_stage_artifact is not None:
        _copy_optional_file(
            source=latest_stage_artifact.events_jsonl_path,
            destination=layout.events_jsonl_path,
            fallback="",
        )

    runtime_events = parse_runtime_log_text(layout.runtime_log_path.read_text(encoding="utf-8"))
    normalized_events = (
        parse_events_jsonl(layout.events_jsonl_path)
        if layout.events_jsonl_path.exists()
        else tuple()
    )
    validator_failures = (
        parse_validator_report_failures(layout.validator_report_path)
        if layout.validator_report_path.exists()
        else tuple()
    )
    stage_metadata_failures = (
        parse_stage_metadata_validation_failures(latest_stage_artifact.stage_metadata_path)
        if latest_stage_artifact is not None and latest_stage_artifact.stage_metadata_path.exists()
        else tuple()
    )
    taxonomy = classify_failure_taxonomy(
        runtime_events=runtime_events,
        normalized_events=normalized_events,
        validator_failures=validator_failures,
        stage_metadata_failures=stage_metadata_failures,
        aidd_exit_code=(aidd_run_result.exit_code if aidd_run_result is not None else None),
        verification_exit_code=(
            verification_result.command_transcripts[-1].exit_code
            if verification_result is not None and verification_result.command_transcripts
            else None
        ),
    )
    first_boundary = select_first_failure_boundary(
        runtime_events=runtime_events,
        normalized_events=normalized_events,
        validator_failures=validator_failures,
        stage_metadata_failures=stage_metadata_failures,
        aidd_exit_code=(aidd_run_result.exit_code if aidd_run_result is not None else None),
        verification_exit_code=(
            verification_result.command_transcripts[-1].exit_code
            if verification_result is not None and verification_result.command_transcripts
            else None
        ),
    )
    layout.log_analysis_path.write_text(
        _build_log_analysis_markdown(
            category=taxonomy.category,
            reason=taxonomy.reason,
            boundary_category=first_boundary.category,
            boundary_signal_source=first_boundary.signal_source,
            boundary_signal_line_number=first_boundary.signal_line_number,
            boundary_reason=first_boundary.reason,
        ),
        encoding="utf-8",
    )

    outcome = HarnessOutcome(
        aidd_exit_code=aidd_run_result.exit_code if aidd_run_result is not None else None,
        verification_failed=verification_failed,
        blocked_by_questions=blocked_by_questions,
        infrastructure_failure=infrastructure_failure,
    )
    status_summary = _build_status_summary(
        scenario_id=scenario.scenario_id,
        runtime_id=runtime_id,
        aidd_exit_code=outcome.aidd_exit_code,
        verification_failed=verification_failed,
        blocked_by_questions=blocked_by_questions,
        infrastructure_failure=infrastructure_failure,
    )
    verdict = build_scenario_verdict_from_harness_outcome(
        scenario_id=scenario.scenario_id,
        run_id=eval_run_id,
        runtime_id=runtime_id,
        outcome=outcome,
        summary=status_summary,
        artifact_links=(
            _workspace_relative(layout.runtime_log_path, workspace_root),
            _workspace_relative(layout.validator_report_path, workspace_root),
            _workspace_relative(layout.log_analysis_path, workspace_root),
        ),
        first_failure_note=first_boundary.reason,
        verification_summary=_build_verification_summary(
            verification_result=verification_result,
            verification_failed=verification_failed,
            infrastructure_failure=infrastructure_failure,
        ),
    )
    write_scenario_verdict_markdown(path=layout.verdict_path, verdict=verdict)
    write_grader_payload(
        path=layout.grader_path,
        payload=build_eval_grader_payload(
            run_id=eval_run_id,
            scenario_id=scenario.scenario_id,
            runtime_id=runtime_id,
            verdict_status=verdict.status,
            validator_failure_count=len(validator_failures),
            aidd_exit_code=outcome.aidd_exit_code,
            verification_failed=verification_failed,
            blocked_by_questions=blocked_by_questions,
            infrastructure_failure=infrastructure_failure,
            failure_taxonomy_category=taxonomy.category,
            failure_taxonomy_reason=taxonomy.reason,
            first_failure_category=first_boundary.category,
            first_failure_signal_source=first_boundary.signal_source,
            first_failure_signal_line_number=first_boundary.signal_line_number,
            first_failure_reason=first_boundary.reason,
        ),
    )

    scenario_row = build_scenario_summary_row(
        verdict=verdict,
        duration_seconds=(
            aidd_run_result.duration_seconds if aidd_run_result is not None else 0.0
        ),
        failure_boundary=first_boundary.category,
    )
    runtime_rows = aggregate_runtime_summary_rows((scenario_row,))
    summary_path = layout.run_root / "summary.md"
    write_eval_summary_markdown(
        path=summary_path,
        scenario_rows=(scenario_row,),
        runtime_summaries=runtime_rows,
    )

    artifact_references = {
        "runtime_log": _workspace_relative(layout.runtime_log_path, workspace_root),
        "validator_report": _workspace_relative(layout.validator_report_path, workspace_root),
        "log_analysis": _workspace_relative(layout.log_analysis_path, workspace_root),
        "verdict": _workspace_relative(layout.verdict_path, workspace_root),
        "summary": _workspace_relative(summary_path, workspace_root),
    }
    write_harness_metadata(
        layout=layout,
        scenario=scenario,
        runtime_id=runtime_id,
        work_item=work_item,
        status=verdict.status,
        aidd_run_id=(latest_stage_artifact.run_id if latest_stage_artifact else None),
        aidd_run_result=aidd_run_result,
        aidd_artifact_references=artifact_references,
        scenario_manifest_path=scenario_path.resolve(strict=False).as_posix(),
        scenario_manifest_sha256=_sha256_file(scenario_path),
        execution_pin={
            "repo_url": scenario.repo.url,
            "default_branch": scenario.repo.default_branch,
            "requested_revision": scenario.repo.revision,
            "prepared_repository_revision": (
                prepared_repository.resolved_revision if prepared_repository is not None else None
            ),
            "working_copy_revision": (
                prepared_working_copy.resolved_revision
                if prepared_working_copy is not None
                else None
            ),
        },
    )

    return EvalRunOutcome(
        eval_run_id=eval_run_id,
        scenario_id=scenario.scenario_id,
        runtime_id=runtime_id,
        verdict_status=verdict.status,
        summary_path=summary_path,
        verdict_path=layout.verdict_path,
        bundle_root=layout.run_root,
        aidd_exit_code=outcome.aidd_exit_code,
        failure_boundary=first_boundary.category,
    )

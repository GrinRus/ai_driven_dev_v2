from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from aidd.core.markdown import MarkdownSectionIndex
from aidd.core.next_flow import (
    FollowUpDraftRequest,
    FollowUpSourceSelection,
    create_follow_up_work_item_draft,
)
from aidd.core.operator_frontend import resolve_operator_dashboard_view
from aidd.core.run_store import (
    load_stage_metadata,
    persist_stage_status,
    run_stage_metadata_path,
)
from aidd.core.runtime_operator import (
    OPERATOR_DECISIONS_FILENAME,
    OPERATOR_REQUESTS_FILENAME,
    RuntimeOperatorRequest,
)
from aidd.core.stages import STAGES
from aidd.evals.reporting import build_scenario_summary_row, write_eval_summary_markdown
from aidd.evals.repository_changes import (
    LIVE_KNOWN_HARNESS_UNTRACKED_FILES,
    LiveWorkspaceSnapshot,
    classify_live_workspace_changes,
    collect_live_workspace_snapshot,
    collect_repository_changes,
    live_workspace_snapshot_from_payload,
)
from aidd.evals.stage_timing import (
    build_stage_timing_payload,
    render_repair_history_markdown,
    write_stage_timing_artifacts,
)
from aidd.evals.verdicts import (
    HarnessOutcome,
    VerdictStatus,
    build_scenario_verdict_from_harness_outcome,
    write_scenario_verdict_markdown,
)
from aidd.harness.eval_preparation import (
    build_feature_selection_payload,
    derive_run_id,
    derive_source_repository_root,
    derive_teardown_commands,
    derive_work_item,
    select_authored_task,
)
from aidd.harness.install_artifact import (
    HarnessInstallError,
    HarnessInstallResult,
    prepare_local_wheel_install,
)
from aidd.harness.live_runtime_config import (
    validate_live_runtime_command,
    write_live_runtime_config,
)
from aidd.harness.live_workspace_bootstrap import bootstrap_live_work_item
from aidd.harness.repo_prep import (
    PreparedRepository,
    PreparedWorkingCopy,
    prepare_live_target_repository,
)
from aidd.harness.result_bundle import (
    EVENTS_JSONL_FILENAME,
    FEATURE_SELECTION_FILENAME,
    GRADER_FILENAME,
    HARNESS_METADATA_FILENAME,
    INSTALL_TRANSCRIPT_FILENAME,
    LOG_ANALYSIS_FILENAME,
    REPAIR_HISTORY_FILENAME,
    RUNTIME_JSONL_FILENAME,
    RUNTIME_LOG_FILENAME,
    SETUP_TRANSCRIPT_FILENAME,
    STAGE_TIMING_JSON_FILENAME,
    STAGE_TIMING_MARKDOWN_FILENAME,
    TEARDOWN_TRANSCRIPT_FILENAME,
    VALIDATOR_REPORT_FILENAME,
    VERDICT_FILENAME,
    VERIFY_TRANSCRIPT_FILENAME,
    build_result_bundle_layout_at_run_root,
    ensure_result_bundle_layout_at_report_root,
    write_feature_selection,
)
from aidd.harness.runner import (
    HarnessAiddRunResult,
    HarnessCommandTranscript,
    HarnessSetupError,
    HarnessSetupResult,
    HarnessTeardownError,
    HarnessTeardownResult,
    HarnessVerificationError,
    HarnessVerificationResult,
    run_setup_steps,
    run_teardown_steps,
    run_verification_steps,
)
from aidd.harness.scenarios import Scenario, ScenarioAuthoredTask, load_scenario
from aidd.validators.semantic_rules.blocks import extract_implementation_verification_blocks
from aidd.validators.semantic_rules.evidence import (
    IMPLEMENT_ARTIFACT_REFERENCE_PATTERN,
    IMPLEMENT_RESULT_PATTERN,
    has_implementation_command_evidence,
    is_deferred_implementation_verification,
)

FlowAction = Literal[
    "install",
    "setup",
    "run-stage",
    "inspect-stage",
    "answer-questions",
    "quality-review",
    "frontend-checkpoint",
    "verify",
    "teardown",
    "finish",
    "stop",
]
LiveE2EStatus = Literal[
    "pass",
    "fail",
    "blocked",
    "infra-fail",
    "awaiting-quality-review",
    "manual-quality-stop",
]
StepClassification = Literal[
    "pass",
    "fail",
    "blocked",
    "infra-fail",
    "skipped",
    "awaiting-quality-review",
    "manual-quality-stop",
]

FLOW_STATE_FILENAME = "flow-state.json"
FLOW_STEPS_FILENAME = "flow-steps.json"
FLOW_REPORT_FILENAME = "flow-report.md"
OPERATOR_ACTIONS_FILENAME = "operator-actions.jsonl"
OPERATOR_REQUEST_JSON_FILENAME = "operator-action-request.json"
OPERATOR_REQUEST_MARKDOWN_FILENAME = "operator-action-request.md"
ANSWER_ANALYSIS_FILENAME = "answer-analysis.md"
RUNTIME_APPROVAL_ANALYSIS_FILENAME = "runtime-approval-analysis.md"
FRONTEND_CHECKPOINTS_JSON_FILENAME = "frontend-checkpoints.json"
FRONTEND_CHECKPOINTS_MARKDOWN_FILENAME = "frontend-checkpoints.md"
NEXT_FLOW_CHECKPOINT_JSON_FILENAME = "next-flow-checkpoint.json"
NEXT_FLOW_CHECKPOINT_MARKDOWN_FILENAME = "next-flow-checkpoint.md"
NEXT_FLOW_LINEAGE_FILENAME = "next-flow-lineage.json"
TARGET_WORKSPACE_EVIDENCE_JSON_FILENAME = "target-workspace-evidence.json"
TARGET_WORKSPACE_EVIDENCE_MARKDOWN_FILENAME = "target-workspace-evidence.md"
VERIFY_WORKSPACE_CLEANUP_SCOPE = "post-verify-known-ignored-residue"
VERIFY_RESIDUE_TOP_LEVEL_DIRS = frozenset(
    {
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "build",
        "coverage",
        "dist",
    }
)
VERIFY_RESIDUE_ANY_LEVEL_DIRS = frozenset({"__pycache__"})
VERIFY_RESIDUE_TOP_LEVEL_FILE_PREFIXES = (".coverage",)
BASELINE_CONTEXT_PATH_SAMPLE_LIMIT = 25
WORKSPACE_EVIDENCE_MARKDOWN_PATH_SAMPLE_LIMIT = 100
RUN_TRANSCRIPT_FILENAME = "run-transcript.json"
SUMMARY_REPORT_FILENAME = "summary.md"
STAGE_AUDITS_DIRNAME = "stage-audits"
STAGE_QUALITY_AUDITS_DIRNAME = "stage-quality-audits"
FLOW_QUALITY_REPORT_FILENAME = "flow-quality-report.md"
CODE_QUALITY_REPORT_FILENAME = "code-quality-report.md"
QUALITY_REPORT_FILENAME = "quality-report.md"
FRONTEND_CHECKPOINT_TIMEOUT_SECONDS = 10.0
STAGE_TIMEOUT_RECONCILIATION_SUFFIX = "-timeout-reconciliation.json"
NEXT_FLOW_OPERATOR_DECISIONS = (
    "no-follow-up",
    "follow-up-draft",
    "clone-draft",
    "eval-batch",
    "archive",
    "blocked",
)

TERMINAL_STATUSES = {"pass", "fail", "infra-fail"}
TERMINAL_MANUAL_STATUSES = {"manual-quality-stop"}
RESUMABLE_STATUSES = {"blocked", "interrupted-resumable", "awaiting-quality-review"}
TERMINAL_STAGE_METADATA_STATUSES = {"blocked", "failed", "succeeded"}
PRESERVED_STATE_EXTRA_KEYS = (
    "error",
    "interruption",
    "operator_action_request_json",
    "operator_action_request_markdown",
    "stage_exit_code",
)


@dataclass(frozen=True, slots=True)
class BlackBoxCommandResult:
    command: tuple[str, ...]
    transcript: HarnessCommandTranscript

    @property
    def exit_code(self) -> int:
        return self.transcript.exit_code

    @property
    def stdout_text(self) -> str:
        return self.transcript.stdout_text

    @property
    def stderr_text(self) -> str:
        return self.transcript.stderr_text

    @property
    def duration_seconds(self) -> float:
        return self.transcript.duration_seconds


@dataclass(frozen=True, slots=True)
class BlackBoxLiveE2EResult:
    scenario_id: str
    run_id: str
    runtime_id: str
    status: LiveE2EStatus
    bundle_root: Path
    flow_report_path: Path
    verdict_path: Path
    summary_path: Path
    first_failure_note: str | None
    operator_action_request_path: Path | None
    quality_review_request_path: Path | None = None


@dataclass(slots=True)
class FlowContext:
    scenario_path: Path
    scenario: Scenario
    run_id: str
    runtime_id: str
    # Internal name kept close to older harness code: this is the temp execution work root.
    workspace_root: Path
    report_root: Path
    bundle_root: Path
    work_item: str
    selected_task_payload: dict[str, object]
    teardown_commands: tuple[str, ...]
    source_repository_root: Path | None
    prepared_repository: PreparedRepository | None
    prepared_working_copy: PreparedWorkingCopy | None
    install_result: HarnessInstallResult | None
    preserved_install_payload: dict[str, object] | None
    config_path: Path | None
    installed_command: tuple[str, ...]
    target_workspace_baseline_snapshot: dict[str, object] | None
    started: float
    enable_next_flow_follow_up_proof: bool = False


class LiveE2EInterrupted(Exception):
    def __init__(
        self,
        message: str,
        *,
        signum: int | None = None,
        command_result: BlackBoxCommandResult | None = None,
        cleanup: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.signum = signum
        self.command_result = command_result
        self.cleanup = cleanup or {}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_work_root() -> Path:
    return Path(tempfile.gettempdir()) / "aidd-live-e2e"


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)
    return path


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path.as_posix()}.")
    return payload


def _read_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    objects: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            objects.append(payload)
    return objects


def _command_transcript_payload(transcript: HarnessCommandTranscript) -> dict[str, object]:
    return {
        "command": transcript.command,
        "duration_seconds": transcript.duration_seconds,
        "exit_code": transcript.exit_code,
        "stderr_text": transcript.stderr_text,
        "stdout_text": transcript.stdout_text,
        "timed_out": transcript.timed_out,
        "timeout_seconds": transcript.timeout_seconds,
    }


def _transcript_duration(transcripts: tuple[HarnessCommandTranscript, ...]) -> float:
    return sum(transcript.duration_seconds for transcript in transcripts)


def _write_step_transcript(
    *,
    path: Path,
    step: str,
    transcripts: tuple[HarnessCommandTranscript, ...],
    extra: dict[str, object] | None = None,
) -> Path:
    payload: dict[str, object] = {
        "command_count": len(transcripts),
        "commands": [_command_transcript_payload(transcript) for transcript in transcripts],
        "duration_seconds": _transcript_duration(transcripts),
        "step": step,
    }
    if extra:
        payload.update(extra)
    return _write_json(path, payload)


def _state_path(bundle_root: Path) -> Path:
    return bundle_root / FLOW_STATE_FILENAME


def _steps_path(bundle_root: Path) -> Path:
    return bundle_root / FLOW_STEPS_FILENAME


def _operator_actions_path(bundle_root: Path) -> Path:
    return bundle_root / OPERATOR_ACTIONS_FILENAME


def _load_steps(bundle_root: Path) -> list[dict[str, Any]]:
    path = _steps_path(bundle_root)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected JSON list in {path.as_posix()}.")
    return [item for item in payload if isinstance(item, dict)]


def _write_steps(bundle_root: Path, steps: list[dict[str, Any]]) -> None:
    _write_json(_steps_path(bundle_root), steps)


def _append_operator_action(
    *,
    bundle_root: Path,
    payload: dict[str, object],
) -> None:
    event = {"timestamp_utc": _utc_now(), **payload}
    path = _operator_actions_path(bundle_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")


def _command_text(command: Sequence[str]) -> str:
    return " ".join(command)


def _run_black_box_command(
    *,
    command: tuple[str, ...],
    cwd: Path,
    environment: dict[str, str],
    timeout_seconds: float | None,
) -> BlackBoxCommandResult:
    started = time.monotonic()
    timed_out = False
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout_text, stderr_text = process.communicate(timeout=timeout_seconds)
        exit_code = process.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout_text = _timeout_output_to_text(exc.stdout)
        stderr_text = _timeout_output_to_text(exc.stderr)
        cleanup = _terminate_process_group(process)
        if cleanup["stdout_text"]:
            stdout_text = str(cleanup["stdout_text"])
        if cleanup["stderr_text"]:
            stderr_text = str(cleanup["stderr_text"])
        timeout_label = (
            f"{timeout_seconds:.3f}s" if timeout_seconds is not None else "configured timeout"
        )
        stderr_text = (
            f"{stderr_text.rstrip()}\nCommand timed out after {timeout_label}.\n"
        ).lstrip()
    except LiveE2EInterrupted as exc:
        cleanup = _terminate_process_group(process)
        duration_seconds = time.monotonic() - started
        stdout_text = str(cleanup.get("stdout_text") or "")
        stderr_text = str(cleanup.get("stderr_text") or "")
        transcript = HarnessCommandTranscript(
            command=_command_text(command),
            exit_code=130,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            duration_seconds=duration_seconds,
            timed_out=False,
            timeout_seconds=timeout_seconds,
        )
        exc.command_result = BlackBoxCommandResult(command=command, transcript=transcript)
        exc.cleanup = {
            "command": list(command),
            "process_exit_code": cleanup.get("return_code"),
            "terminated_process_group": cleanup.get("terminated_process_group"),
            "signal": exc.signum,
        }
        raise
    except KeyboardInterrupt as exc:
        cleanup = _terminate_process_group(process)
        duration_seconds = time.monotonic() - started
        transcript = HarnessCommandTranscript(
            command=_command_text(command),
            exit_code=130,
            stdout_text=str(cleanup.get("stdout_text") or ""),
            stderr_text=str(cleanup.get("stderr_text") or ""),
            duration_seconds=duration_seconds,
            timed_out=False,
            timeout_seconds=timeout_seconds,
        )
        raise LiveE2EInterrupted(
            "Black-box live E2E interrupted by operator.",
            command_result=BlackBoxCommandResult(command=command, transcript=transcript),
            cleanup={
                "command": list(command),
                "process_exit_code": cleanup.get("return_code"),
                "terminated_process_group": cleanup.get("terminated_process_group"),
                "signal": None,
            },
        ) from exc
    except OSError as exc:
        exit_code = 127
        stdout_text = ""
        stderr_text = f"Failed to execute command: {exc}\n"
    duration_seconds = time.monotonic() - started
    transcript = HarnessCommandTranscript(
        command=_command_text(command),
        exit_code=exit_code,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        duration_seconds=duration_seconds,
        timed_out=timed_out,
        timeout_seconds=timeout_seconds,
    )
    return BlackBoxCommandResult(command=command, transcript=transcript)


def _terminate_process_group(
    process: subprocess.Popen[str] | None,
) -> dict[str, object]:
    if process is None:
        return {
            "return_code": None,
            "stdout_text": "",
            "stderr_text": "",
            "terminated_process_group": False,
        }
    terminated_process_group = False
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            terminated_process_group = True
        except ProcessLookupError:
            pass
        except OSError:
            process.terminate()
    try:
        stdout_text, stderr_text = process.communicate(timeout=2.0)
    except subprocess.TimeoutExpired:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
                terminated_process_group = True
            except ProcessLookupError:
                pass
            except OSError:
                process.kill()
        stdout_text, stderr_text = process.communicate(timeout=2.0)
    return {
        "return_code": process.returncode,
        "stdout_text": stdout_text,
        "stderr_text": stderr_text,
        "terminated_process_group": terminated_process_group,
    }


def _terminate_process(process: subprocess.Popen[str]) -> tuple[str, str, int | None]:
    cleanup = _terminate_process_group(process)
    return_code = cleanup.get("return_code")
    return (
        str(cleanup.get("stdout_text") or ""),
        str(cleanup.get("stderr_text") or ""),
        return_code if isinstance(return_code, int) else None,
    )


def _timeout_output_to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _stage_command_timeout_seconds(scenario: Scenario) -> float | None:
    if scenario.run.timeout_minutes is None:
        return None
    return float(scenario.run.timeout_minutes * 60)


def _timeout_policy_payload(ctx: FlowContext) -> dict[str, object]:
    return {
        "scope": "per-stage-command",
        "stage_command_timeout_seconds": _stage_command_timeout_seconds(ctx.scenario),
        "global_flow_timeout_seconds": None,
        "runtime_config_source": None if ctx.config_path is None else ctx.config_path.name,
    }


def _format_timeout_budget(value: object) -> str:
    if not isinstance(value, int | float):
        return "none"
    return f"{float(value):.3f}s"


def _runtime_config_timeout_profile(ctx: FlowContext) -> str:
    if ctx.config_path is None or not ctx.config_path.exists():
        return "n/a"
    try:
        payload = tomllib.loads(ctx.config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return "unreadable"
    runtime_payload = payload.get("runtime")
    if not isinstance(runtime_payload, dict):
        return "missing runtime table"
    runtime_key = ctx.runtime_id.replace("-", "_")
    selected_runtime = runtime_payload.get(runtime_key)
    if not isinstance(selected_runtime, dict):
        return f"missing runtime.{runtime_key}"
    default_timeout = _format_timeout_budget(selected_runtime.get("timeout_seconds"))
    raw_stage_timeouts = selected_runtime.get("stage_timeouts")
    stage_timeouts = raw_stage_timeouts if isinstance(raw_stage_timeouts, dict) else {}
    stage_summary = ", ".join(
        f"{stage}={_format_timeout_budget(stage_timeouts.get(stage))}"
        for stage in STAGES
        if stage in stage_timeouts
    )
    return f"default={default_timeout}; stages={stage_summary or 'none'}"


def _live_workspace_snapshot_payload(
    snapshot: LiveWorkspaceSnapshot,
) -> dict[str, object]:
    payload = snapshot.to_payload()
    payload["captured_at_utc"] = _utc_now()
    return payload


def _capture_target_workspace_baseline(ctx: FlowContext) -> None:
    if ctx.target_workspace_baseline_snapshot is not None:
        _write_target_workspace_baseline_context(ctx)
        return
    if ctx.prepared_working_copy is None:
        return
    snapshot = collect_live_workspace_snapshot(
        ctx.prepared_working_copy.working_copy_path
    )
    ctx.target_workspace_baseline_snapshot = _live_workspace_snapshot_payload(snapshot)
    _write_target_workspace_baseline_context(ctx)


def _baseline_live_workspace_snapshot(ctx: FlowContext) -> LiveWorkspaceSnapshot:
    if ctx.target_workspace_baseline_snapshot is None:
        return LiveWorkspaceSnapshot(
            tracked_files=tuple(),
            untracked_files=tuple(),
            status_short="",
            command_errors=(
                "Target workspace baseline snapshot was not captured before stage execution.",
            ),
        )
    return live_workspace_snapshot_from_payload(ctx.target_workspace_baseline_snapshot)


def _target_workspace_evidence_paths(ctx: FlowContext) -> tuple[Path, Path]:
    return (
        ctx.bundle_root / TARGET_WORKSPACE_EVIDENCE_JSON_FILENAME,
        ctx.bundle_root / TARGET_WORKSPACE_EVIDENCE_MARKDOWN_FILENAME,
    )


def _markdown_path_list(paths: Sequence[str]) -> list[str]:
    if not paths:
        return ["- none"]
    return [f"- `{path}`" for path in paths]


def _path_prefix_counts(paths: Sequence[str]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for path in paths:
        prefix = path.split("/", 1)[0]
        if "/" in path:
            prefix += "/"
        counts[prefix] = counts.get(prefix, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def _markdown_compact_path_summary(
    paths: Sequence[str],
    *,
    sample_limit: int,
    full_list_reference: str,
) -> list[str]:
    if not paths:
        return ["- none"]
    sample = list(paths[:sample_limit])
    omitted_count = max(len(paths) - len(sample), 0)
    lines = [
        f"- Count: `{len(paths)}`",
        f"- Full list: `{full_list_reference}`",
        "- Prefix counts:",
    ]
    for prefix, count in _path_prefix_counts(paths):
        lines.append(f"  - `{prefix}`: `{count}`")
    lines.append("- Sample paths:")
    lines.extend(f"  - `{path}`" for path in sample)
    if omitted_count:
        lines.append(f"- Omitted path count: `{omitted_count}`")
    return lines


def _write_target_workspace_baseline_context(ctx: FlowContext) -> None:
    if ctx.target_workspace_baseline_snapshot is None or ctx.prepared_working_copy is None:
        return
    context_path = (
        ctx.prepared_working_copy.working_copy_path
        / ".aidd"
        / "workitems"
        / ctx.work_item
        / "context"
        / "repository-state.md"
    )
    snapshot = live_workspace_snapshot_from_payload(ctx.target_workspace_baseline_snapshot)
    known_harness_files = tuple(
        path
        for path in LIVE_KNOWN_HARNESS_UNTRACKED_FILES
        if path in snapshot.untracked_files
    )
    known_harness_file_set = set(LIVE_KNOWN_HARNESS_UNTRACKED_FILES)
    setup_baseline_non_aidd = tuple(
        path
        for path in snapshot.untracked_files
        if not path.startswith(".aidd/") and path not in known_harness_file_set
    )
    setup_baseline_aidd_count = sum(
        1 for path in snapshot.untracked_files if path.startswith(".aidd/")
    )
    section_lines = [
        "## Live setup workspace baseline",
        "",
        (
            "- Captured after live bootstrap, runtime config generation, and scenario setup "
            "commands, before the first public `aidd stage run`."
        ),
        (
            "- Files listed here are setup-baseline or harness context, not stage-created "
            "deliverable pollution by themselves."
        ),
        (
            "- Review and QA must still inspect tracked product diff plus any new untracked "
            "files that are not listed in this baseline and are not known harness config."
        ),
        "",
        "### Known harness config present",
        "",
        *_markdown_path_list(known_harness_files),
        "",
        "### Setup-baseline untracked non-AIDD files",
        "",
        *_markdown_path_list(setup_baseline_non_aidd),
        "",
        "### Setup-baseline ignored files",
        "",
        *_markdown_compact_path_summary(
            snapshot.ignored_files,
            sample_limit=BASELINE_CONTEXT_PATH_SAMPLE_LIMIT,
            full_list_reference=(
                "`flow-state.json` field "
                "`target_workspace_baseline_snapshot.ignored_files`; final "
                "`target-workspace-evidence.json` after the run"
            ),
        ),
        "",
        "### Setup-baseline AIDD workspace files",
        "",
        f"- Count: `{setup_baseline_aidd_count}`",
        "- Prefix: `.aidd/`",
        "",
        "### Baseline capture errors",
        "",
        *_markdown_path_list(snapshot.command_errors),
        "",
    ]
    existing = (
        context_path.read_text(encoding="utf-8")
        if context_path.exists()
        else "# Repository State\n"
    )
    marker = "\n## Live setup workspace baseline\n"
    base = existing.split(marker, 1)[0].rstrip()
    context_path.parent.mkdir(parents=True, exist_ok=True)
    context_path.write_text(
        base + "\n\n" + "\n".join(section_lines).rstrip() + "\n",
        encoding="utf-8",
    )


def _write_target_workspace_evidence(ctx: FlowContext) -> tuple[Path, ...]:
    json_path, markdown_path = _target_workspace_evidence_paths(ctx)
    if ctx.prepared_working_copy is None:
        return tuple()

    final_snapshot = collect_live_workspace_snapshot(
        ctx.prepared_working_copy.working_copy_path
    )
    baseline_snapshot = _baseline_live_workspace_snapshot(ctx)
    classification = classify_live_workspace_changes(
        baseline_snapshot=baseline_snapshot,
        final_snapshot=final_snapshot,
    )
    baseline_payload = (
        dict(ctx.target_workspace_baseline_snapshot)
        if ctx.target_workspace_baseline_snapshot is not None
        else _live_workspace_snapshot_payload(baseline_snapshot)
    )
    final_payload = _live_workspace_snapshot_payload(final_snapshot)
    payload: dict[str, object] = {
        "schema_version": 1,
        "created_at_utc": _utc_now(),
        "run_id": ctx.run_id,
        "scenario_id": ctx.scenario.scenario_id,
        "runtime_id": ctx.runtime_id,
        "target_repo_root": ctx.prepared_working_copy.working_copy_path.as_posix(),
        "baseline_after_setup": baseline_payload,
        "final_after_flow": final_payload,
        "classification": classification.to_payload(),
        "non_gating_findings": [
            finding.to_payload() for finding in classification.non_gating_findings
        ],
    }
    _write_json(json_path, payload)

    md_lines = [
        "# Target Workspace Evidence",
        "",
        f"- Scenario: `{ctx.scenario.scenario_id}`",
        f"- Runtime: `{ctx.runtime_id}`",
        f"- Run ID: `{ctx.run_id}`",
        f"- Target repo root: `{ctx.prepared_working_copy.working_copy_path.as_posix()}`",
        (
            "- Scope: `non-gating execution evidence for manual quality-report.md "
            "review`"
        ),
        (
            "- Execution verdict impact: `none`; this report does not change "
            "`verdict.md` or `grader.json`."
        ),
        "",
        "## Baseline After Setup",
        "",
        "- Captured at: "
        f"`{baseline_payload.get('captured_at_utc', 'unknown')}`",
        "- Untracked files:",
        *_markdown_path_list(classification.baseline_untracked_files),
        "- Ignored files:",
        *_markdown_compact_path_summary(
            classification.baseline_ignored_files,
            sample_limit=WORKSPACE_EVIDENCE_MARKDOWN_PATH_SAMPLE_LIMIT,
            full_list_reference=(
                "`target-workspace-evidence.json` field "
                "`classification.baseline_ignored_files`"
            ),
        ),
        "",
        "## Final After Flow",
        "",
        "- Captured at: "
        f"`{final_payload.get('captured_at_utc', 'unknown')}`",
        "- Tracked files:",
        *_markdown_path_list(classification.tracked_files),
        "- Known harness files:",
        *_markdown_path_list(classification.known_harness_files),
        "- New untracked files:",
        *_markdown_path_list(classification.new_untracked_files),
        "- New ignored files:",
        *_markdown_compact_path_summary(
            classification.new_ignored_files,
            sample_limit=WORKSPACE_EVIDENCE_MARKDOWN_PATH_SAMPLE_LIMIT,
            full_list_reference=(
                "`target-workspace-evidence.json` field "
                "`classification.new_ignored_files`"
            ),
        ),
        "- Setup-baseline ignored churn files:",
        *_markdown_compact_path_summary(
            classification.setup_baseline_ignored_churn_files,
            sample_limit=WORKSPACE_EVIDENCE_MARKDOWN_PATH_SAMPLE_LIMIT,
            full_list_reference=(
                "`target-workspace-evidence.json` field "
                "`classification.setup_baseline_ignored_churn_files`"
            ),
        ),
        "",
        "## Non-Gating Findings",
        "",
    ]
    if classification.non_gating_findings:
        for finding in classification.non_gating_findings:
            md_lines.append(
                "- "
                f"`{finding.severity}` `{finding.kind}` "
                f"`{finding.path or 'n/a'}`: {finding.message} "
                f"Manual implication: {finding.manual_quality_implication}"
            )
    else:
        md_lines.append("- none")
    md_lines.extend(
        (
            "",
            "## Raw Git Status",
            "",
            "### Baseline",
            "",
            "```text",
            str(baseline_payload.get("status_short") or ""),
            "```",
            "",
            "### Final",
            "",
            "```text",
            final_snapshot.status_short,
            "```",
            "",
        )
    )
    markdown_path.write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")
    return json_path, markdown_path


def _relative_verify_residue_cleanup_root(path: str) -> str | None:
    normalized = Path(path)
    if normalized.is_absolute() or ".." in normalized.parts:
        return None
    parts = normalized.parts
    if not parts:
        return None
    if parts[0] in VERIFY_RESIDUE_TOP_LEVEL_DIRS:
        return parts[0]
    if len(parts) == 1 and parts[0].startswith(VERIFY_RESIDUE_TOP_LEVEL_FILE_PREFIXES):
        return parts[0]
    for index, part in enumerate(parts):
        if part in VERIFY_RESIDUE_ANY_LEVEL_DIRS:
            return Path(*parts[: index + 1]).as_posix()
    return None


def _path_is_under_any_root(path: str, roots: set[str]) -> bool:
    for root in roots:
        if path == root or path.startswith(f"{root}/"):
            return True
    return False


def _verification_workspace_cleanup(
    *,
    repo_root: Path,
    before_verify: LiveWorkspaceSnapshot,
    after_verify: LiveWorkspaceSnapshot,
) -> dict[str, object]:
    before_ignored = set(before_verify.ignored_files)
    baseline_roots = {
        root
        for path in before_verify.ignored_files
        if (root := _relative_verify_residue_cleanup_root(path)) is not None
    }
    cleanup_roots: set[str] = set()
    skipped_paths: list[str] = []
    for path in after_verify.ignored_files:
        if path in before_ignored:
            continue
        root = _relative_verify_residue_cleanup_root(path)
        if root is None:
            continue
        if root in baseline_roots or _path_is_under_any_root(path, baseline_roots):
            skipped_paths.append(path)
            continue
        cleanup_roots.add(root)

    removed_paths: list[str] = []
    errors: list[str] = []
    resolved_repo_root = repo_root.resolve(strict=False)
    for root in sorted(cleanup_roots):
        target = (repo_root / root).resolve(strict=False)
        if not target.is_relative_to(resolved_repo_root):
            errors.append(f"Skipped unsafe verification cleanup path: {root}")
            continue
        try:
            if target.is_dir():
                shutil.rmtree(target)
                removed_paths.append(root)
            elif target.exists():
                target.unlink()
                removed_paths.append(root)
        except OSError as exc:
            errors.append(f"Failed to remove verification residue `{root}`: {exc}")

    after_cleanup = collect_live_workspace_snapshot(repo_root)
    return {
        "scope": VERIFY_WORKSPACE_CLEANUP_SCOPE,
        "execution_verdict_impact": "none",
        "pre_verify_ignored_count": len(before_verify.ignored_files),
        "post_verify_ignored_count": len(after_verify.ignored_files),
        "post_cleanup_ignored_count": len(after_cleanup.ignored_files),
        "removed_paths": removed_paths,
        "skipped_paths": skipped_paths,
        "errors": errors,
    }


def _without_inherited_python_virtualenv(environment: dict[str, str]) -> dict[str, str]:
    cleaned = dict(environment)
    inherited_virtual_env = cleaned.pop("VIRTUAL_ENV", None)

    blocked_path_entries: set[str] = set()
    candidate_roots = [inherited_virtual_env]
    if sys.prefix != sys.base_prefix:
        candidate_roots.append(sys.prefix)

    for root in candidate_roots:
        if not root:
            continue
        blocked_path_entries.add(
            (Path(root) / ("Scripts" if os.name == "nt" else "bin")).resolve(
                strict=False
            ).as_posix()
        )

    path_value = cleaned.get("PATH")
    if path_value and blocked_path_entries:
        cleaned["PATH"] = os.pathsep.join(
            entry
            for entry in path_value.split(os.pathsep)
            if Path(entry).resolve(strict=False).as_posix() not in blocked_path_entries
        )

    return cleaned


def _harness_environment(
    *,
    scenario: Scenario,
    runtime_id: str,
    work_item: str,
    install_result: HarnessInstallResult | None,
) -> dict[str, str]:
    environment = _without_inherited_python_virtualenv(dict(os.environ))
    environment.update(
        {
            "AIDD_HARNESS_SCENARIO_ID": scenario.scenario_id,
            "AIDD_HARNESS_RUNTIME_ID": runtime_id,
            "AIDD_HARNESS_WORK_ITEM": work_item,
        }
    )
    if install_result is not None:
        environment["PATH"] = os.pathsep.join(
            [
                install_result.tool_bin_dir.as_posix(),
                environment.get("PATH", ""),
            ]
        )
    return environment


def _harness_environment_for_context(ctx: FlowContext) -> dict[str, str]:
    environment = _harness_environment(
        scenario=ctx.scenario,
        runtime_id=ctx.runtime_id,
        work_item=ctx.work_item,
        install_result=ctx.install_result,
    )
    if ctx.install_result is not None or ctx.preserved_install_payload is None:
        return environment

    tool_bin_dir = ctx.preserved_install_payload.get("tool_bin_dir")
    if isinstance(tool_bin_dir, str) and tool_bin_dir:
        environment["PATH"] = os.pathsep.join([tool_bin_dir, environment.get("PATH", "")])
    return environment


def _flow_state_payload(
    *,
    ctx: FlowContext,
    status: str,
    next_action: FlowAction,
    current_stage: str | None,
    completed_stages: tuple[str, ...],
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    install_home = None
    if ctx.install_result is not None:
        install_home = ctx.install_result.install_home.as_posix()
    elif ctx.preserved_install_payload is not None:
        preserved_install_home = ctx.preserved_install_payload.get("install_home")
        if isinstance(preserved_install_home, str):
            install_home = preserved_install_home

    payload: dict[str, object] = {
        "schema_version": 1,
        "updated_at_utc": _utc_now(),
        "scenario_path": ctx.scenario_path.resolve(strict=False).as_posix(),
        "scenario_id": ctx.scenario.scenario_id,
        "runtime_id": ctx.runtime_id,
        "run_id": ctx.run_id,
        "work_item": ctx.work_item,
        "status": status,
        "next_action": next_action,
        "current_stage": current_stage,
        "completed_stages": list(completed_stages),
        "evaluator_pid": os.getpid(),
        "bundle_root": ctx.bundle_root.as_posix(),
        "work_root": ctx.workspace_root.as_posix(),
        "run_work_root": (ctx.workspace_root / ctx.run_id).as_posix(),
        "report_root": ctx.report_root.as_posix(),
        "source_snapshot": (
            ctx.install_result.source_snapshot_path.as_posix()
            if ctx.install_result is not None
            and ctx.install_result.source_snapshot_path is not None
            else (
                ctx.preserved_install_payload.get("source_snapshot")
                if ctx.preserved_install_payload is not None
                else None
            )
        ),
        "target_repo_root": (
            None
            if ctx.prepared_working_copy is None
            else ctx.prepared_working_copy.working_copy_path.as_posix()
        ),
        "target_workspace_root": (
            None
            if ctx.prepared_working_copy is None
            else (ctx.prepared_working_copy.working_copy_path / ".aidd").as_posix()
        ),
        "working_copy_path": (
            None
            if ctx.prepared_working_copy is None
            else ctx.prepared_working_copy.working_copy_path.as_posix()
        ),
        "config_path": None if ctx.config_path is None else ctx.config_path.as_posix(),
        "install_home": install_home,
        "installed_command": list(ctx.installed_command),
        "target_workspace_baseline_snapshot": ctx.target_workspace_baseline_snapshot,
        "next_flow_follow_up_proof_enabled": ctx.enable_next_flow_follow_up_proof,
    }
    if ctx.install_result is not None:
        payload["install"] = {
            "artifact_identity": ctx.install_result.artifact_identity,
            "artifact_source": ctx.install_result.artifact_source,
            "install_channel": ctx.install_result.install_channel,
            "install_home": ctx.install_result.install_home.as_posix(),
            "tool_bin_dir": ctx.install_result.tool_bin_dir.as_posix(),
            "uv_cache_dir": (
                None
                if ctx.install_result.uv_cache_dir is None
                else ctx.install_result.uv_cache_dir.as_posix()
            ),
            "source_snapshot": (
                None
                if ctx.install_result.source_snapshot_path is None
                else ctx.install_result.source_snapshot_path.as_posix()
            ),
            "build_dist": (
                None
                if ctx.install_result.build_dist_path is None
                else ctx.install_result.build_dist_path.as_posix()
            ),
            "source_revision": ctx.install_result.source_revision,
        }
    elif ctx.preserved_install_payload is not None:
        payload["install"] = dict(ctx.preserved_install_payload)
    if ctx.prepared_repository is not None:
        payload["prepared_repository"] = {
            "action": ctx.prepared_repository.action,
            "repo_path": ctx.prepared_repository.repo_path.as_posix(),
            "resolved_revision": ctx.prepared_repository.resolved_revision,
        }
    if ctx.prepared_working_copy is not None:
        payload["prepared_working_copy"] = {
            "action": ctx.prepared_working_copy.action,
            "resolved_revision": ctx.prepared_working_copy.resolved_revision,
            "working_copy_path": ctx.prepared_working_copy.working_copy_path.as_posix(),
        }
    if extra:
        payload.update(extra)
    return payload


def _persist_state(
    *,
    ctx: FlowContext,
    status: str,
    next_action: FlowAction,
    current_stage: str | None,
    completed_stages: tuple[str, ...],
    extra: dict[str, object] | None = None,
) -> None:
    payload = _flow_state_payload(
        ctx=ctx,
        status=status,
        next_action=next_action,
        current_stage=current_stage,
        completed_stages=completed_stages,
        extra=extra,
    )
    _write_json(_state_path(ctx.bundle_root), payload)


def _state_completed_stages(bundle_root: Path) -> tuple[str, ...]:
    path = _state_path(bundle_root)
    if not path.exists():
        return tuple()
    payload = _read_json_object(path)
    raw = payload.get("completed_stages")
    if not isinstance(raw, list):
        return tuple()
    return tuple(str(item) for item in raw if isinstance(item, str))


def _state_current_stage(bundle_root: Path) -> str | None:
    path = _state_path(bundle_root)
    if not path.exists():
        return None
    current_stage = _read_json_object(path).get("current_stage")
    return current_stage if isinstance(current_stage, str) and current_stage else None


def _state_status(bundle_root: Path) -> str | None:
    path = _state_path(bundle_root)
    if not path.exists():
        return None
    status = _read_json_object(path).get("status")
    return status if isinstance(status, str) else None


def _preserved_state_extras(ctx: FlowContext) -> dict[str, object]:
    path = _state_path(ctx.bundle_root)
    if not path.exists():
        return {}
    state = _read_json_object(path)
    return {key: state[key] for key in PRESERVED_STATE_EXTRA_KEYS if key in state}


def _record_step(
    *,
    ctx: FlowContext,
    action: FlowAction,
    classification: StepClassification,
    decision: str,
    plan: str,
    stage: str | None = None,
    command_results: tuple[BlackBoxCommandResult, ...] = tuple(),
    evidence_paths: tuple[Path, ...] = tuple(),
    details: dict[str, object] | None = None,
) -> dict[str, Any]:
    steps = _load_steps(ctx.bundle_root)
    started_at = _utc_now()
    duration_seconds = sum(result.duration_seconds for result in command_results)
    step_payload: dict[str, Any] = {
        "step_index": len(steps) + 1,
        "action": action,
        "classification": classification,
        "decision": decision,
        "duration_seconds": duration_seconds,
        "evidence_paths": [path.as_posix() for path in evidence_paths],
        "finished_at_utc": started_at,
        "plan": plan,
        "stage": stage,
        "commands": [
            {
                "command": list(result.command),
                "duration_seconds": result.duration_seconds,
                "exit_code": result.exit_code,
                "stderr_text": result.stderr_text,
                "stdout_text": result.stdout_text,
                "timed_out": result.transcript.timed_out,
                "timeout_seconds": result.transcript.timeout_seconds,
            }
            for result in command_results
        ],
    }
    if details:
        step_payload["details"] = details
    steps.append(step_payload)
    _write_steps(ctx.bundle_root, steps)
    _append_operator_action(
        bundle_root=ctx.bundle_root,
        payload={
            "action": action,
            "classification": classification,
            "decision": decision,
            "stage": stage or "",
            "step_index": len(steps),
        },
    )
    _write_flow_report(ctx)
    return step_payload


def _write_flow_report(ctx: FlowContext) -> Path:
    state = (
        _read_json_object(_state_path(ctx.bundle_root))
        if _state_path(ctx.bundle_root).exists()
        else {}
    )
    steps = _load_steps(ctx.bundle_root)
    lines = [
        "# Black-Box Live E2E Flow Report",
        "",
        "## Run",
        f"- Scenario: `{ctx.scenario.scenario_id}`",
        f"- Runtime: `{ctx.runtime_id}`",
        f"- Run ID: `{ctx.run_id}`",
        f"- Work item: `{ctx.work_item}`",
        f"- Status: `{state.get('status', 'running')}`",
        f"- Next action: `{state.get('next_action', 'unknown')}`",
        "",
        "## Steps",
    ]
    if not steps:
        lines.append("- No steps recorded yet.")
    for step in steps:
        stage = step.get("stage") or "n/a"
        lines.extend(
            (
                "",
                f"### {step.get('step_index', '?')}. {step.get('action', 'unknown')}",
                f"- Stage: `{stage}`",
                f"- Plan: {step.get('plan', '')}",
                f"- Classification: `{step.get('classification', 'unknown')}`",
                f"- Decision: {step.get('decision', '')}",
            )
        )
        raw_commands = step.get("commands")
        commands = raw_commands if isinstance(raw_commands, list) else []
        for command in commands:
            if not isinstance(command, dict):
                continue
            command_text = _command_text(
                tuple(str(item) for item in command.get("command", []))
                if isinstance(command.get("command"), list)
                else tuple()
            )
            lines.append(
                f"- Command: `{command_text}` exit=`{command.get('exit_code', 'n/a')}`"
            )
    report_path = ctx.bundle_root / FLOW_REPORT_FILENAME
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path


def _pid_is_alive(pid: object) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _mark_stale_running_state_interrupted(state_path: Path) -> dict[str, Any]:
    payload = _read_json_object(state_path)
    if payload.get("status") != "running" or _pid_is_alive(payload.get("evaluator_pid")):
        return payload
    interruption = {
        "created_at_utc": _utc_now(),
        "reason": "stale-running-state",
        "previous_status": "running",
        "previous_evaluator_pid": payload.get("evaluator_pid"),
        "cleanup": "no active evaluator process was found",
    }
    payload["status"] = "interrupted-resumable"
    payload["next_action"] = "run-stage"
    payload["updated_at_utc"] = interruption["created_at_utc"]
    payload["interruption"] = interruption
    _write_json(state_path, payload)
    return payload


def _find_resume_state(
    *,
    report_root: Path,
    run_id: str | None,
) -> Path | None:
    normalized_run_id = run_id.strip() if run_id is not None else None
    if normalized_run_id == "":
        raise ValueError("run_id must be non-empty when provided.")
    if normalized_run_id is None:
        return None
    candidate = report_root / normalized_run_id / FLOW_STATE_FILENAME
    if not candidate.exists():
        raise ValueError(
            "Explicit --run-id can only resume or refresh an existing black-box live "
            f"E2E run. State file not found: {candidate.as_posix()}."
        )
    state = _mark_stale_running_state_interrupted(candidate)
    status = state.get("status")
    if status == "awaiting-quality-review":
        required_path = state.get("quality_review_required_path")
        if not isinstance(required_path, str) or not Path(required_path).exists():
            raise ValueError(
                "Run "
                f"'{normalized_run_id}' is awaiting quality review. Resume requires "
                "the launching operator-agent audit file: "
                f"{required_path if isinstance(required_path, str) else 'missing'}."
            )
    if status not in {
        *RESUMABLE_STATUSES,
        *TERMINAL_STATUSES,
        *TERMINAL_MANUAL_STATUSES,
    }:
        raise ValueError(
            "Explicit --run-id can only resume a blocked or interrupted-resumable "
            "run, resume an awaiting-quality-review run with its required audit "
            "file, or refresh terminal execution reporting. "
            f"Run '{normalized_run_id}' has status `{status}`."
        )
    return candidate


def _new_run_id(
    *,
    scenario_id: str,
    runtime_id: str,
    report_root: Path,
    run_id: str | None,
) -> str:
    normalized_run_id = run_id.strip() if run_id is not None else None
    if normalized_run_id == "":
        raise ValueError("run_id must be non-empty when provided.")
    if normalized_run_id is not None:
        return normalized_run_id
    candidate = derive_run_id(scenario_id=scenario_id, runtime_id=runtime_id)
    if not (report_root / candidate).exists():
        return candidate
    suffix = 2
    while (report_root / f"{candidate}-r{suffix}").exists():
        suffix += 1
    return f"{candidate}-r{suffix}"


def _feature_selection_payload(
    *,
    bundle_root: Path,
    scenario: Scenario,
) -> dict[str, object]:
    path = bundle_root / FEATURE_SELECTION_FILENAME
    if path.exists():
        return dict(_read_json_object(path))
    return build_feature_selection_payload(
        scenario=scenario,
        selected_task=select_authored_task(scenario),
    )


def _string_tuple_from_snapshot(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return tuple()
    return tuple(item.strip() for item in raw if isinstance(item, str) and item.strip())


def _selected_task_from_payload(
    payload: dict[str, object],
) -> ScenarioAuthoredTask | None:
    raw = payload.get("selected_task")
    if not isinstance(raw, dict):
        return None

    required_strings = (
        "id",
        "title",
        "summary",
        "intent",
        "target_change",
        "expected_scope",
        "quality_bar",
        "size_rationale",
    )
    strings: dict[str, str] = {}
    for key in required_strings:
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            return None
        strings[key] = value.strip()

    visible_request = raw.get("visible_request")
    audit_rubric = raw.get("audit_rubric")

    return ScenarioAuthoredTask(
        task_id=strings["id"],
        title=strings["title"],
        summary=strings["summary"],
        intent=strings["intent"],
        target_change=strings["target_change"],
        expected_scope=strings["expected_scope"],
        acceptance_criteria=_string_tuple_from_snapshot(raw.get("acceptance_criteria")),
        verification=_string_tuple_from_snapshot(raw.get("verification")),
        quality_bar=strings["quality_bar"],
        size_rationale=strings["size_rationale"],
        interview=_string_tuple_from_snapshot(raw.get("interview")),
        visible_request=(
            visible_request.strip()
            if isinstance(visible_request, str) and visible_request.strip()
            else None
        ),
        audit_rubric=(
            audit_rubric.strip()
            if isinstance(audit_rubric, str) and audit_rubric.strip()
            else None
        ),
        complexity_axes=_string_tuple_from_snapshot(raw.get("complexity_axes")),
    )


def _selected_task_for_context(ctx: FlowContext) -> ScenarioAuthoredTask | None:
    return _selected_task_from_payload(ctx.selected_task_payload) or select_authored_task(
        ctx.scenario
    )


def _initial_context(
    *,
    scenario_path: Path,
    runtime_id: str,
    work_root: Path,
    report_root: Path,
    run_id: str | None,
    enable_next_flow_follow_up_proof: bool,
) -> FlowContext:
    scenario = load_scenario(
        scenario_path,
        runtime_id=runtime_id,
        workspace_root=work_root,
    )
    if not scenario.is_live:
        raise ValueError("Black-box live E2E evaluator only supports live scenarios.")
    if runtime_id not in scenario.runtime_targets:
        supported = ", ".join(scenario.runtime_targets)
        raise ValueError(
            f"Runtime '{runtime_id}' is not allowed by scenario '{scenario.scenario_id}'. "
            f"Supported runtime targets: {supported}."
    )
    selected_task = select_authored_task(scenario)
    if selected_task is None:
        raise ValueError("Live scenario must provide an authored task pool.")
    if enable_next_flow_follow_up_proof and scenario.automation_lane != "manual":
        raise ValueError("Next-flow follow-up proof is manual-only.")
    resolved_run_id = _new_run_id(
        scenario_id=scenario.scenario_id,
        runtime_id=runtime_id,
        report_root=report_root,
        run_id=run_id,
    )
    layout = ensure_result_bundle_layout_at_report_root(
        report_root=report_root,
        run_id=resolved_run_id,
    )
    work_root.mkdir(parents=True, exist_ok=True)
    selected_task_payload = build_feature_selection_payload(
        scenario=scenario,
        selected_task=selected_task,
    )
    write_feature_selection(layout=layout, payload=selected_task_payload)
    return FlowContext(
        scenario_path=scenario_path,
        scenario=scenario,
        run_id=resolved_run_id,
        runtime_id=runtime_id,
        workspace_root=work_root,
        report_root=report_root,
        bundle_root=layout.run_root,
        work_item=derive_work_item(scenario),
        selected_task_payload=selected_task_payload,
        teardown_commands=derive_teardown_commands(scenario),
        source_repository_root=derive_source_repository_root(scenario_path),
        prepared_repository=None,
        prepared_working_copy=None,
        install_result=None,
        preserved_install_payload=None,
        config_path=None,
        installed_command=tuple(),
        target_workspace_baseline_snapshot=None,
        started=time.monotonic(),
        enable_next_flow_follow_up_proof=enable_next_flow_follow_up_proof,
    )


def _context_from_state(
    *,
    state_path: Path,
    scenario_path: Path,
    runtime_id: str,
    work_root: Path,
    report_root: Path,
    enable_next_flow_follow_up_proof: bool,
) -> FlowContext:
    state = _read_json_object(state_path)
    state_work_root = state.get("work_root")
    resolved_work_root = (
        Path(state_work_root)
        if isinstance(state_work_root, str) and state_work_root
        else work_root
    )
    scenario = load_scenario(
        scenario_path,
        runtime_id=runtime_id,
        workspace_root=resolved_work_root,
    )
    run_id = str(state["run_id"])
    layout = build_result_bundle_layout_at_run_root(run_root=state_path.parent)
    selected_task_payload = _feature_selection_payload(
        bundle_root=layout.run_root,
        scenario=scenario,
    )
    working_copy_path = state.get("working_copy_path")
    prepared_working_copy = (
        PreparedWorkingCopy(
            working_copy_path=Path(working_copy_path),
            action="resumed",
            resolved_revision=str(
                cast(dict[str, object], state.get("prepared_working_copy", {})).get(
                    "resolved_revision",
                    "unknown",
                )
            ),
        )
        if isinstance(working_copy_path, str) and working_copy_path
        else None
    )
    repo_payload = state.get("prepared_repository")
    prepared_repository = None
    if isinstance(repo_payload, dict):
        repo_path = repo_payload.get("repo_path")
        if isinstance(repo_path, str) and repo_path:
            prepared_repository = PreparedRepository(
                repo_path=Path(repo_path),
                action="resumed",
                resolved_revision=str(repo_payload.get("resolved_revision", "unknown")),
            )
    config_path = state.get("config_path")
    raw_command = state.get("installed_command")
    installed_command = (
        tuple(str(item) for item in raw_command if isinstance(item, str))
        if isinstance(raw_command, list)
        else tuple()
    )
    install_payload = state.get("install")
    preserved_install_payload = (
        dict(install_payload) if isinstance(install_payload, dict) else None
    )
    state_follow_up_proof = state.get("next_flow_follow_up_proof_enabled") is True
    baseline_snapshot = state.get("target_workspace_baseline_snapshot")
    return FlowContext(
        scenario_path=scenario_path,
        scenario=scenario,
        run_id=run_id,
        runtime_id=runtime_id,
        workspace_root=resolved_work_root,
        report_root=report_root,
        bundle_root=layout.run_root,
        work_item=str(state.get("work_item") or derive_work_item(scenario)),
        selected_task_payload=selected_task_payload,
        teardown_commands=derive_teardown_commands(scenario),
        source_repository_root=derive_source_repository_root(scenario_path),
        prepared_repository=prepared_repository,
        prepared_working_copy=prepared_working_copy,
        install_result=None,
        preserved_install_payload=preserved_install_payload,
        config_path=Path(config_path) if isinstance(config_path, str) and config_path else None,
        installed_command=installed_command,
        target_workspace_baseline_snapshot=(
            dict(baseline_snapshot) if isinstance(baseline_snapshot, dict) else None
        ),
        started=time.monotonic(),
        enable_next_flow_follow_up_proof=(
            enable_next_flow_follow_up_proof or state_follow_up_proof
        ),
    )


def _load_or_create_context(
    *,
    scenario_path: Path,
    runtime_id: str,
    work_root: Path,
    report_root: Path,
    run_id: str | None,
    enable_next_flow_follow_up_proof: bool,
) -> FlowContext:
    resume_state = _find_resume_state(
        report_root=report_root,
        run_id=run_id,
    )
    if resume_state is not None:
        return _context_from_state(
            state_path=resume_state,
            scenario_path=scenario_path,
            runtime_id=runtime_id,
            work_root=work_root,
            report_root=report_root,
            enable_next_flow_follow_up_proof=enable_next_flow_follow_up_proof,
        )
    ctx = _initial_context(
        scenario_path=scenario_path,
        runtime_id=runtime_id,
        work_root=work_root,
        report_root=report_root,
        run_id=None,
        enable_next_flow_follow_up_proof=enable_next_flow_follow_up_proof,
    )
    _persist_state(
        ctx=ctx,
        status="created",
        next_action="install",
        current_stage=ctx.scenario.run.stage_start,
        completed_stages=tuple(),
    )
    _record_step(
        ctx=ctx,
        action="setup",
        classification="pass",
        decision="Initialized evaluator state and selected the first authored task.",
        plan="Create durable black-box flow state before touching the target repository.",
        evidence_paths=(ctx.bundle_root / FEATURE_SELECTION_FILENAME,),
        details={"selected_task": ctx.selected_task_payload.get("selected_task")},
    )
    return ctx


def _stage_scope(scenario: Scenario) -> tuple[str, ...]:
    start = scenario.run.stage_start or STAGES[0]
    end = scenario.run.stage_end or STAGES[-1]
    start_index = STAGES.index(start)
    end_index = STAGES.index(end)
    return STAGES[start_index : end_index + 1]


def _first_incomplete_stage(ctx: FlowContext) -> str | None:
    completed = set(_state_completed_stages(ctx.bundle_root))
    current_stage = _state_current_stage(ctx.bundle_root)
    if current_stage is not None and current_stage not in completed:
        return current_stage
    for stage in _stage_scope(ctx.scenario):
        if stage not in completed:
            return stage
    return None


_QUALITY_REVIEW_DECISION_PATTERN = re.compile(
    r"^\s*-\s*Flow decision:\s*`?(?P<decision>[a-z-]+)`?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_QUALITY_REVIEW_FLOW_DECISIONS = {
    "continue",
    "continue-with-risk",
    "stop-not-counted",
    "operator-intervention",
}


def _requires_stage_quality_audits(ctx: FlowContext) -> bool:
    return ctx.scenario.live_matrix_role == "product-evaluation"


def _stage_quality_audit_path(ctx: FlowContext, stage: str) -> Path:
    return ctx.bundle_root / STAGE_QUALITY_AUDITS_DIRNAME / f"{stage}.md"


def _stage_quality_audit_flow_decision(path: Path) -> str | None:
    if not path.exists():
        return None
    match = _QUALITY_REVIEW_DECISION_PATTERN.search(path.read_text(encoding="utf-8"))
    if match is None:
        return None
    decision = match.group("decision").strip().lower()
    return decision if decision in _QUALITY_REVIEW_FLOW_DECISIONS else None


def _record_awaiting_quality_review(
    *,
    ctx: FlowContext,
    stage: str,
    required_path: Path,
    reason: str,
    decision: str | None = None,
) -> StepClassification:
    required_path.parent.mkdir(parents=True, exist_ok=True)
    _persist_state(
        ctx=ctx,
        status="awaiting-quality-review",
        next_action="quality-review",
        current_stage=stage,
        completed_stages=_state_completed_stages(ctx.bundle_root),
        extra={
            "quality_review_required_stage": stage,
            "quality_review_required_path": required_path.as_posix(),
            "quality_review_reason": reason,
            **({"quality_review_decision": decision} if decision is not None else {}),
        },
    )
    _record_step(
        ctx=ctx,
        action="quality-review",
        classification="awaiting-quality-review",
        decision=(
            "Stop for launching operator-agent product-quality review before "
            "continuing execution."
        ),
        plan=(
            "Write the required stage quality audit, then resume this same run id "
            "if the audit decision allows continuation."
        ),
        stage=stage,
        details={
            "required_audit_path": required_path.as_posix(),
            "reason": reason,
            **({"flow_decision": decision} if decision is not None else {}),
        },
    )
    return "awaiting-quality-review"


def _record_manual_quality_stop(
    *,
    ctx: FlowContext,
    stage: str,
    audit_path: Path,
) -> StepClassification:
    _persist_state(
        ctx=ctx,
        status="manual-quality-stop",
        next_action="stop",
        current_stage=stage,
        completed_stages=_state_completed_stages(ctx.bundle_root),
        extra={
            "quality_review_required_stage": stage,
            "quality_review_required_path": audit_path.as_posix(),
            "quality_review_decision": "stop-not-counted",
            "quality_review_reason": (
                "Launching operator-agent stage audit chose stop-not-counted."
            ),
        },
    )
    _record_step(
        ctx=ctx,
        action="stop",
        classification="manual-quality-stop",
        decision=(
            "Manual stage quality audit requested `stop-not-counted`; stop without "
            "classifying this as provider, infrastructure, or unresolved-question failure."
        ),
        plan="Preserve the run bundle for manual quality reporting and do not run later stages.",
        stage=stage,
        evidence_paths=(audit_path,),
        details={"flow_decision": "stop-not-counted"},
    )
    return "manual-quality-stop"


def _quality_review_gate(ctx: FlowContext) -> StepClassification | None:
    if not _requires_stage_quality_audits(ctx):
        return None
    for stage in _state_completed_stages(ctx.bundle_root):
        required_path = _stage_quality_audit_path(ctx, stage)
        if not required_path.exists():
            return _record_awaiting_quality_review(
                ctx=ctx,
                stage=stage,
                required_path=required_path,
                reason="stage quality audit file is missing",
            )
        decision = _stage_quality_audit_flow_decision(required_path)
        if decision is None:
            return _record_awaiting_quality_review(
                ctx=ctx,
                stage=stage,
                required_path=required_path,
                reason="stage quality audit is missing a valid Flow decision",
            )
        if decision == "stop-not-counted":
            return _record_manual_quality_stop(
                ctx=ctx,
                stage=stage,
                audit_path=required_path,
            )
        if decision == "operator-intervention":
            return _record_awaiting_quality_review(
                ctx=ctx,
                stage=stage,
                required_path=required_path,
                reason="stage quality audit requested operator intervention",
                decision=decision,
            )
    return None


def _manual_quality_artifacts_payload(ctx: FlowContext) -> dict[str, object]:
    required_for_counted_clean = _requires_stage_quality_audits(ctx)
    stage_audits = [
        {
            "stage": stage,
            "path": _stage_quality_audit_path(ctx, stage).as_posix(),
            "exists": _stage_quality_audit_path(ctx, stage).exists(),
        }
        for stage in _stage_scope(ctx.scenario)
    ]
    final_reports = [
        {
            "kind": "flow-quality-report",
            "path": (ctx.bundle_root / FLOW_QUALITY_REPORT_FILENAME).as_posix(),
            "exists": (ctx.bundle_root / FLOW_QUALITY_REPORT_FILENAME).exists(),
        },
        {
            "kind": "code-quality-report",
            "path": (ctx.bundle_root / CODE_QUALITY_REPORT_FILENAME).as_posix(),
            "exists": (ctx.bundle_root / CODE_QUALITY_REPORT_FILENAME).exists(),
        },
        {
            "kind": "quality-report",
            "path": (ctx.bundle_root / QUALITY_REPORT_FILENAME).as_posix(),
            "exists": (ctx.bundle_root / QUALITY_REPORT_FILENAME).exists(),
        },
    ]
    return {
        "required_for_counted_clean": required_for_counted_clean,
        "stage_quality_audits": stage_audits if required_for_counted_clean else [],
        "final_reports": final_reports if required_for_counted_clean else [],
    }


def _quality_review_request_path_from_state(ctx: FlowContext) -> Path | None:
    state_path = _state_path(ctx.bundle_root)
    if not state_path.exists():
        return None
    raw_path = _read_json_object(state_path).get("quality_review_required_path")
    return Path(raw_path) if isinstance(raw_path, str) and raw_path else None


def _require_working_copy(ctx: FlowContext) -> Path:
    if ctx.prepared_working_copy is None:
        raise RuntimeError("Evaluator state is missing the prepared target working copy.")
    if not ctx.prepared_working_copy.working_copy_path.exists():
        raise RuntimeError(
            "Prepared target working copy no longer exists: "
            f"{ctx.prepared_working_copy.working_copy_path.as_posix()}"
        )
    return ctx.prepared_working_copy.working_copy_path


def _require_installed_command(ctx: FlowContext) -> tuple[str, ...]:
    if not ctx.installed_command:
        raise RuntimeError("Evaluator state is missing the installed AIDD command.")
    return ctx.installed_command


def _require_config_path(ctx: FlowContext) -> Path:
    if ctx.config_path is None:
        raise RuntimeError("Evaluator state is missing the target AIDD config path.")
    return ctx.config_path


def _install_failure_classification(error: Exception) -> StepClassification:
    message = str(error).lower()
    if isinstance(error, HarnessInstallError) and (
        "clean tracked source checkout" in message
        or "git checkout" in message
        or "could not locate" in message
    ):
        return "infra-fail"
    return "fail"


def _prepare_target_repository(ctx: FlowContext) -> None:
    if ctx.prepared_working_copy is not None:
        return
    try:
        validate_live_runtime_command(
            runtime_id=ctx.runtime_id,
            scenario=ctx.scenario,
        )
        ctx.prepared_working_copy = prepare_live_target_repository(
            work_root=ctx.workspace_root,
            scenario=ctx.scenario,
            run_id=ctx.run_id,
        )
    except Exception as exc:
        _record_step(
            ctx=ctx,
            action="setup",
            classification="infra-fail",
            decision="Stop before stage execution because target repository setup failed.",
            plan="Prepare the pinned target repository before installing AIDD.",
            details={"error": str(exc)},
        )
        _persist_state(
            ctx=ctx,
            status="infra-fail",
            next_action="stop",
            current_stage=_first_incomplete_stage(ctx),
            completed_stages=_state_completed_stages(ctx.bundle_root),
            extra={"error": str(exc)},
        )
        raise
    _record_step(
        ctx=ctx,
        action="setup",
        classification="pass",
        decision="Continue to install after the pinned target repository is ready.",
        plan="Prepare the pinned target repository before installing AIDD.",
        evidence_paths=(
            ctx.prepared_working_copy.working_copy_path,
        ),
        details={
            "resolved_revision": ctx.prepared_working_copy.resolved_revision,
            "working_copy": ctx.prepared_working_copy.working_copy_path.as_posix(),
        },
    )
    _persist_state(
        ctx=ctx,
        status="running",
        next_action="install",
        current_stage=ctx.scenario.run.stage_start,
        completed_stages=_state_completed_stages(ctx.bundle_root),
    )


def _install_aidd(ctx: FlowContext) -> None:
    if ctx.installed_command:
        return
    try:
        ctx.install_result = prepare_local_wheel_install(
            work_root=ctx.workspace_root,
            run_id=ctx.run_id,
            repository_root=ctx.source_repository_root,
        )
        ctx.installed_command = ctx.install_result.installed_command
        ctx.preserved_install_payload = None
    except Exception as exc:
        classification = _install_failure_classification(exc)
        _record_step(
            ctx=ctx,
            action="install",
            classification=classification,
            decision="Stop before target setup commands because AIDD installation failed.",
            plan="Install the AIDD artifact under test outside the product CLI.",
            details={"error": str(exc)},
        )
        _persist_state(
            ctx=ctx,
            status=classification,
            next_action="stop",
            current_stage=_first_incomplete_stage(ctx),
            completed_stages=_state_completed_stages(ctx.bundle_root),
            extra={"error": str(exc)},
        )
        raise
    _write_step_transcript(
        path=ctx.bundle_root / INSTALL_TRANSCRIPT_FILENAME,
        step="install",
        transcripts=ctx.install_result.command_transcripts,
    )
    _record_step(
        ctx=ctx,
        action="install",
        classification="pass",
        decision="Continue to target setup commands with the installed AIDD CLI.",
        plan="Install the AIDD artifact under test outside the product CLI.",
        evidence_paths=(ctx.bundle_root / INSTALL_TRANSCRIPT_FILENAME,),
        details={
            "artifact_identity": ctx.install_result.artifact_identity,
            "artifact_source": ctx.install_result.artifact_source,
            "installed_command": list(ctx.installed_command),
        },
    )
    _persist_state(
        ctx=ctx,
        status="running",
        next_action="setup",
        current_stage=ctx.scenario.run.stage_start,
        completed_stages=_state_completed_stages(ctx.bundle_root),
    )


def _bootstrap_target_workspace(ctx: FlowContext) -> None:
    if ctx.config_path is not None:
        return
    working_copy = _require_working_copy(ctx)
    selected_task = _selected_task_for_context(ctx)
    if selected_task is None:
        raise RuntimeError("Live scenario selected task is missing.")
    try:
        init_command = (
            *_require_installed_command(ctx),
            "init",
            "--work-item",
            ctx.work_item,
            "--root",
            ".aidd",
        )
        init_result = _run_black_box_command(
            command=init_command,
            cwd=working_copy,
            environment=_harness_environment_for_context(ctx),
            timeout_seconds=60.0,
        )
        if init_result.exit_code != 0:
            raise RuntimeError(
                "Installed `aidd init` failed before scenario context bootstrap: "
                f"{init_result.stderr_text or init_result.stdout_text or 'no command output'}"
            )
        bootstrap_live_work_item(
            working_copy_path=working_copy,
            scenario=ctx.scenario,
            work_item=ctx.work_item,
            selected_task=selected_task,
            resolved_revision=(
                None
                if ctx.prepared_working_copy is None
                else ctx.prepared_working_copy.resolved_revision
            ),
        )
        ctx.config_path = write_live_runtime_config(
            working_copy_path=working_copy,
            runtime_id=ctx.runtime_id,
            scenario=ctx.scenario,
            environment=_harness_environment_for_context(ctx),
        )
    except Exception as exc:
        _record_step(
            ctx=ctx,
            action="setup",
            classification="infra-fail",
            decision="Stop before stage execution because public AIDD bootstrap failed.",
            plan="Run installed `aidd init`, then write operator-provided scenario context.",
            details={"error": str(exc)},
        )
        _persist_state(
            ctx=ctx,
            status="infra-fail",
            next_action="stop",
            current_stage=_first_incomplete_stage(ctx),
            completed_stages=_state_completed_stages(ctx.bundle_root),
            extra={"error": str(exc)},
        )
        raise
    _record_step(
        ctx=ctx,
        action="setup",
        classification="pass",
        decision="Continue to target setup commands after public AIDD bootstrap.",
        plan="Run installed `aidd init`, then write operator-provided scenario context.",
        command_results=(init_result,),
        evidence_paths=(
            ctx.config_path,
            working_copy / ".aidd" / "workitems" / ctx.work_item / "context",
        ),
    )
    _persist_state(
        ctx=ctx,
        status="running",
        next_action="setup",
        current_stage=ctx.scenario.run.stage_start,
        completed_stages=_state_completed_stages(ctx.bundle_root),
    )


def _run_setup(ctx: FlowContext) -> None:
    existing_transcript = ctx.bundle_root / SETUP_TRANSCRIPT_FILENAME
    if existing_transcript.exists():
        try:
            payload = _read_json_object(existing_transcript)
        except (OSError, ValueError, json.JSONDecodeError):
            payload = {}
        if int(payload.get("command_count", 0) or 0) > 0:
            _capture_target_workspace_baseline(ctx)
            return
    working_copy = _require_working_copy(ctx)
    try:
        result = run_setup_steps(
            scenario=ctx.scenario,
            working_copy_path=working_copy,
            environment=_harness_environment_for_context(ctx),
        )
    except HarnessSetupError as exc:
        transcripts = _transcripts_from_error(exc)
        partial_result = HarnessSetupResult(
            executed_commands=tuple(transcript.command for transcript in transcripts),
            command_transcripts=transcripts,
            duration_seconds=_transcript_duration(transcripts),
        )
        _write_step_transcript(
            path=ctx.bundle_root / SETUP_TRANSCRIPT_FILENAME,
            step="setup",
            transcripts=partial_result.command_transcripts,
        )
        _record_step(
            ctx=ctx,
            action="setup",
            classification="infra-fail",
            decision="Stop before stage execution because scenario setup commands failed.",
            plan="Run scenario setup commands in the pinned target repository.",
            evidence_paths=(ctx.bundle_root / SETUP_TRANSCRIPT_FILENAME,),
            details={"error": str(exc)},
        )
        _persist_state(
            ctx=ctx,
            status="infra-fail",
            next_action="stop",
            current_stage=_first_incomplete_stage(ctx),
            completed_stages=_state_completed_stages(ctx.bundle_root),
            extra={"error": str(exc)},
        )
        raise
    _write_step_transcript(
        path=ctx.bundle_root / SETUP_TRANSCRIPT_FILENAME,
        step="setup",
        transcripts=result.command_transcripts,
    )
    _record_step(
        ctx=ctx,
        action="setup",
        classification="pass",
        decision="Continue to the first public stage run.",
        plan="Run scenario setup commands in the pinned target repository.",
        evidence_paths=(ctx.bundle_root / SETUP_TRANSCRIPT_FILENAME,),
    )
    _capture_target_workspace_baseline(ctx)
    _persist_state(
        ctx=ctx,
        status="running",
        next_action="run-stage",
        current_stage=_first_incomplete_stage(ctx),
        completed_stages=_state_completed_stages(ctx.bundle_root),
    )


def _has_action_passed(
    bundle_root: Path,
    action: FlowAction,
    *,
    require_command: bool = False,
) -> bool:
    for step in _load_steps(bundle_root):
        if step.get("action") != action or step.get("classification") != "pass":
            continue
        if require_command:
            commands = step.get("commands")
            if not isinstance(commands, list) or not commands:
                continue
        return True
    return False


def _transcripts_from_error(error: BaseException) -> tuple[HarnessCommandTranscript, ...]:
    raw: object = getattr(error, "command_transcripts", tuple())
    if isinstance(raw, tuple) and all(
        isinstance(item, HarnessCommandTranscript) for item in raw
    ):
        return raw
    return tuple()


def _stage_run_command(ctx: FlowContext, stage: str) -> tuple[str, ...]:
    return (
        *_require_installed_command(ctx),
        "stage",
        "run",
        stage,
        "--work-item",
        ctx.work_item,
        "--runtime",
        ctx.runtime_id,
        "--run-id",
        ctx.run_id,
        "--root",
        ".aidd",
        "--config",
        _require_config_path(ctx).as_posix(),
    )


def _inspection_commands(ctx: FlowContext, stage: str) -> tuple[tuple[str, ...], ...]:
    aidd = _require_installed_command(ctx)
    return (
        (
            *aidd,
            "stage",
            "summary",
            stage,
            "--work-item",
            ctx.work_item,
            "--root",
            ".aidd",
            "--run-id",
            ctx.run_id,
        ),
        (
            *aidd,
            "stage",
            "questions",
            stage,
            "--work-item",
            ctx.work_item,
            "--root",
            ".aidd",
        ),
        (
            *aidd,
            "run",
            "show",
            "--work-item",
            ctx.work_item,
            "--root",
            ".aidd",
            "--run-id",
            ctx.run_id,
        ),
        (
            *aidd,
            "run",
            "logs",
            "--work-item",
            ctx.work_item,
            "--stage",
            stage,
            "--root",
            ".aidd",
            "--run-id",
            ctx.run_id,
            "--tail",
            "--lines",
            "80",
        ),
        (
            *aidd,
            "run",
            "artifacts",
            "--work-item",
            ctx.work_item,
            "--stage",
            stage,
            "--root",
            ".aidd",
            "--run-id",
            ctx.run_id,
        ),
    )


def _classify_stage_run(result: BlackBoxCommandResult) -> StepClassification:
    output = f"{result.stdout_text}\n{result.stderr_text}".lower()
    if (
        "blocking questions are unresolved" in output
        or "action=wait state=blocked" in output
        or "runtime approval is waiting for operator" in output
    ):
        return "blocked"
    if result.exit_code == 0:
        return "pass"
    return "fail"


def _inspection_reports_unresolved_questions(
    results: tuple[BlackBoxCommandResult, ...],
) -> bool:
    for result in results:
        if not any(
            result.command[index : index + 2] == ("stage", "questions")
            for index in range(len(result.command) - 1)
        ):
            continue
        output = f"{result.stdout_text}\n{result.stderr_text}".lower()
        if (
            "blocking questions are unresolved" in output
            or "pending-blocking" in output
            or "action=wait state=blocked" in output
        ):
            return True
    return False


def _frontend_checkpoints_enabled(ctx: FlowContext) -> bool:
    return (
        ctx.scenario.live_flow is not None
        and ctx.scenario.live_flow.frontend_checkpoints is True
    )


def _allocate_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _frontend_checkpoint_command(ctx: FlowContext, port: int) -> tuple[str, ...]:
    return (
        *_require_installed_command(ctx),
        "ui",
        "--work-item",
        ctx.work_item,
        "--root",
        ".aidd",
        "--config",
        _require_config_path(ctx).as_posix(),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    )


def _http_probe(url: str) -> dict[str, object]:
    try:
        with urlopen(url, timeout=2.0) as response:
            body = response.read(1048576).decode("utf-8", errors="replace")
            payload: dict[str, object] = {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "body_preview": body[:1000],
            }
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                payload["json_payload"] = parsed
            return payload
    except HTTPError as exc:
        body = exc.read(1048576).decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "body_preview": body[:1000],
            "error": str(exc),
        }
    except (OSError, URLError) as exc:
        return {"ok": False, "status": None, "body_preview": "", "error": str(exc)}


def _frontend_probe_targets(ctx: FlowContext, stage: str) -> tuple[tuple[str, str], ...]:
    stage_query = urlencode({"stage": stage, "run_id": ctx.run_id})
    run_query = urlencode({"run_id": ctx.run_id})
    return (
        ("page", "/"),
        ("run-api", f"/api/run?{run_query}"),
        ("stage-api", f"/api/stage?{stage_query}"),
        ("questions-api", f"/api/questions?{urlencode({'stage': stage})}"),
        ("logs-api", f"/api/logs?{stage_query}"),
        ("artifacts-api", f"/api/artifacts?{stage_query}"),
    )


def _json_contains_value(value: object, expected: str) -> bool:
    if isinstance(value, str):
        return value == expected or expected in value
    if isinstance(value, dict):
        return any(_json_contains_value(item, expected) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_json_contains_value(item, expected) for item in value)
    return False


def _json_has_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_json_has_key(item, key) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_json_has_key(item, key) for item in value)
    return False


def _frontend_probe_semantic_failure(
    *,
    ctx: FlowContext,
    stage: str,
    name: str,
    probe: dict[str, object],
) -> str | None:
    if probe.get("ok") is not True:
        return "probe returned non-2xx response"
    if name == "page":
        body = str(probe.get("body_preview") or "")
        return None if body.strip() else "UI page body is empty"
    payload = probe.get("json_payload")
    if not isinstance(payload, dict):
        return "API probe did not return a JSON object"
    if name == "run-api":
        if not _json_contains_value(payload, ctx.run_id):
            return "run API response does not include current run_id"
        if not _json_contains_value(payload, ctx.work_item):
            return "run API response does not include current work_item"
        return None
    if name == "stage-api":
        if not _json_contains_value(payload, ctx.run_id):
            return "stage API response does not include current run_id"
        if not _json_contains_value(payload, stage):
            return "stage API response does not include current stage"
        if not any(
            _json_has_key(payload, key)
            for key in ("status", "state", "stage_state", "final_state")
        ):
            return "stage API response does not include stage status/state"
        return None
    if name == "questions-api":
        if not _json_contains_value(payload, stage):
            return "questions API response does not include current stage"
        if not any(_json_has_key(payload, key) for key in ("questions", "items", "state")):
            return "questions API response does not expose question state"
        return None
    if name == "logs-api":
        if not _json_contains_value(payload, stage):
            return "logs API response does not include current stage"
        if not any(_json_has_key(payload, key) for key in ("logs", "chunks", "text", "lines")):
            return "logs API response does not expose log data"
        return None
    if name == "artifacts-api":
        if not _json_contains_value(payload, stage):
            return "artifacts API response does not include current stage"
        primary = _PRIMARY_STAGE_OUTPUTS.get(stage, "")
        if not (
            _json_contains_value(payload, primary)
            or _json_has_key(payload, "artifacts")
            or _json_has_key(payload, "items")
        ):
            return "artifacts API response does not expose artifact list"
    return None


def _read_frontend_checkpoint_payload(ctx: FlowContext) -> dict[str, object]:
    path = ctx.bundle_root / FRONTEND_CHECKPOINTS_JSON_FILENAME
    if not path.exists():
        return {
            "enabled": True,
            "reason": "frontend checkpoints were enabled for this evaluator run",
            "checkpoints": [],
        }
    payload = _read_json_object(path)
    payload["enabled"] = True
    checkpoints = payload.get("checkpoints")
    if not isinstance(checkpoints, list):
        payload["checkpoints"] = []
    return payload


def _write_frontend_checkpoint_markdown(ctx: FlowContext, payload: dict[str, object]) -> Path:
    lines = ["# Frontend Checkpoints", ""]
    checkpoints_raw = payload.get("checkpoints")
    checkpoints = checkpoints_raw if isinstance(checkpoints_raw, list) else []
    if not checkpoints:
        lines.append("- No frontend checkpoints were recorded.")
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, dict):
            continue
        lines.extend(
            (
                f"## {checkpoint.get('stage', 'unknown')}",
                "",
                f"- Classification: `{checkpoint.get('classification', 'unknown')}`",
                f"- Base URL: `{checkpoint.get('base_url', '')}`",
                f"- Process exit: `{checkpoint.get('process_exit_code', 'n/a')}`",
                "",
            )
        )
        probes_raw = checkpoint.get("probes")
        probes = probes_raw if isinstance(probes_raw, list) else []
        for probe in probes:
            if not isinstance(probe, dict):
                continue
            lines.append(
                f"- `{probe.get('name', 'probe')}` {probe.get('path', '')}: "
                f"status=`{probe.get('status', 'n/a')}` ok=`{probe.get('ok', False)}`"
            )
        lines.append("")
    path = ctx.bundle_root / FRONTEND_CHECKPOINTS_MARKDOWN_FILENAME
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _artifact_payload(
    *,
    stage: str,
    key: str,
    kind: str,
    path: Path,
) -> dict[str, object]:
    return {
        "stage": stage,
        "key": key,
        "kind": kind,
        "path": path.as_posix(),
        "byte_size": path.stat().st_size if path.exists() and path.is_file() else None,
        "present": path.exists(),
    }


def _next_flow_dashboard_snapshot(ctx: FlowContext) -> dict[str, object]:
    if ctx.prepared_working_copy is None:
        return {
            "available": False,
            "reason": "target working copy is not available",
        }
    working_copy = ctx.prepared_working_copy.working_copy_path
    try:
        dashboard = resolve_operator_dashboard_view(
            workspace_root=working_copy / ".aidd",
            work_item=ctx.work_item,
            active_stage="qa",
            run_id=ctx.run_id,
            project_root=working_copy,
        )
    except Exception as exc:  # Best-effort evidence; fallback fields remain authoritative.
        return {
            "available": False,
            "reason": str(exc),
        }

    lineage = dashboard.run.lineage
    handoff = dashboard.terminal_handoff
    handoff_payload: dict[str, object] | None = None
    if handoff is not None:
        handoff_payload = {
            "status": handoff.status,
            "final_qa_status": handoff.final_qa_status,
            "qa_stage_state": handoff.qa_stage_state,
            "final_artifacts": [
                {
                    "stage": artifact.stage,
                    "key": artifact.key,
                    "kind": artifact.kind,
                    "path": artifact.path,
                    "byte_size": artifact.byte_size,
                    "updated_at_utc": artifact.updated_at_utc,
                }
                for artifact in handoff.final_artifacts
            ],
            "repair_counts": {
                "attempts": handoff.repair_counts.attempts,
                "succeeded": handoff.repair_counts.succeeded,
                "failed": handoff.repair_counts.failed,
            },
            "approval_counts": {
                "requested": handoff.approval_counts.requested,
                "approved": handoff.approval_counts.approved,
                "denied": handoff.approval_counts.denied,
                "cancelled": handoff.approval_counts.cancelled,
                "pending": handoff.approval_counts.pending,
            },
            "questions_answered_count": handoff.questions_answered_count,
            "questions_total_count": handoff.questions_total_count,
            "recommended_next_flow_actions": [
                {
                    "action": action.action,
                    "label": action.label,
                    "detail": action.detail,
                    "enabled": action.enabled,
                }
                for action in handoff.recommended_next_flow_actions
            ],
        }
    return {
        "available": True,
        "run": {
            "run_id": dashboard.run.run_id,
            "work_item": dashboard.run.work_item,
            "runtime_id": dashboard.run.runtime_id,
            "stage_target": dashboard.run.stage_target,
            "workflow_stage_start": dashboard.run.workflow_stage_start,
            "workflow_stage_end": dashboard.run.workflow_stage_end,
            "archive": {
                "archived": dashboard.run.archive.archived,
                "archived_at_utc": dashboard.run.archive.archived_at_utc,
                "reason": dashboard.run.archive.reason,
                "source": dashboard.run.archive.source,
            },
            "lineage": {
                "source_run_id": lineage.source_run_id,
                "source_work_item_id": lineage.source_work_item_id,
                "baseline_id": lineage.baseline_id,
                "baseline_label": lineage.baseline_label,
                "child_work_item_candidates": [
                    {
                        "work_item_id": candidate.work_item_id,
                        "label": candidate.label,
                        "relationship": candidate.relationship,
                        "source_run_id": candidate.source_run_id,
                    }
                    for candidate in lineage.child_work_item_candidates
                ],
            },
        },
        "terminal_handoff": handoff_payload,
    }


def _qa_stage_audit(ctx: FlowContext) -> dict[str, object] | None:
    for payload in _stage_audit_payloads(ctx):
        if payload.get("stage") == "qa":
            return payload
    return None


_QA_VERDICT_PATTERN = re.compile(
    r"\b(ready-with-risks|not-ready|ready)\b",
    re.IGNORECASE,
)


def _qa_report_path(ctx: FlowContext) -> Path | None:
    if ctx.prepared_working_copy is None:
        return None
    working_copy = ctx.prepared_working_copy.working_copy_path
    candidates = (
        working_copy
        / ".aidd"
        / "workitems"
        / ctx.work_item
        / "stages"
        / "qa"
        / "output"
        / "qa-report.md",
        working_copy
        / ".aidd"
        / "workitems"
        / ctx.work_item
        / "stages"
        / "qa"
        / "qa-report.md",
    )
    return next((path for path in candidates if path.exists()), None)


def _qa_status_from_artifacts(ctx: FlowContext) -> str:
    path = _qa_report_path(ctx)
    if path is None:
        return "missing"
    match = _QA_VERDICT_PATTERN.search(path.read_text(encoding="utf-8", errors="replace"))
    return match.group(1).lower() if match is not None else "unknown"


def _next_flow_final_artifacts(
    *,
    ctx: FlowContext,
    dashboard_snapshot: dict[str, object],
) -> list[dict[str, object]]:
    handoff = dashboard_snapshot.get("terminal_handoff")
    if isinstance(handoff, dict):
        final_artifacts = handoff.get("final_artifacts")
        if isinstance(final_artifacts, list):
            return [item for item in final_artifacts if isinstance(item, dict)]

    artifacts: list[dict[str, object]] = []
    if ctx.prepared_working_copy is not None:
        working_copy = ctx.prepared_working_copy.working_copy_path
        workspace_root = working_copy / ".aidd"
        stage_root = workspace_root / "workitems" / ctx.work_item / "stages" / "qa"
        for key, relative in (
            ("qa_report", Path("output/qa-report.md")),
            ("stage_result", Path("output/stage-result.md")),
            ("validator_report", Path("output/validator-report.md")),
        ):
            output_path = stage_root / relative
            root_path = stage_root / relative.name
            path = output_path if output_path.exists() else root_path
            if path.exists():
                artifacts.append(
                    _artifact_payload(stage="qa", key=key, kind="document", path=path)
                )
    for key, filename in (
        ("flow_report", FLOW_REPORT_FILENAME),
        ("verdict", VERDICT_FILENAME),
        ("grader", GRADER_FILENAME),
    ):
        path = ctx.bundle_root / filename
        if path.exists():
            artifacts.append(
                _artifact_payload(stage="final", key=key, kind="evidence", path=path)
            )
    return artifacts


def _next_flow_follow_up_work_item_id(ctx: FlowContext) -> str:
    suffix = re.sub(r"[^A-Za-z0-9._-]+", "-", ctx.run_id).strip("-")
    return f"{ctx.work_item}-FOLLOW-UP-{suffix or 'live-e2e'}"


def _workspace_relative_artifact_path(*, workspace_root: Path, path: Path) -> str:
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = path.resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_workspace):
        raise ValueError(
            "Next-flow follow-up proof source artifact is outside the target workspace: "
            f"{path.as_posix()}."
        )
    return resolved_path.relative_to(resolved_workspace).as_posix()


def _next_flow_follow_up_source_selection(ctx: FlowContext) -> FollowUpSourceSelection:
    if ctx.prepared_working_copy is None:
        raise RuntimeError("Next-flow follow-up proof requires a prepared target working copy.")
    qa_report_path = _qa_report_path(ctx)
    if qa_report_path is None:
        raise RuntimeError("Next-flow follow-up proof requires a terminal QA report.")
    workspace_root = ctx.prepared_working_copy.working_copy_path / ".aidd"
    return FollowUpSourceSelection(
        kind="qa-finding",
        title="Terminal QA report findings",
        source_path=_workspace_relative_artifact_path(
            workspace_root=workspace_root,
            path=qa_report_path,
        ),
        stage="qa",
        note="Selected by explicit manual live E2E next-flow follow-up proof option.",
    )


def _write_next_flow_lineage_artifact(
    *,
    ctx: FlowContext,
    status: VerdictStatus,
) -> dict[str, object] | None:
    if not ctx.enable_next_flow_follow_up_proof:
        return None
    lineage_path = ctx.bundle_root / NEXT_FLOW_LINEAGE_FILENAME
    if lineage_path.exists():
        return _read_json_object(lineage_path)
    if status != "pass":
        return None
    if ctx.prepared_working_copy is None:
        raise RuntimeError("Next-flow follow-up proof requires a prepared target working copy.")
    if ctx.scenario.automation_lane != "manual":
        raise RuntimeError("Next-flow follow-up proof is manual-only.")

    working_copy = ctx.prepared_working_copy.working_copy_path
    workspace_root = working_copy / ".aidd"
    child_work_item = _next_flow_follow_up_work_item_id(ctx)
    selection = _next_flow_follow_up_source_selection(ctx)
    result = create_follow_up_work_item_draft(
        FollowUpDraftRequest(
            workspace_root=workspace_root,
            source_work_item=ctx.work_item,
            source_run_id=ctx.run_id,
            new_work_item=child_work_item,
            title="Follow-up from live E2E terminal QA findings",
            selections=(selection,),
            project_root=working_copy,
        )
    )
    child_metadata_path = (
        workspace_root / "workitems" / result.work_item / "work-item.json"
    )
    child_metadata = (
        _read_json_object(child_metadata_path) if child_metadata_path.exists() else {}
    )
    lineage_payload: dict[str, object] = {
        "schema_version": 1,
        "created_at_utc": _utc_now(),
        "enabled": True,
        "manual_only": True,
        "launched_child_flow": False,
        "automation_lane": ctx.scenario.automation_lane,
        "source_run_id": ctx.run_id,
        "source_work_item_id": ctx.work_item,
        "child_work_item_id": result.work_item,
        "relationship": "follow-up-draft",
        "follow_up_request_path": result.request_path.as_posix(),
        "source_artifact_paths": list(result.source_artifact_paths),
        "child_work_item_lineage": child_metadata.get("lineage", {}),
        "next_flow_checkpoint": (ctx.bundle_root / NEXT_FLOW_CHECKPOINT_JSON_FILENAME).as_posix(),
        "operator_policy": {
            "second_public_repository_flow_required": False,
            "child_flow_launch": "not-run",
        },
    }
    lineage_payload["lineage_artifact"] = lineage_path.as_posix()
    _write_json(lineage_path, lineage_payload)
    return lineage_payload


def _next_flow_recommendation_payloads(
    *,
    status: VerdictStatus,
    runtime_id: str,
) -> list[dict[str, object]]:
    completed = status == "pass"
    follow_up_detail = (
        "Create a scoped follow-up only when the operator selects new work."
        if completed
        else "Create a scoped follow-up from QA findings, blockers, or manual notes."
    )
    return [
        {
            "action": "create-new-work-item",
            "label": "Create New Work Item",
            "detail": "Start unrelated work without inheriting completed-run context.",
            "enabled": True,
        },
        {
            "action": "start-follow-up-flow",
            "label": "Start Follow-up Flow",
            "detail": follow_up_detail,
            "enabled": True,
        },
        {
            "action": "clone-flow",
            "label": "Clone This Flow",
            "detail": f"Reuse runtime `{runtime_id}` and configuration in a new run identity.",
            "enabled": True,
        },
        {
            "action": "run-eval-batch",
            "label": "Run Eval / Scenario Batch",
            "detail": "Use completed-run evidence for comparison without mutating the source run.",
            "enabled": True,
        },
        {
            "action": "archive-run",
            "label": "Archive Run",
            "detail": "Close the run for navigation while preserving read-only artifacts.",
            "enabled": True,
        },
    ]


def _next_flow_question_counts(ctx: FlowContext) -> dict[str, int]:
    if ctx.prepared_working_copy is None:
        return {"answered": 0, "total": 0}
    workspace_root = ctx.prepared_working_copy.working_copy_path / ".aidd"
    answered = 0
    total = 0
    for stage in STAGES:
        stage_root = workspace_root / "workitems" / ctx.work_item / "stages" / stage
        questions_text = _read_text_if_exists(stage_root / "questions.md")
        answers_text = _read_text_if_exists(stage_root / "answers.md")
        stage_total = len(re.findall(r"(?im)^-\s*Q\d+\b", questions_text))
        stage_answered = len(re.findall(r"(?im)^-\s*Q\d+\s+\[resolved\]", answers_text))
        total += stage_total
        answered += min(stage_answered, stage_total)
    return {"answered": answered, "total": total}


def _next_flow_repair_counts(ctx: FlowContext) -> dict[str, int]:
    attempts = 0
    succeeded = 0
    failed = 0
    if ctx.prepared_working_copy is not None:
        workspace_root = ctx.prepared_working_copy.working_copy_path / ".aidd"
        for stage in STAGES:
            try:
                metadata = load_stage_metadata(
                    workspace_root=workspace_root,
                    work_item=ctx.work_item,
                    run_id=ctx.run_id,
                    stage=stage,
                )
            except (OSError, KeyError, ValueError, json.JSONDecodeError):
                metadata = None
            if metadata is None:
                continue
            for entry in metadata.repair_history:
                if entry.trigger != "repair":
                    continue
                attempts += 1
                outcome = entry.outcome.lower()
                if "fail" in outcome or "block" in outcome:
                    failed += 1
                elif "pass" in outcome or "succeed" in outcome:
                    succeeded += 1
    if attempts:
        return {"attempts": attempts, "succeeded": succeeded, "failed": failed}

    for audit in _stage_audit_payloads(ctx):
        raw_audit_attempts = audit.get("repair_attempts")
        audit_attempts = raw_audit_attempts if isinstance(raw_audit_attempts, int) else 0
        attempts += audit_attempts
        if audit_attempts and audit.get("stage_state") == "passed":
            succeeded += 1
        elif audit_attempts:
            failed += audit_attempts
    return {"attempts": attempts, "succeeded": succeeded, "failed": failed}


def _next_flow_approval_counts(ctx: FlowContext) -> dict[str, int]:
    counts = {"requested": 0, "approved": 0, "denied": 0, "cancelled": 0, "pending": 0}
    if ctx.prepared_working_copy is None:
        return counts
    runs_root = (
        ctx.prepared_working_copy.working_copy_path
        / ".aidd"
        / "reports"
        / "runs"
        / ctx.work_item
        / ctx.run_id
    )
    requests_by_id: dict[str, dict[str, Any]] = {}
    decisions_by_id: dict[str, dict[str, Any]] = {}
    for path in sorted(runs_root.glob("stages/*/attempts/attempt-*/operator-requests.jsonl")):
        for request in _read_jsonl_objects(path):
            request_id = request.get("id")
            if isinstance(request_id, str) and request_id:
                requests_by_id[request_id] = request
    for path in sorted(runs_root.glob("stages/*/attempts/attempt-*/operator-decisions.jsonl")):
        for decision in _read_jsonl_objects(path):
            request_id = decision.get("request_id")
            if isinstance(request_id, str) and request_id:
                decisions_by_id[request_id] = decision
    counts["requested"] = len(requests_by_id)
    for request_id in requests_by_id:
        decision_payload = decisions_by_id.get(request_id)
        if decision_payload is None:
            counts["pending"] += 1
            continue
        action = str(decision_payload.get("action") or "").lower()
        if action in {"allow_once", "allow_for_session", "approve", "approved"}:
            counts["approved"] += 1
        elif action in {"deny", "denied"}:
            counts["denied"] += 1
        elif action in {"cancel", "cancelled"}:
            counts["cancelled"] += 1
        else:
            counts["pending"] += 1
    return counts


def _next_flow_blockers(
    *,
    ctx: FlowContext,
    status: VerdictStatus,
    first_failure_note: str | None,
) -> list[dict[str, object]]:
    blockers: list[dict[str, object]] = []
    if first_failure_note:
        blockers.append(
            {
                "kind": "first-failure",
                "severity": "error",
                "stage": _first_failure_from_steps(ctx, status=status)[0],
                "detail": first_failure_note,
            }
        )
    for audit in _stage_audit_payloads(ctx):
        classifications = audit.get("classifications")
        failed_classifications = (
            [
                f"{key}={value}"
                for key, value in classifications.items()
                if value in {"fail", "blocked", "infra-fail"}
            ]
            if isinstance(classifications, dict)
            else []
        )
        stage_state = str(audit.get("stage_state") or "unknown")
        validator_verdict = str(audit.get("validator_verdict") or "unknown")
        unresolved = audit.get("unresolved_questions") is True
        if (
            stage_state not in {"passed", "unknown"}
            or validator_verdict == "fail"
            or unresolved
            or failed_classifications
        ):
            blockers.append(
                {
                    "kind": "stage-audit",
                    "severity": "error" if stage_state in {"blocked", "failed"} else "warn",
                    "stage": audit.get("stage"),
                    "detail": "; ".join(
                        item
                        for item in (
                            f"stage_state={stage_state}",
                            f"validator={validator_verdict}",
                            "unresolved_questions=true" if unresolved else "",
                            ", ".join(failed_classifications),
                        )
                        if item
                    ),
                    "path": (
                        ctx.bundle_root
                        / STAGE_AUDITS_DIRNAME
                        / f"{audit.get('stage', 'unknown')}.json"
                    ).as_posix(),
                }
            )
    return blockers


def _default_next_flow_decision(
    *,
    status: VerdictStatus,
    blockers: list[dict[str, object]],
) -> tuple[str, str]:
    has_error_blocker = any(blocker.get("severity") == "error" for blocker in blockers)
    if status == "pass" and not has_error_blocker:
        return (
            "no-follow-up",
            "Default manual live E2E policy stops after the terminal checkpoint; "
            "a second public-repository flow is optional and not required.",
        )
    return (
        "blocked",
        "Terminal execution evidence contains failure or blocker signals; "
        "do not launch a child public-repository flow by default.",
    )


def _next_flow_complete_visible(*, status: str, qa_stage_state: str) -> bool:
    return status == "pass" and qa_stage_state.strip().lower() in {
        "passed",
        "succeeded",
    }


def _write_next_flow_checkpoint_artifacts(
    *,
    ctx: FlowContext,
    status: VerdictStatus,
    first_failure_note: str | None,
    next_flow_lineage: dict[str, object] | None = None,
) -> tuple[Path, Path, dict[str, object]]:
    dashboard_snapshot = _next_flow_dashboard_snapshot(ctx)
    qa_audit = _qa_stage_audit(ctx) or {}
    qa_stage_state = str(qa_audit.get("stage_state") or "not-run")
    dashboard_handoff = dashboard_snapshot.get("terminal_handoff")
    if isinstance(dashboard_handoff, dict):
        final_qa_status = str(dashboard_handoff.get("final_qa_status") or "missing")
        qa_stage_state = str(dashboard_handoff.get("qa_stage_state") or qa_stage_state)
        recommendations = dashboard_handoff.get("recommended_next_flow_actions")
        recommended_next_flow_actions = (
            [item for item in recommendations if isinstance(item, dict)]
            if isinstance(recommendations, list)
            else _next_flow_recommendation_payloads(
                status=status,
                runtime_id=ctx.runtime_id,
            )
        )
    else:
        final_qa_status = _qa_status_from_artifacts(ctx)
        recommended_next_flow_actions = _next_flow_recommendation_payloads(
            status=status,
            runtime_id=ctx.runtime_id,
        )

    final_artifacts = _next_flow_final_artifacts(
        ctx=ctx,
        dashboard_snapshot=dashboard_snapshot,
    )
    blockers = _next_flow_blockers(
        ctx=ctx,
        status=status,
        first_failure_note=first_failure_note,
    )
    default_decision, decision_rationale = _default_next_flow_decision(
        status=status,
        blockers=blockers,
    )
    questions = _next_flow_question_counts(ctx)
    repair_counts = _next_flow_repair_counts(ctx)
    approval_counts = _next_flow_approval_counts(ctx)
    state = (
        _read_json_object(_state_path(ctx.bundle_root))
        if _state_path(ctx.bundle_root).exists()
        else {}
    )
    dashboard_run = dashboard_snapshot.get("run")
    dashboard_lineage: dict[str, object] = {}
    if isinstance(dashboard_run, dict):
        raw_dashboard_lineage = dashboard_run.get("lineage")
        if isinstance(raw_dashboard_lineage, dict):
            dashboard_lineage = {
                str(key): value for key, value in raw_dashboard_lineage.items()
            }
    source_artifact_links = [
        path for artifact in final_artifacts if isinstance(path := artifact.get("path"), str)
    ]
    baseline_id = dashboard_lineage.get("baseline_id")
    if not isinstance(baseline_id, str) or not baseline_id:
        baseline_id = ctx.run_id
    baseline_label = dashboard_lineage.get("baseline_label")
    if not isinstance(baseline_label, str) or not baseline_label:
        baseline_label = f"live E2E source run {ctx.run_id}"
    lineage_metadata: dict[str, object] = {
        "present": bool(dashboard_lineage),
        "source": "operator-dashboard" if dashboard_lineage else "evaluator-fallback",
        "source_run_id": ctx.run_id,
        "source_work_item_id": ctx.work_item,
        "baseline_id": baseline_id,
        "baseline_label": baseline_label,
        "child_work_item_id": None,
        "child_flow_enabled": False,
        "child_flow_required": False,
        "lineage_artifact": None,
        "source_artifact_links": source_artifact_links,
    }
    if next_flow_lineage is not None:
        child_work_item = next_flow_lineage.get("child_work_item_id")
        lineage_artifact = next_flow_lineage.get("lineage_artifact")
        lineage_metadata.update(
            {
                "present": True,
                "source": "manual-live-follow-up-proof",
                "child_work_item_id": child_work_item if isinstance(child_work_item, str) else None,
                "child_flow_enabled": True,
                "lineage_artifact": (
                    lineage_artifact if isinstance(lineage_artifact, str) else None
                ),
                "source_artifact_links": next_flow_lineage.get(
                    "source_artifact_paths",
                    source_artifact_links,
                ),
            }
        )
    payload: dict[str, object] = {
        "schema_version": 1,
        "created_at_utc": _utc_now(),
        "run_id": ctx.run_id,
        "runtime_id": ctx.runtime_id,
        "scenario_id": ctx.scenario.scenario_id,
        "work_item": ctx.work_item,
        "terminal_status": status,
        "flow_complete_visible": _next_flow_complete_visible(
            status=status,
            qa_stage_state=qa_stage_state,
        ),
        "source_run_summary": {
            "source_run_id": ctx.run_id,
            "source_work_item_id": ctx.work_item,
            "runtime_id": ctx.runtime_id,
            "scenario_id": ctx.scenario.scenario_id,
            "terminal_stage": "qa",
            "terminal_status": status,
            "completed_stages": list(_state_completed_stages(ctx.bundle_root)),
            "current_stage": state.get("current_stage"),
            "stage_scope": {
                "start": ctx.scenario.run.stage_start,
                "end": ctx.scenario.run.stage_end,
            },
            "qa_stage_state": qa_stage_state,
            "final_qa_status": final_qa_status,
            "final_artifacts": final_artifacts,
            "blockers": blockers,
            "repair_counts": repair_counts,
            "approval_counts": approval_counts,
            "questions": {
                "answered_count": questions["answered"],
                "total_count": questions["total"],
            },
        },
        "next_flow_actions": {
            "allowed_operator_decisions": list(NEXT_FLOW_OPERATOR_DECISIONS),
            "recommended_next_flow_actions": recommended_next_flow_actions,
            "operator_decision": {
                "decision": default_decision,
                "source": "evaluator-default",
                "rationale": decision_rationale,
                "requires_second_public_repository_flow": False,
            },
        },
        "optional_lineage_metadata": lineage_metadata,
        "operator_dashboard_snapshot": dashboard_snapshot,
    }
    json_path = _write_json(ctx.bundle_root / NEXT_FLOW_CHECKPOINT_JSON_FILENAME, payload)
    lines = [
        "# Next-Flow Checkpoint",
        "",
        "## Run",
        "",
        f"- Scenario: `{ctx.scenario.scenario_id}`",
        f"- Runtime: `{ctx.runtime_id}`",
        f"- Source run: `{ctx.run_id}`",
        f"- Work item: `{ctx.work_item}`",
        f"- Terminal status: `{status}`",
        f"- Flow Complete visible: `{payload['flow_complete_visible']}`",
        "",
        "## Source Run Summary",
        "",
        f"- Final QA status: `{final_qa_status}`",
        f"- QA stage state: `{qa_stage_state}`",
        f"- Questions answered: `{questions['answered']}` / `{questions['total']}`",
        (
            f"- Repair counts: attempts=`{repair_counts['attempts']}` "
            f"succeeded=`{repair_counts['succeeded']}` failed=`{repair_counts['failed']}`"
        ),
        (
            f"- Approval counts: requested=`{approval_counts['requested']}` "
            f"approved=`{approval_counts['approved']}` denied=`{approval_counts['denied']}` "
            f"cancelled=`{approval_counts['cancelled']}` pending=`{approval_counts['pending']}`"
        ),
        "",
        "## Operator Decision",
        "",
        f"- Default decision: `{default_decision}`",
        "- Requires second public-repository flow: `false`",
        f"- Rationale: {decision_rationale}",
        "",
        "## Recommended Next Actions",
        "",
    ]
    for action in recommended_next_flow_actions:
        lines.append(
            f"- `{action.get('action', 'unknown')}` enabled=`{action.get('enabled', False)}`: "
            f"{action.get('label', '')}"
        )
    lines.extend(("", "## Blockers", ""))
    if not blockers:
        lines.append("- none")
    for blocker in blockers:
        stage = blocker.get("stage") or "n/a"
        lines.append(
            f"- `{blocker.get('kind', 'blocker')}` severity=`{blocker.get('severity', 'warn')}` "
            f"stage=`{stage}`: {blocker.get('detail', '')}"
        )
    lines.extend(("", "## Source Artifacts", ""))
    if not final_artifacts:
        lines.append("- none")
    for artifact in final_artifacts:
        lines.append(
            f"- `{artifact.get('key', 'artifact')}` {artifact.get('path', '')}"
        )
    lines.extend(
        (
            "",
            "## Optional Lineage Metadata",
            "",
            f"- Child flow enabled: `{lineage_metadata['child_flow_enabled']}`",
            "- Child flow required: `false`",
            f"- Baseline id: `{lineage_metadata['baseline_id']}`",
            "- Lineage artifact: "
            f"`{lineage_metadata['lineage_artifact'] or 'none'}`",
            "- Source artifact links: "
            f"`{len(cast(list[object], lineage_metadata['source_artifact_links']))}`",
        )
    )
    markdown_path = ctx.bundle_root / NEXT_FLOW_CHECKPOINT_MARKDOWN_FILENAME
    markdown_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return json_path, markdown_path, payload


def _append_frontend_checkpoint(
    *,
    ctx: FlowContext,
    checkpoint: dict[str, object],
) -> tuple[Path, Path]:
    payload = _read_frontend_checkpoint_payload(ctx)
    checkpoints = cast(list[object], payload["checkpoints"])
    checkpoints.append(checkpoint)
    json_path = _write_json(ctx.bundle_root / FRONTEND_CHECKPOINTS_JSON_FILENAME, payload)
    markdown_path = _write_frontend_checkpoint_markdown(ctx, payload)
    return json_path, markdown_path


def _run_frontend_checkpoint(ctx: FlowContext, stage: str) -> StepClassification:
    if not _frontend_checkpoints_enabled(ctx):
        return "skipped"
    working_copy = _require_working_copy(ctx)
    port = _allocate_loopback_port()
    base_url = f"http://127.0.0.1:{port}"
    command = _frontend_checkpoint_command(ctx, port)
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            command,
            cwd=working_copy,
            env=_harness_environment_for_context(ctx),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        duration_seconds = time.monotonic() - started
        startup_failure_reason = f"Failed to start UI checkpoint process: {exc}"
        transcript = HarnessCommandTranscript(
            command=_command_text(command),
            exit_code=127,
            stdout_text="",
            stderr_text=f"{startup_failure_reason}\n",
            duration_seconds=duration_seconds,
            timed_out=False,
            timeout_seconds=FRONTEND_CHECKPOINT_TIMEOUT_SECONDS,
        )
        checkpoint = {
            "base_url": base_url,
            "classification": "fail",
            "command": list(command),
            "created_at_utc": _utc_now(),
            "duration_seconds": duration_seconds,
            "failure_reason": startup_failure_reason,
            "process_exit_code": None,
            "probes": [],
            "stage": stage,
        }
        evidence_paths = _append_frontend_checkpoint(ctx=ctx, checkpoint=checkpoint)
        _record_step(
            ctx=ctx,
            action="frontend-checkpoint",
            classification="fail",
            decision=(
                "Stop if the stage otherwise passed because UI/API checkpoint failed."
            ),
            plan="Start `aidd ui` on loopback and inspect public operator UI/API endpoints.",
            stage=stage,
            command_results=(
                BlackBoxCommandResult(command=command, transcript=transcript),
            ),
            evidence_paths=evidence_paths,
            details={"failure_reason": startup_failure_reason},
        )
        return "fail"
    probes: list[dict[str, object]] = []
    classification: StepClassification = "fail"
    failure_reason: str | None = None
    try:
        deadline = started + FRONTEND_CHECKPOINT_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if process.poll() is not None:
                failure_reason = "UI process exited before the checkpoint became ready."
                break
            ready_probe = _http_probe(f"{base_url}/")
            if ready_probe["ok"] is True:
                failure_reason = None
                break
            failure_reason = str(ready_probe.get("error") or "UI page is not ready yet.")
            time.sleep(0.1)
        else:
            failure_reason = "Timed out waiting for the UI checkpoint to become ready."

        if failure_reason is None:
            semantic_failures: list[str] = []
            for name, path in _frontend_probe_targets(ctx, stage):
                probe = _http_probe(f"{base_url}{path}")
                semantic_failure = _frontend_probe_semantic_failure(
                    ctx=ctx,
                    stage=stage,
                    name=name,
                    probe=probe,
                )
                enriched_probe = {
                    "name": name,
                    "path": path,
                    "semantic_ok": semantic_failure is None,
                    **probe,
                }
                if semantic_failure is not None:
                    enriched_probe["semantic_failure"] = semantic_failure
                    semantic_failures.append(f"{name}: {semantic_failure}")
                probes.append(enriched_probe)
            classification = (
                "pass"
                if all(
                    probe.get("ok") is True and probe.get("semantic_ok") is True
                    for probe in probes
                )
                else "fail"
            )
            if classification != "pass":
                failure_reason = (
                    "One or more UI/API probes failed semantic black-box checks: "
                    + "; ".join(semantic_failures)
                    if semantic_failures
                    else "One or more UI/API probes returned a non-2xx response."
                )
    finally:
        stdout_text, stderr_text, process_return_code = _terminate_process(process)

    duration_seconds = time.monotonic() - started
    transcript = HarnessCommandTranscript(
        command=_command_text(command),
        exit_code=0 if classification == "pass" else 1,
        stdout_text=stdout_text,
        stderr_text=stderr_text,
        duration_seconds=duration_seconds,
        timed_out=failure_reason is not None
        and "Timed out" in failure_reason,
        timeout_seconds=FRONTEND_CHECKPOINT_TIMEOUT_SECONDS,
    )
    checkpoint = {
        "base_url": base_url,
        "classification": classification,
        "command": list(command),
        "created_at_utc": _utc_now(),
        "duration_seconds": duration_seconds,
        "failure_reason": failure_reason,
        "process_exit_code": process_return_code,
        "probes": probes,
        "stage": stage,
    }
    evidence_paths = _append_frontend_checkpoint(ctx=ctx, checkpoint=checkpoint)
    _record_step(
        ctx=ctx,
        action="frontend-checkpoint",
        classification=classification,
        decision=(
            "Continue after UI/API checkpoint passed."
            if classification == "pass"
            else "Stop if the stage otherwise passed because UI/API checkpoint failed."
        ),
        plan="Start `aidd ui` on loopback and inspect public operator UI/API endpoints.",
        stage=stage,
        command_results=(BlackBoxCommandResult(command=command, transcript=transcript),),
        evidence_paths=evidence_paths,
        details={"failure_reason": failure_reason} if failure_reason else None,
    )
    return classification


_PRIMARY_STAGE_OUTPUTS: dict[str, str] = {
    "idea": "idea-brief.md",
    "research": "research-notes.md",
    "plan": "plan.md",
    "review-spec": "review-spec-report.md",
    "tasklist": "tasklist.md",
    "implement": "implementation-report.md",
    "review": "review-report.md",
    "qa": "qa-report.md",
}


def _stage_output_root(ctx: FlowContext, stage: str) -> Path:
    working_copy = _require_working_copy(ctx)
    return (
        working_copy
        / ".aidd"
        / "workitems"
        / ctx.work_item
        / "stages"
        / stage
        / "output"
    )


def _stage_root(ctx: FlowContext, stage: str) -> Path:
    working_copy = _require_working_copy(ctx)
    return working_copy / ".aidd" / "workitems" / ctx.work_item / "stages" / stage


def _stage_document_path(ctx: FlowContext, stage: str, filename: str) -> Path:
    output_path = _stage_output_root(ctx, stage) / filename
    if output_path.exists():
        return output_path
    root_path = _stage_root(ctx, stage) / filename
    if root_path.exists():
        return root_path
    return output_path


def _stage_audit_paths(ctx: FlowContext, stage: str) -> tuple[Path, Path]:
    audit_root = ctx.bundle_root / STAGE_AUDITS_DIRNAME
    return audit_root / f"{stage}.json", audit_root / f"{stage}.md"


def _stage_timeout_reconciliation_path(ctx: FlowContext, stage: str) -> Path:
    audit_root = ctx.bundle_root / STAGE_AUDITS_DIRNAME
    return audit_root / f"{stage}{STAGE_TIMEOUT_RECONCILIATION_SUFFIX}"


def _read_text_if_exists(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _stage_status_section_state(stage_result_text: str) -> str | None:
    in_status = False
    for raw_line in stage_result_text.splitlines():
        line = raw_line.strip().lower()
        if line.startswith("## "):
            in_status = line == "## status"
            continue
        if not in_status:
            continue
        if "blocked" in line:
            return "blocked"
        if "succeeded" in line or "passed" in line:
            return "passed"
        if "failed" in line:
            return "failed"
    return None


def _stage_state_from_text(stage_result_text: str) -> str:
    status_section_state = _stage_status_section_state(stage_result_text)
    if status_section_state is not None:
        return status_section_state

    lowered = stage_result_text.lower()
    if "action=wait" in lowered or "state=blocked" in lowered:
        return "blocked"
    if (
        "action=proceed" in lowered
        or "state=valid" in lowered
        or "status: `succeeded`" in lowered
        or "status: succeeded" in lowered
    ):
        return "passed"
    if (
        "action=stop" in lowered
        or "state=invalid" in lowered
        or "state=failed" in lowered
        or "status: `failed`" in lowered
        or "status: failed" in lowered
    ):
        return "failed"
    return "unknown"


def _stage_metadata_status(ctx: FlowContext, stage: str) -> str | None:
    working_copy = _require_working_copy(ctx)
    metadata_path = run_stage_metadata_path(
        workspace_root=working_copy / ".aidd",
        work_item=ctx.work_item,
        run_id=ctx.run_id,
        stage=stage,
    )
    if not metadata_path.exists():
        return None
    try:
        payload = _read_json_object(metadata_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    status = payload.get("status")
    return status if isinstance(status, str) and status else None


def _resolved_stage_audit_state(
    *,
    stage_result_text: str,
    metadata_status: str | None,
) -> str:
    stage_state = _stage_state_from_text(stage_result_text)
    if stage_state != "unknown":
        return stage_state
    if metadata_status == "succeeded":
        return "passed"
    if metadata_status in {"blocked", "failed"}:
        return metadata_status
    return stage_state


def _reconcile_timed_out_stage_run(
    *,
    ctx: FlowContext,
    stage: str,
    stage_result: BlackBoxCommandResult,
) -> tuple[tuple[Path, ...], dict[str, object] | None]:
    if not stage_result.transcript.timed_out:
        return tuple(), None

    working_copy = _require_working_copy(ctx)
    workspace_root = working_copy / ".aidd"
    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item=ctx.work_item,
        run_id=ctx.run_id,
        stage=stage,
    )
    before = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=ctx.work_item,
        run_id=ctx.run_id,
        stage=stage,
    )
    previous_status = None if before is None else before.status
    reconciled = False
    if previous_status not in TERMINAL_STAGE_METADATA_STATUSES:
        persist_stage_status(
            workspace_root=workspace_root,
            work_item=ctx.work_item,
            run_id=ctx.run_id,
            stage=stage,
            status="failed",
        )
        reconciled = True

    after = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=ctx.work_item,
        run_id=ctx.run_id,
        stage=stage,
    )
    reconciled_status = None if after is None else after.status
    payload: dict[str, object] = {
        "schema_version": 1,
        "created_at_utc": _utc_now(),
        "run_id": ctx.run_id,
        "runtime_id": ctx.runtime_id,
        "scenario_id": ctx.scenario.scenario_id,
        "work_item": ctx.work_item,
        "stage": stage,
        "timed_out": True,
        "timeout_seconds": stage_result.transcript.timeout_seconds,
        "stage_run_exit_code": stage_result.exit_code,
        "metadata_path": metadata_path.as_posix(),
        "previous_status": previous_status,
        "reconciled_status": reconciled_status,
        "reconciled": reconciled,
    }
    reconciliation_path = _stage_timeout_reconciliation_path(ctx, stage)
    _write_json(reconciliation_path, payload)
    return (reconciliation_path,), payload


def _validator_verdict_from_text(validator_text: str) -> str:
    lowered = validator_text.lower()
    if not lowered.strip():
        return "missing"
    if "verdict: `pass`" in lowered or "status: `pass`" in lowered:
        return "pass"
    if "verdict: `fail`" in lowered or "status: `fail`" in lowered:
        return "fail"
    if "no findings" in lowered or "- none" in lowered:
        return "pass"
    if "finding" in lowered or "invalid" in lowered or "`high`" in lowered:
        return "fail"
    return "unknown"


_STAGE_RESULT_VALIDATOR_VERDICT_PATTERN = re.compile(
    r"validator\s+verdict\s*:\s*`?(?P<verdict>pass|fail|unknown|missing)`?",
    flags=re.IGNORECASE,
)


def _stage_result_validator_verdict_from_text(stage_result_text: str) -> str:
    for line in stage_result_text.splitlines():
        match = _STAGE_RESULT_VALIDATOR_VERDICT_PATTERN.search(line)
        if match is not None:
            return match.group("verdict").lower()
    return "unknown"


def _stage_audit_consistency_findings(
    *,
    stage_result_text: str,
    validator_verdict: str,
) -> list[dict[str, object]]:
    stage_result_validator_verdict = _stage_result_validator_verdict_from_text(
        stage_result_text
    )
    if (
        stage_result_validator_verdict not in {"pass", "fail"}
        or validator_verdict not in {"pass", "fail"}
        or stage_result_validator_verdict == validator_verdict
    ):
        return []
    return [
        {
            "kind": "stage-result-validator-verdict-mismatch",
            "severity": "warning",
            "non_gating": True,
            "stage_result_validator_verdict": stage_result_validator_verdict,
            "audit_validator_verdict": validator_verdict,
            "message": (
                "stage-result.md declares a validator verdict that differs from "
                "the canonical stage-audit validator verdict."
            ),
        }
    ]


def _stage_attempt_count(ctx: FlowContext, stage: str) -> int:
    working_copy = _require_working_copy(ctx)
    runs_root = working_copy / ".aidd" / "reports" / "runs" / ctx.work_item
    if not runs_root.exists():
        return 0
    return len(list(runs_root.glob(f"*/stages/{stage}/attempts/attempt-*")))


def _stage_unresolved_questions(ctx: FlowContext, stage: str) -> bool:
    questions_path = _questions_path(ctx, stage)
    if not questions_path.exists():
        return False
    questions_text = questions_path.read_text(encoding="utf-8", errors="replace").lower()
    no_question_markers = (
        "no unresolved blocking questions",
        "no blocking or non-blocking questions remain",
        "no questions were raised",
        "no questions yet",
    )
    if any(marker in questions_text for marker in no_question_markers):
        return False
    if (
        "[blocking]" not in questions_text
        and "pending-blocking" not in questions_text
        and "blocking questions are unresolved" not in questions_text
    ):
        return False
    return not _answers_file_has_resolved_answers(_answers_path(ctx, stage))


def _inspection_runtime_log_visible(
    inspection_results: tuple[BlackBoxCommandResult, ...],
) -> bool:
    for result in inspection_results:
        if not any(
            result.command[index : index + 2] == ("run", "logs")
            for index in range(len(result.command) - 1)
        ):
            continue
        if result.exit_code == 0 and f"{result.stdout_text}{result.stderr_text}".strip():
            return True
    return False


def _implementation_verification_evidence_shape(report_text: str) -> dict[str, object]:
    section_index = MarkdownSectionIndex.from_markdown(report_text)
    verification_match = section_index.first_match(("Verification", "Verification notes"))
    verification_text = (
        report_text
        if verification_match is None
        else section_index.section_content(verification_match[0])
    )
    verification_items = extract_implementation_verification_blocks(verification_text)
    if not verification_items:
        verification_items = tuple(
            line.strip() for line in verification_text.splitlines() if line.strip()
        )

    backed_items = []
    outcome_claims = []
    for item in verification_items:
        has_result_reference = IMPLEMENT_RESULT_PATTERN.search(item) is not None
        has_command_reference = has_implementation_command_evidence(item)
        has_artifact_reference = IMPLEMENT_ARTIFACT_REFERENCE_PATTERN.search(item) is not None
        is_deferred = is_deferred_implementation_verification(item)
        if has_result_reference:
            outcome_claims.append(item)
        if is_deferred or (
            has_result_reference and (has_command_reference or has_artifact_reference)
        ):
            backed_items.append(item)
    return {
        "backed_evidence_line_count": len(backed_items),
        "outcome_claim_line_count": len(outcome_claims),
        "has_executable_or_not_run_evidence": bool(backed_items),
    }


def _write_stage_audit(
    *,
    ctx: FlowContext,
    stage: str,
    stage_classification: StepClassification,
    inspect_classification: StepClassification,
    frontend_classification: StepClassification,
    inspection_results: tuple[BlackBoxCommandResult, ...],
) -> tuple[Path, Path, StepClassification]:
    working_copy = _require_working_copy(ctx)
    primary_filename = _PRIMARY_STAGE_OUTPUTS.get(stage)
    primary_path = (
        None
        if primary_filename is None
        else _stage_document_path(ctx, stage, primary_filename)
    )
    stage_result_path = _stage_document_path(ctx, stage, "stage-result.md")
    validator_report_path = _stage_document_path(ctx, stage, "validator-report.md")
    stage_result_text = _read_text_if_exists(stage_result_path)
    validator_text = _read_text_if_exists(validator_report_path)
    stage_metadata_status = _stage_metadata_status(ctx, stage)
    validator_verdict = _validator_verdict_from_text(validator_text)
    consistency_findings = _stage_audit_consistency_findings(
        stage_result_text=stage_result_text,
        validator_verdict=validator_verdict,
    )
    implementation_details: dict[str, object] | None = None
    implementation_policy: dict[str, object] | None = None
    if stage == "implement":
        implementation_report_text = (
            ""
            if primary_path is None
            else _read_text_if_exists(primary_path)
        )
        repository_changes = collect_repository_changes(working_copy)
        verification_evidence_shape = _implementation_verification_evidence_shape(
            implementation_report_text
        )
        tracked_changed_files = list(repository_changes.tracked_files)
        findings: list[str] = []
        policy_status: StepClassification = "pass"
        if not tracked_changed_files:
            findings.append("No tracked target repository diff was produced.")
            policy_status = "fail"
        patch_budget_files = ctx.scenario.run.patch_budget_files
        if (
            patch_budget_files is not None
            and len(tracked_changed_files) > patch_budget_files
        ):
            findings.append(
                "Tracked target repository diff exceeds patch budget: "
                f"{len(tracked_changed_files)} > {patch_budget_files}."
            )
            policy_status = "fail"
        if not bool(verification_evidence_shape["has_executable_or_not_run_evidence"]):
            findings.append(
                "Implementation verification claims do not cite executable or "
                "explicit not-run evidence."
            )
            policy_status = "fail"
        implementation_policy = {
            "status": policy_status,
            "patch_budget_files": patch_budget_files,
            "findings": findings,
        }
        implementation_details = {
            "changed_files": list(repository_changes.changed_files),
            "tracked_changed_files": tracked_changed_files,
            "untracked_changed_files": list(repository_changes.untracked_files),
            "diff_summary": repository_changes.diff_summary,
            "git_change_collection_errors": list(repository_changes.command_errors),
            "implementation_report_verification_evidence": verification_evidence_shape,
        }

    payload: dict[str, object] = {
        "schema_version": 1,
        "created_at_utc": _utc_now(),
        "run_id": ctx.run_id,
        "runtime_id": ctx.runtime_id,
        "scenario_id": ctx.scenario.scenario_id,
        "work_item": ctx.work_item,
        "stage": stage,
        "stage_state": _resolved_stage_audit_state(
            stage_result_text=stage_result_text,
            metadata_status=stage_metadata_status,
        ),
        "stage_metadata_status": stage_metadata_status,
        "classifications": {
            "stage_run": stage_classification,
            "public_inspection": inspect_classification,
            "frontend_checkpoint": frontend_classification,
        },
        "validator_verdict": validator_verdict,
        "consistency_findings": consistency_findings,
        "primary_artifact": {
            "filename": primary_filename,
            "path": None if primary_path is None else primary_path.as_posix(),
            "present": primary_path.exists() if primary_path is not None else False,
        },
        "stage_result_path": stage_result_path.as_posix(),
        "validator_report_path": validator_report_path.as_posix(),
        "repair_attempts": max(_stage_attempt_count(ctx, stage) - 1, 0),
        "unresolved_questions": _stage_unresolved_questions(ctx, stage),
        "runtime_log_visible": _inspection_runtime_log_visible(inspection_results),
        "artifact_presence_notes": [
            (
                "primary artifact present"
                if primary_path is not None and primary_path.exists()
                else "primary artifact missing"
            ),
            (
                "validator report present"
                if validator_report_path.exists()
                else "validator report missing"
            ),
            (
                "runtime logs visible through public CLI"
                if _inspection_runtime_log_visible(inspection_results)
                else "runtime logs not visible through public CLI"
            ),
        ],
    }
    if implementation_details is not None:
        payload["implementation"] = implementation_details
    if implementation_policy is not None:
        payload["implementation_policy"] = implementation_policy

    json_path, markdown_path = _stage_audit_paths(ctx, stage)
    _write_json(json_path, payload)
    primary_artifact = cast(dict[str, object], payload["primary_artifact"])
    changed_files = (
        []
        if implementation_details is None
        else cast(list[str], implementation_details["changed_files"])
    )
    md_lines = [
        f"# Stage Audit: {stage}",
        "",
        f"- Run: `{ctx.runtime_id}` / `{ctx.scenario_path.as_posix()}` / `{ctx.run_id}`",
        f"- Stage state: `{payload['stage_state']}`",
        f"- Validator verdict: `{payload['validator_verdict']}`",
        f"- Primary artifact present: `{primary_artifact['present']}`",
        f"- Repair attempts: `{payload['repair_attempts']}`",
        f"- Unresolved questions: `{payload['unresolved_questions']}`",
        f"- Runtime log visible: `{payload['runtime_log_visible']}`",
        "",
        "## Classifications",
        "",
        f"- Stage run: `{stage_classification}`",
        f"- Public inspection: `{inspect_classification}`",
        f"- Frontend checkpoint: `{frontend_classification}`",
        "",
        "## Artifact Presence Notes",
        "",
    ]
    md_lines.extend(f"- {note}" for note in cast(list[str], payload["artifact_presence_notes"]))
    if consistency_findings:
        md_lines.extend(("", "## Consistency Findings", ""))
        for finding in consistency_findings:
            md_lines.append(
                "- "
                f"`{finding['severity']}` "
                f"`{finding['kind']}`: {finding['message']} "
                f"(stage-result={finding['stage_result_validator_verdict']}, "
                f"audit={finding['audit_validator_verdict']}, "
                f"non-gating={finding['non_gating']})"
            )
    if implementation_details is not None:
        md_lines.extend(
            (
                "",
                "## Implementation Evidence",
                "",
                f"- Changed files: `{len(changed_files)}`",
                "- Tracked changed files: "
                f"`{len(cast(list[str], implementation_details['tracked_changed_files']))}`",
                "- Untracked changed files: "
                f"`{len(cast(list[str], implementation_details['untracked_changed_files']))}`",
                "- Verification evidence shape: "
                f"`{implementation_details['implementation_report_verification_evidence']}`",
            )
        )
        if implementation_policy is not None:
            md_lines.extend(
                (
                    f"- Implementation policy: `{implementation_policy['status']}`",
                    "- Implementation policy findings: "
                    + (
                        "`none`"
                        if not implementation_policy["findings"]
                        else "; ".join(cast(list[str], implementation_policy["findings"]))
                    ),
                )
            )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(md_lines).rstrip() + "\n", encoding="utf-8")
    audit_classification: StepClassification = (
        cast(StepClassification, implementation_policy["status"])
        if implementation_policy is not None
        else "pass"
    )
    return json_path, markdown_path, audit_classification


def _answers_path(ctx: FlowContext, stage: str) -> Path:
    working_copy = _require_working_copy(ctx)
    return working_copy / ".aidd" / "workitems" / ctx.work_item / "stages" / stage / "answers.md"


def _answers_file_has_resolved_answers(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace").lower()
    return "[resolved]" in text


def _questions_path(ctx: FlowContext, stage: str) -> Path:
    working_copy = _require_working_copy(ctx)
    return working_copy / ".aidd" / "workitems" / ctx.work_item / "stages" / stage / "questions.md"


def _write_operator_action_request(
    *,
    ctx: FlowContext,
    stage: str,
    stage_result: BlackBoxCommandResult,
    inspection_results: tuple[BlackBoxCommandResult, ...],
) -> tuple[Path, Path]:
    questions_path = _questions_path(ctx, stage)
    answers_path = _answers_path(ctx, stage)
    payload = {
        "schema_version": 1,
        "created_at_utc": _utc_now(),
        "action": "answer-questions",
        "scenario_id": ctx.scenario.scenario_id,
        "runtime_id": ctx.runtime_id,
        "run_id": ctx.run_id,
        "work_item": ctx.work_item,
        "stage": stage,
        "questions_path": questions_path.as_posix(),
        "answers_path": answers_path.as_posix(),
        "selected_task": ctx.selected_task_payload.get("selected_task"),
        "stage_command": {
            "command": list(stage_result.command),
            "exit_code": stage_result.exit_code,
            "stdout_text": stage_result.stdout_text,
            "stderr_text": stage_result.stderr_text,
        },
        "inspection_commands": [
            {
                "command": list(result.command),
                "exit_code": result.exit_code,
                "stdout_text": result.stdout_text,
                "stderr_text": result.stderr_text,
            }
            for result in inspection_results
        ],
    }
    json_path = ctx.bundle_root / OPERATOR_REQUEST_JSON_FILENAME
    md_path = ctx.bundle_root / OPERATOR_REQUEST_MARKDOWN_FILENAME
    _write_json(json_path, payload)
    questions_text = (
        questions_path.read_text(encoding="utf-8", errors="replace")
        if questions_path.exists()
        else "Questions file was not found."
    )
    md_path.write_text(
        "\n".join(
            (
                "# Operator Action Request",
                "",
                "- Action: `answer-questions`",
                f"- Scenario: `{ctx.scenario.scenario_id}`",
                f"- Runtime: `{ctx.runtime_id}`",
                f"- Run ID: `{ctx.run_id}`",
                f"- Work item: `{ctx.work_item}`",
                f"- Stage: `{stage}`",
                "- Operator: launching operator-agent",
                f"- Questions: `{questions_path.as_posix()}`",
                f"- Answers: `{answers_path.as_posix()}`",
                "",
                "## Question Context",
                "",
                questions_text.rstrip(),
                "",
                "## Required Operator-Agent Output",
                "",
                "- Write standard `[resolved]` answers to the answers path above.",
                "- Use exact answer lines such as `- Q1 [resolved] answer text`.",
                (
                    "- Record answer reasoning in "
                    f"`{(ctx.bundle_root / ANSWER_ANALYSIS_FILENAME).as_posix()}`."
                ),
                "",
            )
        ),
        encoding="utf-8",
    )
    return json_path, md_path


def _write_answer_analysis_if_detected(ctx: FlowContext, stage: str) -> Path | None:
    answers_path = _answers_path(ctx, stage)
    if not _answers_file_has_resolved_answers(answers_path):
        return None
    analysis_path = ctx.bundle_root / ANSWER_ANALYSIS_FILENAME
    if analysis_path.exists():
        return analysis_path
    answers_text = answers_path.read_text(encoding="utf-8", errors="replace")
    analysis_path.write_text(
        "\n".join(
            (
                "# Answer Analysis",
                "",
                f"- Scenario: `{ctx.scenario.scenario_id}`",
                f"- Stage: `{stage}`",
                f"- Answers path: `{answers_path.as_posix()}`",
                "- Source: launching operator-agent answers detected by evaluator resume.",
                "",
                "## Answers Snapshot",
                "",
                answers_text.rstrip(),
                "",
            )
        ),
        encoding="utf-8",
    )
    return analysis_path


def _runtime_approval_analysis_path(ctx: FlowContext) -> Path:
    return ctx.bundle_root / RUNTIME_APPROVAL_ANALYSIS_FILENAME


def _format_runtime_approval_request_lines(
    request: RuntimeOperatorRequest | None,
) -> tuple[str, ...]:
    if request is None:
        return (
            "- Kind: `unknown`",
            "- Tool: ``",
            "- CWD: ``",
            "- Paths: `none`",
        )
    return (
        f"- Kind: `{request.kind.value}`",
        f"- Tool: `{request.tool_name or ''}`",
        f"- CWD: `{'' if request.cwd is None else request.cwd.as_posix()}`",
        "- Paths: "
        + (
            "`none`"
            if not request.paths
            else ", ".join(f"`{path.as_posix()}`" for path in request.paths)
        ),
    )


def _write_runtime_approval_analysis_from_attempt_ledgers(ctx: FlowContext) -> Path | None:
    if ctx.prepared_working_copy is None:
        return None
    run_root = (
        ctx.prepared_working_copy.working_copy_path
        / ".aidd"
        / "reports"
        / "runs"
        / ctx.work_item
        / ctx.run_id
    )
    if not run_root.exists():
        return None

    sections: list[str] = []
    decision_paths = sorted(
        run_root.glob(f"stages/*/attempts/attempt-*/{OPERATOR_DECISIONS_FILENAME}")
    )
    for decision_path in decision_paths:
        decisions = _read_jsonl_objects(decision_path)
        if not decisions:
            continue
        request_path = decision_path.with_name(OPERATOR_REQUESTS_FILENAME)
        requests_by_id: dict[str, RuntimeOperatorRequest] = {}
        for raw_request in _read_jsonl_objects(request_path):
            raw_request_id = raw_request.get("id")
            if not isinstance(raw_request_id, str) or not raw_request_id:
                continue
            try:
                requests_by_id[raw_request_id] = RuntimeOperatorRequest.from_dict(raw_request)
            except (KeyError, TypeError, ValueError):
                continue

        try:
            relative = decision_path.relative_to(run_root)
            stage = relative.parts[1]
            attempt = relative.parts[3]
        except (ValueError, IndexError):
            stage = "unknown"
            attempt = decision_path.parent.name

        for raw_decision in decisions:
            request_id = str(raw_decision.get("request_id") or "unknown")
            request = requests_by_id.get(request_id)
            action = str(raw_decision.get("action") or "unknown")
            source = str(raw_decision.get("source") or "unknown")
            reason = str(raw_decision.get("reason") or "")
            sections.extend(
                (
                    f"## {stage} / {attempt} / {request_id}",
                    "",
                    *_format_runtime_approval_request_lines(request),
                    f"- Decision: `{action}`",
                    f"- Source: `{source}`",
                    f"- Reason: {reason}",
                    "",
                )
            )

    if not sections:
        return None

    path = _runtime_approval_analysis_path(ctx)
    path.write_text(
        "\n".join(
            (
                "# Runtime Approval Analysis",
                "",
                f"- Scenario: `{ctx.scenario.scenario_id}`",
                f"- Runtime: `{ctx.runtime_id}`",
                f"- Run ID: `{ctx.run_id}`",
                "- Runtime approvals: `operator-ui-local-project-lane-only`",
                "",
                *sections,
            )
        ),
        encoding="utf-8",
    )
    return path


def _run_stage_and_inspect(ctx: FlowContext, stage: str) -> StepClassification:
    working_copy = _require_working_copy(ctx)
    environment = _harness_environment_for_context(ctx)
    answer_analysis_path = _write_answer_analysis_if_detected(ctx, stage)
    if answer_analysis_path is not None:
        _record_step(
            ctx=ctx,
            action="answer-questions",
            classification="pass",
            decision="Answers are present; retry the blocked stage through public CLI.",
            plan="Consume launching operator-agent answers without generating them inside AIDD.",
            stage=stage,
            evidence_paths=(answer_analysis_path, _answers_path(ctx, stage)),
        )

    stage_command = _stage_run_command(ctx, stage)
    stage_timeout_seconds = _stage_command_timeout_seconds(ctx.scenario)
    _persist_state(
        ctx=ctx,
        status="running",
        next_action="run-stage",
        current_stage=stage,
        completed_stages=_state_completed_stages(ctx.bundle_root),
        extra={
            "active_step": {
                "action": "run-stage",
                "stage": stage,
                "started_at_utc": _utc_now(),
                "timeout_seconds": stage_timeout_seconds,
                "command": list(stage_command),
            }
        },
    )
    stage_result = _run_black_box_command(
        command=stage_command,
        cwd=working_copy,
        environment=environment,
        timeout_seconds=stage_timeout_seconds,
    )
    classification = _classify_stage_run(stage_result)
    timeout_evidence_paths, timeout_reconciliation = _reconcile_timed_out_stage_run(
        ctx=ctx,
        stage=stage,
        stage_result=stage_result,
    )
    _record_step(
        ctx=ctx,
        action="run-stage",
        classification=classification,
        decision=(
            "Inspect public artifacts before deciding next stage."
            if classification == "pass"
            else "Inspect public artifacts before stopping or requesting operator input."
        ),
        plan=f"Run `{stage}` through the installed public `aidd stage run` surface.",
        stage=stage,
        command_results=(stage_result,),
        evidence_paths=timeout_evidence_paths,
        details=(
            {"timeout_reconciliation": timeout_reconciliation}
            if timeout_reconciliation is not None
            else None
        ),
    )

    inspection_results = tuple(
        _run_black_box_command(
            command=command,
            cwd=working_copy,
            environment=environment,
            timeout_seconds=60.0,
        )
        for command in _inspection_commands(ctx, stage)
    )
    inspection_reports_blocked = _inspection_reports_unresolved_questions(inspection_results)
    inspect_classification: StepClassification
    if inspection_reports_blocked:
        inspect_classification = "blocked"
    elif classification == "pass":
        inspect_classification = (
            "pass"
            if all(result.exit_code == 0 for result in inspection_results)
            else "fail"
        )
    else:
        inspect_classification = (
            "pass"
            if any(result.exit_code == 0 for result in inspection_results)
            else classification
        )
    if inspection_reports_blocked:
        inspect_decision = (
            "Stop and request operator input because public question inspection "
            "found unresolved blocking questions."
        )
    elif classification == "pass" and inspect_classification == "pass":
        inspect_decision = "Continue to the next stage."
    elif classification == "pass":
        inspect_decision = (
            "Stop because public inspection failed after a successful stage run."
        )
    else:
        inspect_decision = "Use inspection output to classify the blocked or failed stage."
    _record_step(
        ctx=ctx,
        action="inspect-stage",
        classification=inspect_classification,
        decision=inspect_decision,
        plan=(
            "Inspect stage summary, questions, run metadata, logs, and artifacts "
            "through public CLI."
        ),
        stage=stage,
        command_results=inspection_results,
    )
    if inspection_reports_blocked:
        classification = "blocked"
    frontend_classification = (
        "skipped"
        if stage_result.transcript.timed_out
        else _run_frontend_checkpoint(ctx, stage)
    )
    _, _, audit_classification = _write_stage_audit(
        ctx=ctx,
        stage=stage,
        stage_classification=classification,
        inspect_classification=inspect_classification,
        frontend_classification=frontend_classification,
        inspection_results=inspection_results,
    )
    if classification == "pass" and inspect_classification == "fail":
        _persist_state(
            ctx=ctx,
            status="fail",
            next_action="stop",
            current_stage=stage,
            completed_stages=_state_completed_stages(ctx.bundle_root),
            extra={"error": "public inspection failed"},
        )
        return "fail"
    if classification == "pass" and audit_classification == "fail":
        _persist_state(
            ctx=ctx,
            status="fail",
            next_action="stop",
            current_stage=stage,
            completed_stages=_state_completed_stages(ctx.bundle_root),
            extra={"error": "stage audit failed"},
        )
        return "fail"
    if classification == "pass" and frontend_classification == "fail":
        _persist_state(
            ctx=ctx,
            status="fail",
            next_action="stop",
            current_stage=stage,
            completed_stages=_state_completed_stages(ctx.bundle_root),
            extra={"error": "frontend checkpoint failed"},
        )
        return "fail"
    if classification == "pass":
        completed = (*_state_completed_stages(ctx.bundle_root), stage)
        _persist_state(
            ctx=ctx,
            status="running",
            next_action="run-stage",
            current_stage=_next_stage_after(ctx.scenario, stage),
            completed_stages=completed,
        )
        quality_gate = _quality_review_gate(ctx)
        if quality_gate is not None:
            return quality_gate
        return classification
    if classification == "blocked":
        existing_request_paths = (
            ctx.bundle_root / OPERATOR_REQUEST_JSON_FILENAME,
            ctx.bundle_root / OPERATOR_REQUEST_MARKDOWN_FILENAME,
        )
        request_paths = (
            existing_request_paths
            if all(path.exists() for path in existing_request_paths)
            else _write_operator_action_request(
                ctx=ctx,
                stage=stage,
                stage_result=stage_result,
                inspection_results=inspection_results,
            )
        )
        _record_step(
            ctx=ctx,
            action="answer-questions",
            classification="blocked",
            decision="Stop and wait for launching operator-agent input.",
            plan="Surface blocking questions or runtime approvals as an operator action request.",
            stage=stage,
            evidence_paths=request_paths,
        )
        _persist_state(
            ctx=ctx,
            status="blocked",
            next_action="answer-questions",
            current_stage=stage,
            completed_stages=_state_completed_stages(ctx.bundle_root),
            extra={
                "operator_action_request_json": request_paths[0].as_posix(),
                "operator_action_request_markdown": request_paths[1].as_posix(),
            },
        )
        return classification
    _persist_state(
        ctx=ctx,
        status="fail",
        next_action="stop",
        current_stage=stage,
        completed_stages=_state_completed_stages(ctx.bundle_root),
        extra={
            "stage_exit_code": stage_result.exit_code,
            **(
                {"timeout_reconciliation": timeout_reconciliation}
                if timeout_reconciliation is not None
                else {}
            ),
        },
    )
    return classification


def _next_stage_after(scenario: Scenario, stage: str) -> str | None:
    stages = _stage_scope(scenario)
    index = stages.index(stage)
    if index == len(stages) - 1:
        return None
    return stages[index + 1]


def _run_stage_loop(ctx: FlowContext) -> StepClassification:
    while True:
        quality_gate = _quality_review_gate(ctx)
        if quality_gate is not None:
            return quality_gate
        stage = _first_incomplete_stage(ctx)
        if stage is None:
            return "pass"
        classification = _run_stage_and_inspect(ctx, stage)
        if classification != "pass":
            return classification


def _has_timed_out_stage_attempt(ctx: FlowContext) -> bool:
    if ctx.prepared_working_copy is None:
        return False
    working_copy = ctx.prepared_working_copy.working_copy_path
    run_root = working_copy / ".aidd" / "reports" / "runs" / ctx.work_item / ctx.run_id
    if not run_root.exists():
        return False
    for runtime_exit_path in run_root.glob("stages/*/attempts/attempt-*/runtime-exit.json"):
        payload = _read_json_object(runtime_exit_path)
        if payload.get("exit_classification") == "timeout":
            return True
    return False


def _synthetic_aidd_run_result(ctx: FlowContext, exit_code: int) -> HarnessAiddRunResult:
    steps = _load_steps(ctx.bundle_root)
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    timed_out = _has_timed_out_stage_attempt(ctx)
    for step in steps:
        raw_commands = step.get("commands")
        commands = raw_commands if isinstance(raw_commands, list) else []
        for command in commands:
            if not isinstance(command, dict):
                continue
            if command.get("timed_out") is True:
                timed_out = True
            stdout = command.get("stdout_text")
            stderr = command.get("stderr_text")
            if isinstance(stdout, str) and stdout.strip():
                stdout_lines.append(stdout.rstrip())
            if isinstance(stderr, str) and stderr.strip():
                stderr_lines.append(stderr.rstrip())
    transcript = HarnessCommandTranscript(
        command="black-box-stage-loop",
        exit_code=exit_code,
        stdout_text="\n".join(stdout_lines),
        stderr_text="\n".join(stderr_lines),
        duration_seconds=max(time.monotonic() - ctx.started, 0.0),
        timed_out=timed_out,
        timeout_seconds=None,
    )
    return HarnessAiddRunResult(
        command=("black-box-stage-loop",),
        runtime_id=ctx.runtime_id,
        work_item=ctx.work_item,
        exit_code=exit_code,
        stdout_text=transcript.stdout_text,
        stderr_text=transcript.stderr_text,
        duration_seconds=transcript.duration_seconds,
        command_transcript=transcript,
        timed_out=timed_out,
        timeout_seconds=None,
    )


def _run_verify(ctx: FlowContext) -> HarnessVerificationResult:
    working_copy = _require_working_copy(ctx)
    aidd_result = _synthetic_aidd_run_result(ctx, exit_code=0)
    before_verify_snapshot = collect_live_workspace_snapshot(working_copy)
    try:
        result = run_verification_steps(
            scenario=ctx.scenario,
            working_copy_path=working_copy,
            aidd_run_result=aidd_result,
            environment=_harness_environment_for_context(ctx),
        )
    except HarnessVerificationError as exc:
        transcripts = _transcripts_from_error(exc)
        partial_result = HarnessVerificationResult(
            executed_commands=tuple(transcript.command for transcript in transcripts),
            aidd_exit_code=0,
            command_transcripts=transcripts,
            duration_seconds=_transcript_duration(transcripts),
        )
        _write_step_transcript(
            path=ctx.bundle_root / VERIFY_TRANSCRIPT_FILENAME,
            step="verify",
            transcripts=partial_result.command_transcripts,
        )
        _record_step(
            ctx=ctx,
            action="verify",
            classification="fail",
            decision="Stop before teardown because scenario verification failed.",
            plan="Run manifest verification commands after every stage passed.",
            evidence_paths=(ctx.bundle_root / VERIFY_TRANSCRIPT_FILENAME,),
            details={"error": str(exc)},
        )
        _persist_state(
            ctx=ctx,
            status="fail",
            next_action="stop",
            current_stage=None,
            completed_stages=_state_completed_stages(ctx.bundle_root),
            extra={"error": str(exc)},
        )
        raise
    after_verify_snapshot = collect_live_workspace_snapshot(working_copy)
    workspace_cleanup = _verification_workspace_cleanup(
        repo_root=working_copy,
        before_verify=before_verify_snapshot,
        after_verify=after_verify_snapshot,
    )
    _write_step_transcript(
        path=ctx.bundle_root / VERIFY_TRANSCRIPT_FILENAME,
        step="verify",
        transcripts=result.command_transcripts,
        extra={"workspace_cleanup": workspace_cleanup},
    )
    _record_step(
        ctx=ctx,
        action="verify",
        classification="pass",
        decision="Continue to teardown and final reporting.",
        plan="Run manifest verification commands after every stage passed.",
        evidence_paths=(ctx.bundle_root / VERIFY_TRANSCRIPT_FILENAME,),
        details={"workspace_cleanup": workspace_cleanup},
    )
    _persist_state(
        ctx=ctx,
        status="running",
        next_action="teardown",
        current_stage=None,
        completed_stages=_state_completed_stages(ctx.bundle_root),
    )
    return result


def _run_teardown(ctx: FlowContext) -> tuple[HarnessTeardownResult | None, BaseException | None]:
    if not ctx.teardown_commands:
        _write_step_transcript(
            path=ctx.bundle_root / TEARDOWN_TRANSCRIPT_FILENAME,
            step="teardown",
            transcripts=tuple(),
        )
        _record_step(
            ctx=ctx,
            action="teardown",
            classification="skipped",
            decision="Finish reporting; no teardown commands are declared.",
            plan="Run declared teardown commands after verification.",
            evidence_paths=(ctx.bundle_root / TEARDOWN_TRANSCRIPT_FILENAME,),
        )
        return None, None
    working_copy = _require_working_copy(ctx)
    try:
        result = run_teardown_steps(
            teardown_commands=ctx.teardown_commands,
            working_copy_path=working_copy,
            environment=_harness_environment_for_context(ctx),
        )
    except HarnessTeardownError as exc:
        transcripts = _transcripts_from_error(exc)
        partial_result = HarnessTeardownResult(
            executed_commands=tuple(transcript.command for transcript in transcripts),
            command_transcripts=transcripts,
            duration_seconds=_transcript_duration(transcripts),
        )
        _write_step_transcript(
            path=ctx.bundle_root / TEARDOWN_TRANSCRIPT_FILENAME,
            step="teardown",
            transcripts=partial_result.command_transcripts,
        )
        _record_step(
            ctx=ctx,
            action="teardown",
            classification="infra-fail",
            decision="Finish reporting with teardown infrastructure failure.",
            plan="Run declared teardown commands after verification.",
            evidence_paths=(ctx.bundle_root / TEARDOWN_TRANSCRIPT_FILENAME,),
            details={"error": str(exc)},
        )
        return partial_result, exc
    _write_step_transcript(
        path=ctx.bundle_root / TEARDOWN_TRANSCRIPT_FILENAME,
        step="teardown",
        transcripts=result.command_transcripts,
    )
    _record_step(
        ctx=ctx,
        action="teardown",
        classification="pass",
        decision="Finish reporting.",
        plan="Run declared teardown commands after verification.",
        evidence_paths=(ctx.bundle_root / TEARDOWN_TRANSCRIPT_FILENAME,),
    )
    return result, None


def _copy_best_effort_artifact(*, source: Path, destination: Path) -> Path | None:
    if not source.exists() or not source.is_file():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(source.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    return destination


def _copy_attempt_jsonl_artifacts(
    *,
    ctx: FlowContext,
    filename: str,
    destination: Path,
) -> Path | None:
    if ctx.prepared_working_copy is None:
        return None
    working_copy = ctx.prepared_working_copy.working_copy_path
    if not working_copy.exists():
        return None
    runs_root = working_copy / ".aidd" / "reports" / "runs" / ctx.work_item
    if not runs_root.exists():
        return None
    search_root = runs_root / ctx.run_id
    glob_pattern = f"stages/*/attempts/attempt-*/{filename}"
    if not search_root.exists():
        search_root = runs_root
        glob_pattern = f"*/stages/*/attempts/attempt-*/{filename}"
    lines: list[str] = []
    for source_path in sorted(search_root.glob(glob_pattern)):
        text = source_path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            lines.extend(text.splitlines())
    if not lines:
        return None
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _format_failure_step(step: dict[str, Any]) -> tuple[str, str]:
    action = str(step.get("action", "unknown"))
    stage = step.get("stage")
    reason = str(step.get("decision", "step did not pass"))
    stage_text = f" stage `{stage}`" if isinstance(stage, str) and stage else ""
    return action, f"{action}{stage_text}: {reason}"


def _first_failure_from_steps(
    ctx: FlowContext,
    *,
    status: VerdictStatus,
) -> tuple[str, str | None]:
    steps = _load_steps(ctx.bundle_root)
    classifications: tuple[str, ...]
    if status == "blocked":
        classifications = ("blocked",)
    elif status == "infra-fail":
        classifications = ("infra-fail", "fail")
    else:
        classifications = ("fail", "infra-fail")

    for step in steps:
        classification = step.get("classification")
        action = step.get("action")
        if classification not in classifications or action in {"finish", "stop"}:
            continue
        return _format_failure_step(step)

    if status != "pass":
        for step in steps:
            classification = step.get("classification")
            action = step.get("action")
            if classification in {"fail", "blocked", "infra-fail"} and action not in {
                "finish",
                "stop",
            }:
                return _format_failure_step(step)
    return "none", None


def _required_interview_flow_failure(ctx: FlowContext) -> str | None:
    if not ctx.scenario.run.interview_required:
        return None

    steps = _load_steps(ctx.bundle_root)
    observed_blocked_question_stop = any(
        step.get("classification") == "blocked"
        and step.get("action") in {"run-stage", "inspect-stage"}
        for step in steps
    )
    observed_operator_answers = any(
        step.get("action") == "answer-questions" and step.get("classification") == "pass"
        for step in steps
    )

    if not observed_blocked_question_stop:
        return (
            "Required interview flow was not observed: scenario requires at least "
            "one blocking question stop before progression."
        )
    if not observed_operator_answers:
        return (
            "Required interview flow was not observed: scenario requires "
            "operator-authored answers before resumed progression."
        )
    return None


def _write_runtime_log_from_steps(ctx: FlowContext) -> Path:
    lines = [
        f"run_id={ctx.run_id}",
        f"scenario_id={ctx.scenario.scenario_id}",
        f"runtime_id={ctx.runtime_id}",
        "source=black-box-live-e2e-flow-steps",
    ]
    for step in _load_steps(ctx.bundle_root):
        lines.append(
            "step="
            f"{step.get('step_index')} action={step.get('action')} "
            f"classification={step.get('classification')} stage={step.get('stage')}"
        )
        raw_commands = step.get("commands")
        commands = raw_commands if isinstance(raw_commands, list) else []
        for command in commands:
            if not isinstance(command, dict):
                continue
            lines.append(
                "command="
                f"{_command_text(tuple(str(item) for item in command.get('command', [])))} "
                f"exit={command.get('exit_code')}"
            )
            stdout = command.get("stdout_text")
            stderr = command.get("stderr_text")
            if isinstance(stdout, str) and stdout.strip():
                lines.append("stdout:")
                lines.extend(stdout.rstrip().splitlines())
            if isinstance(stderr, str) and stderr.strip():
                lines.append("stderr:")
                lines.extend(stderr.rstrip().splitlines())
    path = ctx.bundle_root / RUNTIME_LOG_FILENAME
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def _write_validator_report_from_steps(
    *,
    ctx: FlowContext,
    status: VerdictStatus,
    summary: str,
) -> Path:
    finding_lines: list[str] = []
    if status != "pass":
        for step in _load_steps(ctx.bundle_root):
            classification = step.get("classification")
            if classification not in {"fail", "blocked", "infra-fail"}:
                continue
            finding_lines.append(
                f"- `{classification}` in `{step.get('action', 'unknown')}`: "
                f"{step.get('decision', '')}"
            )
    if not finding_lines:
        finding_lines.append("- none")
    path = ctx.bundle_root / VALIDATOR_REPORT_FILENAME
    path.write_text(
        "\n".join(
            (
                "# Validator report",
                "",
                "## Verdict",
                f"- Verdict: `{'pass' if status == 'pass' else 'fail'}`",
                f"- Summary: {summary}",
                "",
                "## Findings",
                *finding_lines,
                "",
            )
        ),
        encoding="utf-8",
    )
    return path


def _write_log_analysis(
    *,
    ctx: FlowContext,
    status: VerdictStatus,
    first_failure_note: str | None,
) -> Path:
    boundary_action, note = (
        ("none", None)
        if status == "pass"
        else _first_failure_from_steps(ctx, status=status)
    )
    reason = first_failure_note or note or "No unresolved failure signals were recorded."
    timeout_policy = _timeout_policy_payload(ctx)
    path = ctx.bundle_root / LOG_ANALYSIS_FILENAME
    path.write_text(
        "\n".join(
            (
                "# Log Analysis",
                "",
                f"- Status: `{status}`",
                f"- First Failure Boundary: `{boundary_action}`",
                "- Signal Source: `flow-steps.json`",
                "- Signal Line: `n/a`",
                f"- Reason: {reason}",
                "",
                "## Timeout Policy",
                "",
                f"- Scope: `{timeout_policy['scope']}`",
                "- Stage Command Timeout: "
                f"`{_format_timeout_budget(timeout_policy['stage_command_timeout_seconds'])}`",
                "- Global Flow Timeout: "
                f"`{_format_timeout_budget(timeout_policy['global_flow_timeout_seconds'])}`",
                "- Runtime Config Source: "
                f"`{timeout_policy['runtime_config_source'] or 'n/a'}`",
                f"- Runtime Adapter Timeout Profile: `{_runtime_config_timeout_profile(ctx)}`",
                "",
            )
        ),
        encoding="utf-8",
    )
    return path


def _stage_timing_payload_from_flow(
    *,
    ctx: FlowContext,
    teardown_result: HarnessTeardownResult | None,
) -> dict[str, object]:
    workspace_root = (
        None
        if ctx.prepared_working_copy is None
        else ctx.prepared_working_copy.working_copy_path / ".aidd"
    )
    payload = build_stage_timing_payload(
        scenario=ctx.scenario,
        run_id=ctx.run_id,
        runtime_id=ctx.runtime_id,
        work_item=ctx.work_item,
        workspace_root=workspace_root,
        total_duration_seconds=max(time.monotonic() - ctx.started, 0.0),
        install_result=ctx.install_result,
        teardown_result=teardown_result,
    )
    flow_steps: list[dict[str, object]] = []
    for step in _load_steps(ctx.bundle_root):
        commands_raw = step.get("commands")
        commands = commands_raw if isinstance(commands_raw, list) else []
        first_exit_code: int | None = None
        timeout_values: list[float] = []
        for command in commands:
            if not isinstance(command, dict):
                continue
            exit_code = command.get("exit_code")
            if isinstance(exit_code, int):
                first_exit_code = exit_code
                break
        for command in commands:
            if not isinstance(command, dict):
                continue
            timeout_seconds = command.get("timeout_seconds")
            if isinstance(timeout_seconds, int | float):
                timeout_values.append(float(timeout_seconds))
        step_timeout_seconds = (
            timeout_values[0]
            if timeout_values and all(value == timeout_values[0] for value in timeout_values)
            else None
        )
        flow_steps.append(
            {
                "command_count": len(commands),
                "duration_seconds": step.get("duration_seconds", 0.0),
                "exit_code": first_exit_code,
                "stage": step.get("stage"),
                "status": step.get("classification", "unknown"),
                "step": step.get("action", "unknown"),
                "timed_out": any(
                    isinstance(command, dict) and command.get("timed_out") is True
                    for command in commands
                ),
                "timeout_seconds": step_timeout_seconds,
            }
        )
    payload["steps"] = flow_steps
    return payload


def _write_frontend_checkpoint_placeholders(ctx: FlowContext) -> None:
    json_path = ctx.bundle_root / FRONTEND_CHECKPOINTS_JSON_FILENAME
    md_path = ctx.bundle_root / FRONTEND_CHECKPOINTS_MARKDOWN_FILENAME
    if json_path.exists() and md_path.exists():
        return
    if _frontend_checkpoints_enabled(ctx):
        payload = (
            _read_frontend_checkpoint_payload(ctx)
            if json_path.exists()
            else {
                "enabled": True,
                "reason": "frontend checkpoints were enabled but no checkpoint was recorded",
                "checkpoints": [],
            }
        )
        _write_json(json_path, payload)
        _write_frontend_checkpoint_markdown(ctx, payload)
        return
    _write_json(
        json_path,
        {
            "enabled": False,
            "reason": "frontend checkpoints were not enabled for this evaluator run",
            "checkpoints": [],
        },
    )
    md_path.write_text(
        "# Frontend Checkpoints\n\n- Frontend checkpointing was not enabled.\n",
        encoding="utf-8",
    )


def _write_runtime_approval_analysis_placeholder(ctx: FlowContext) -> None:
    path = _runtime_approval_analysis_path(ctx)
    if path.exists():
        return
    if _write_runtime_approval_analysis_from_attempt_ledgers(ctx) is not None:
        return
    path.write_text(
        "\n".join(
            (
                "# Runtime Approval Analysis",
                "",
                f"- Scenario: `{ctx.scenario.scenario_id}`",
                f"- Runtime: `{ctx.runtime_id}`",
                f"- Run ID: `{ctx.run_id}`",
                "- Runtime approvals: `operator-ui-local-project-lane-only`",
                "",
                "- No runtime approval decisions were recorded.",
                "",
            )
        ),
        encoding="utf-8",
    )


def _ensure_transcript_files(ctx: FlowContext) -> None:
    for filename, step in (
        (INSTALL_TRANSCRIPT_FILENAME, "install"),
        (SETUP_TRANSCRIPT_FILENAME, "setup"),
        (VERIFY_TRANSCRIPT_FILENAME, "verify"),
        (TEARDOWN_TRANSCRIPT_FILENAME, "teardown"),
    ):
        path = ctx.bundle_root / filename
        if path.exists():
            continue
        _write_step_transcript(path=path, step=step, transcripts=tuple())


def _stage_audit_payloads(ctx: FlowContext) -> list[dict[str, object]]:
    audit_root = ctx.bundle_root / STAGE_AUDITS_DIRNAME
    if not audit_root.exists():
        return []
    payloads: list[dict[str, object]] = []
    for path in sorted(audit_root.glob("*.json")):
        try:
            payloads.append(dict(_read_json_object(path)))
        except (OSError, ValueError, json.JSONDecodeError):
            payloads.append({"path": path.as_posix(), "error": "failed to read audit"})
    return payloads


def _write_harness_metadata(
    *,
    ctx: FlowContext,
    status: VerdictStatus,
) -> Path:
    state = _read_json_object(_state_path(ctx.bundle_root))
    payload: dict[str, object] = {
        "automation_lane": ctx.scenario.automation_lane,
        "canonical_runtime": ctx.scenario.canonical_runtime,
        "created_at_utc": _utc_now(),
        "feature_size": ctx.scenario.feature_size,
        "is_live": ctx.scenario.is_live,
        "run_id": ctx.run_id,
        "runtime_id": ctx.runtime_id,
        "scenario_class": ctx.scenario.scenario_class,
        "scenario_id": ctx.scenario.scenario_id,
        "status": status,
        "task": ctx.scenario.task,
        "work_item": ctx.work_item,
        "stage_scope": {
            "start": ctx.scenario.run.stage_start,
            "end": ctx.scenario.run.stage_end,
        },
        "runtime_targets": list(ctx.scenario.runtime_targets),
        "aidd_artifact_references": {
            "flow_state": (ctx.bundle_root / FLOW_STATE_FILENAME).as_posix(),
            "flow_steps": (ctx.bundle_root / FLOW_STEPS_FILENAME).as_posix(),
            "flow_report": (ctx.bundle_root / FLOW_REPORT_FILENAME).as_posix(),
            "operator_actions": (ctx.bundle_root / OPERATOR_ACTIONS_FILENAME).as_posix(),
            "runtime_approval_analysis": (
                ctx.bundle_root / RUNTIME_APPROVAL_ANALYSIS_FILENAME
            ).as_posix(),
            "scenario_path": ctx.scenario_path.as_posix(),
            "stage_audits": (ctx.bundle_root / STAGE_AUDITS_DIRNAME).as_posix(),
            "target_workspace_evidence": (
                ctx.bundle_root / TARGET_WORKSPACE_EVIDENCE_JSON_FILENAME
            ).as_posix(),
            "target_workspace_evidence_markdown": (
                ctx.bundle_root / TARGET_WORKSPACE_EVIDENCE_MARKDOWN_FILENAME
            ).as_posix(),
            "frontend_checkpoints": (
                ctx.bundle_root / FRONTEND_CHECKPOINTS_JSON_FILENAME
            ).as_posix(),
            "next_flow_checkpoint": (
                ctx.bundle_root / NEXT_FLOW_CHECKPOINT_JSON_FILENAME
            ).as_posix(),
            "next_flow_lineage": (ctx.bundle_root / NEXT_FLOW_LINEAGE_FILENAME).as_posix(),
        },
        "black_box": {
            "operator_surface": "installed-aidd-cli",
            "stage_execution": "aidd stage run",
            "frontend_checkpoint_evidence": (
                ctx.bundle_root / FRONTEND_CHECKPOINTS_JSON_FILENAME
            ).as_posix(),
            "inspection": [
                "aidd stage summary",
                "aidd stage questions",
                "aidd run show",
                "aidd run logs",
                "aidd run artifacts",
                "aidd ui",
                "aidd ui /api/run",
                "aidd ui /api/stage",
                "aidd ui /api/questions",
                "aidd ui /api/logs",
                "aidd ui /api/artifacts",
            ],
        },
        "flow_state": state,
        "temp_layout": {
            "work_root": ctx.workspace_root.as_posix(),
            "run_work_root": (ctx.workspace_root / ctx.run_id).as_posix(),
            "report_root": ctx.report_root.as_posix(),
            "bundle_root": ctx.bundle_root.as_posix(),
            "source_snapshot": state.get("source_snapshot"),
            "target_repo_root": state.get("target_repo_root") or state.get("working_copy_path"),
            "target_workspace_root": state.get("target_workspace_root"),
        },
        "stage_audits": _stage_audit_payloads(ctx),
    }
    if ctx.prepared_working_copy is None:
        artifact_refs = cast(dict[str, object], payload["aidd_artifact_references"])
        artifact_refs.pop("target_workspace_evidence", None)
        artifact_refs.pop("target_workspace_evidence_markdown", None)
    if state.get("install") is not None:
        payload["aidd_install"] = state["install"]
    if ctx.prepared_working_copy is not None:
        payload["execution_context"] = {
            "resource_source": "packaged",
            "target_repository_cwd": ctx.prepared_working_copy.working_copy_path.as_posix(),
            "workspace_root": (
                ctx.prepared_working_copy.working_copy_path / ".aidd"
            ).as_posix(),
            "work_root": ctx.workspace_root.as_posix(),
            "report_root": ctx.report_root.as_posix(),
        }
    return _write_json(ctx.bundle_root / HARNESS_METADATA_FILENAME, payload)


def _grader_payload(
    *,
    ctx: FlowContext,
    status: VerdictStatus,
    summary: str,
    next_flow_checkpoint: dict[str, object],
    first_failure_note: str | None,
) -> dict[str, object]:
    return {
        "execution": {
            "status": status,
            "summary": summary,
            "first_failure_note": first_failure_note,
            "step_evidence_source": (ctx.bundle_root / FLOW_STEPS_FILENAME).as_posix(),
        },
        "run_id": ctx.run_id,
        "runtime_id": ctx.runtime_id,
        "scenario_id": ctx.scenario.scenario_id,
        "next_flow_checkpoint": {
            "artifact": (ctx.bundle_root / NEXT_FLOW_CHECKPOINT_JSON_FILENAME).as_posix(),
            "operator_decision": next_flow_checkpoint.get("next_flow_actions", {}),
            "flow_complete_visible": next_flow_checkpoint.get("flow_complete_visible"),
        },
        "manual_quality_artifacts": _manual_quality_artifacts_payload(ctx),
        "selected_task": ctx.selected_task_payload.get("selected_task"),
        "stage_audits": _stage_audit_payloads(ctx),
        "steps": _load_steps(ctx.bundle_root),
    }


def _terminal_step_classification(status: VerdictStatus) -> StepClassification:
    if status == "pass":
        return "pass"
    if status == "blocked":
        return "blocked"
    if status == "infra-fail":
        return "infra-fail"
    return "fail"


def _record_terminal_decision_step(
    *,
    ctx: FlowContext,
    status: VerdictStatus,
    evidence_paths: tuple[Path, ...] = tuple(),
) -> None:
    _record_step(
        ctx=ctx,
        action="finish" if status == "pass" else "stop",
        classification=_terminal_step_classification(status),
        decision=f"Final verdict is `{status}`.",
        plan="Generate final audit artifacts from black-box step evidence.",
        evidence_paths=(
            ctx.bundle_root / VERDICT_FILENAME,
            ctx.bundle_root / GRADER_FILENAME,
            ctx.bundle_root / LOG_ANALYSIS_FILENAME,
            ctx.bundle_root / STAGE_TIMING_JSON_FILENAME,
            ctx.bundle_root / STAGE_TIMING_MARKDOWN_FILENAME,
            ctx.bundle_root / FRONTEND_CHECKPOINTS_JSON_FILENAME,
            ctx.bundle_root / FRONTEND_CHECKPOINTS_MARKDOWN_FILENAME,
            ctx.bundle_root / RUNTIME_APPROVAL_ANALYSIS_FILENAME,
            ctx.bundle_root / NEXT_FLOW_CHECKPOINT_JSON_FILENAME,
            ctx.bundle_root / NEXT_FLOW_CHECKPOINT_MARKDOWN_FILENAME,
            ctx.bundle_root / NEXT_FLOW_LINEAGE_FILENAME,
            ctx.bundle_root / STAGE_AUDITS_DIRNAME,
            *evidence_paths,
        ),
    )


@contextlib.contextmanager
def _live_interruption_handlers() -> Any:
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    previous_handlers: dict[int, Any] = {}

    def _handler(signum: int, _frame: object) -> None:
        raise LiveE2EInterrupted(
            f"Black-box live E2E interrupted by signal {signum}.",
            signum=signum,
        )

    for signum in (int(signal.SIGINT), int(signal.SIGTERM)):
        previous_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, _handler)
    try:
        yield
    finally:
        for signum, previous_handler in previous_handlers.items():
            signal.signal(signum, previous_handler)


def _record_interruption(
    *,
    ctx: FlowContext,
    interruption: LiveE2EInterrupted,
) -> None:
    command_results = (
        (interruption.command_result,)
        if interruption.command_result is not None
        else tuple()
    )
    details: dict[str, object] = {
        "interruption": {
            "message": str(interruption),
            "signal": interruption.signum,
            "cleanup": interruption.cleanup,
        }
    }
    _record_step(
        ctx=ctx,
        action="stop",
        classification="infra-fail",
        decision=(
            "Live evaluator was interrupted; runtime subprocesses were cleaned up "
            "and the run can be resumed explicitly."
        ),
        plan="Convert interrupted live execution into explicit resumable evidence.",
        stage=_first_incomplete_stage(ctx),
        command_results=command_results,
        details=details,
    )
    _persist_state(
        ctx=ctx,
        status="interrupted-resumable",
        next_action="run-stage",
        current_stage=_first_incomplete_stage(ctx),
        completed_stages=_state_completed_stages(ctx.bundle_root),
        extra=details,
    )


def _finalize_reports(
    *,
    ctx: FlowContext,
    status: VerdictStatus,
    summary: str,
    verification_failed: bool,
    teardown_result: HarnessTeardownResult | None,
    teardown_error: BaseException | None,
) -> BlackBoxLiveE2EResult:
    _ensure_transcript_files(ctx)
    if teardown_error is not None:
        status = "infra-fail"
        summary = f"Teardown failed after black-box execution: {teardown_error}"
    _write_frontend_checkpoint_placeholders(ctx)
    _persist_state(
        ctx=ctx,
        status=status,
        next_action="finish" if status == "pass" else "stop",
        current_stage=None,
        completed_stages=_state_completed_stages(ctx.bundle_root),
        extra=_preserved_state_extras(ctx),
    )
    first_failure_note = (
        None if status == "pass" else _first_failure_from_steps(ctx, status=status)[1]
    )
    target_workspace_evidence_paths = _write_target_workspace_evidence(ctx)
    _record_terminal_decision_step(
        ctx=ctx,
        status=status,
        evidence_paths=target_workspace_evidence_paths,
    )
    runtime_log_path = _write_runtime_log_from_steps(ctx)
    _copy_attempt_jsonl_artifacts(
        ctx=ctx,
        filename=RUNTIME_JSONL_FILENAME,
        destination=ctx.bundle_root / RUNTIME_JSONL_FILENAME,
    )
    _copy_attempt_jsonl_artifacts(
        ctx=ctx,
        filename=EVENTS_JSONL_FILENAME,
        destination=ctx.bundle_root / EVENTS_JSONL_FILENAME,
    )
    _copy_attempt_jsonl_artifacts(
        ctx=ctx,
        filename=OPERATOR_REQUESTS_FILENAME,
        destination=ctx.bundle_root / OPERATOR_REQUESTS_FILENAME,
    )
    _copy_attempt_jsonl_artifacts(
        ctx=ctx,
        filename=OPERATOR_DECISIONS_FILENAME,
        destination=ctx.bundle_root / OPERATOR_DECISIONS_FILENAME,
    )
    _write_validator_report_from_steps(ctx=ctx, status=status, summary=summary)
    _write_log_analysis(ctx=ctx, status=status, first_failure_note=first_failure_note)
    stage_timing_payload = _stage_timing_payload_from_flow(
        ctx=ctx,
        teardown_result=teardown_result,
    )
    layout = build_result_bundle_layout_at_run_root(run_root=ctx.bundle_root)
    write_stage_timing_artifacts(layout=layout, payload=stage_timing_payload)
    (ctx.bundle_root / REPAIR_HISTORY_FILENAME).write_text(
        render_repair_history_markdown(stage_timing_payload),
        encoding="utf-8",
    )
    outcome = HarnessOutcome(
        aidd_exit_code=0 if status == "pass" else 1,
        verification_failed=verification_failed,
        blocked_by_questions=status == "blocked",
        infrastructure_failure=status == "infra-fail",
    )
    verdict = build_scenario_verdict_from_harness_outcome(
        scenario_id=ctx.scenario.scenario_id,
        run_id=ctx.run_id,
        runtime_id=ctx.runtime_id,
        outcome=outcome,
        summary=summary,
        artifact_links=(
            runtime_log_path.as_posix(),
            (ctx.bundle_root / VALIDATOR_REPORT_FILENAME).as_posix(),
            (ctx.bundle_root / FLOW_STEPS_FILENAME).as_posix(),
        ),
        first_failure_note=first_failure_note,
        verification_summary=(
            "verification command(s) passed"
            if not verification_failed
            else "verification command returned non-zero status"
        ),
    )
    write_scenario_verdict_markdown(path=ctx.bundle_root / VERDICT_FILENAME, verdict=verdict)
    next_flow_lineage = _write_next_flow_lineage_artifact(ctx=ctx, status=status)
    _, _, next_flow_checkpoint = _write_next_flow_checkpoint_artifacts(
        ctx=ctx,
        status=status,
        first_failure_note=first_failure_note,
        next_flow_lineage=next_flow_lineage,
    )
    _write_json(
        ctx.bundle_root / GRADER_FILENAME,
        _grader_payload(
            ctx=ctx,
            status=verdict.status,
            summary=summary,
            next_flow_checkpoint=next_flow_checkpoint,
            first_failure_note=first_failure_note,
        ),
    )
    write_eval_summary_markdown(
        path=ctx.bundle_root / SUMMARY_REPORT_FILENAME,
        scenario_rows=(
            build_scenario_summary_row(
                verdict=verdict,
                duration_seconds=max(time.monotonic() - ctx.started, 0.0),
                failure_boundary="none" if verdict.status == "pass" else "scenario-verification",
            ),
        ),
    )
    _write_harness_metadata(
        ctx=ctx,
        status=verdict.status,
    )
    _write_runtime_approval_analysis_placeholder(ctx)
    _write_run_transcript_from_flow(ctx=ctx, exit_code=0 if verdict.status == "pass" else 1)
    return BlackBoxLiveE2EResult(
        scenario_id=ctx.scenario.scenario_id,
        run_id=ctx.run_id,
        runtime_id=ctx.runtime_id,
        status=verdict.status,
        bundle_root=ctx.bundle_root,
        flow_report_path=ctx.bundle_root / FLOW_REPORT_FILENAME,
        verdict_path=ctx.bundle_root / VERDICT_FILENAME,
        summary_path=ctx.bundle_root / SUMMARY_REPORT_FILENAME,
        first_failure_note=first_failure_note,
        operator_action_request_path=(
            ctx.bundle_root / OPERATOR_REQUEST_MARKDOWN_FILENAME
            if (ctx.bundle_root / OPERATOR_REQUEST_MARKDOWN_FILENAME).exists()
            else None
        ),
    )


def _awaiting_quality_review_result(ctx: FlowContext) -> BlackBoxLiveE2EResult:
    _ensure_transcript_files(ctx)
    _write_runtime_log_from_steps(ctx)
    _write_flow_report(ctx)
    return BlackBoxLiveE2EResult(
        scenario_id=ctx.scenario.scenario_id,
        run_id=ctx.run_id,
        runtime_id=ctx.runtime_id,
        status="awaiting-quality-review",
        bundle_root=ctx.bundle_root,
        flow_report_path=ctx.bundle_root / FLOW_REPORT_FILENAME,
        verdict_path=ctx.bundle_root / VERDICT_FILENAME,
        summary_path=ctx.bundle_root / SUMMARY_REPORT_FILENAME,
        first_failure_note=None,
        operator_action_request_path=None,
        quality_review_request_path=_quality_review_request_path_from_state(ctx),
    )


def _manual_quality_stop_result(ctx: FlowContext) -> BlackBoxLiveE2EResult:
    _ensure_transcript_files(ctx)
    _write_runtime_log_from_steps(ctx)
    _write_flow_report(ctx)
    return BlackBoxLiveE2EResult(
        scenario_id=ctx.scenario.scenario_id,
        run_id=ctx.run_id,
        runtime_id=ctx.runtime_id,
        status="manual-quality-stop",
        bundle_root=ctx.bundle_root,
        flow_report_path=ctx.bundle_root / FLOW_REPORT_FILENAME,
        verdict_path=ctx.bundle_root / VERDICT_FILENAME,
        summary_path=ctx.bundle_root / SUMMARY_REPORT_FILENAME,
        first_failure_note="Manual stage quality audit chose `stop-not-counted`.",
        operator_action_request_path=None,
        quality_review_request_path=_quality_review_request_path_from_state(ctx),
    )


def _write_run_transcript_from_flow(*, ctx: FlowContext, exit_code: int) -> Path:
    result = _synthetic_aidd_run_result(ctx, exit_code=exit_code)
    return _write_step_transcript(
        path=ctx.bundle_root / RUN_TRANSCRIPT_FILENAME,
        step="run",
        transcripts=(result.command_transcript,),
        extra={
            "exit_code": result.exit_code,
            "runtime_id": result.runtime_id,
            "timed_out": result.timed_out,
            "timeout_seconds": result.timeout_seconds,
            "timeout_policy": _timeout_policy_payload(ctx),
            "work_item": result.work_item,
        },
    )


def _blocked_result(ctx: FlowContext) -> BlackBoxLiveE2EResult:
    summary = "Black-box live E2E is blocked waiting for operator-agent input."
    _ensure_transcript_files(ctx)
    _write_frontend_checkpoint_placeholders(ctx)
    _write_runtime_log_from_steps(ctx)
    _write_validator_report_from_steps(ctx=ctx, status="blocked", summary=summary)
    first_failure_note = _first_failure_from_steps(ctx, status="blocked")[1]
    _write_log_analysis(
        ctx=ctx,
        status="blocked",
        first_failure_note=first_failure_note,
    )
    outcome = HarnessOutcome(
        aidd_exit_code=1,
        verification_failed=True,
        blocked_by_questions=True,
        infrastructure_failure=False,
    )
    verdict = build_scenario_verdict_from_harness_outcome(
        scenario_id=ctx.scenario.scenario_id,
        run_id=ctx.run_id,
        runtime_id=ctx.runtime_id,
        outcome=outcome,
        summary=summary,
        artifact_links=(
            (ctx.bundle_root / RUNTIME_LOG_FILENAME).as_posix(),
            (ctx.bundle_root / VALIDATOR_REPORT_FILENAME).as_posix(),
            (ctx.bundle_root / FLOW_STEPS_FILENAME).as_posix(),
        ),
        first_failure_note=first_failure_note,
        verification_summary="blocked waiting for answers",
    )
    write_scenario_verdict_markdown(path=ctx.bundle_root / VERDICT_FILENAME, verdict=verdict)
    stage_timing_payload = _stage_timing_payload_from_flow(
        ctx=ctx,
        teardown_result=None,
    )
    layout = build_result_bundle_layout_at_run_root(run_root=ctx.bundle_root)
    write_stage_timing_artifacts(layout=layout, payload=stage_timing_payload)
    (ctx.bundle_root / REPAIR_HISTORY_FILENAME).write_text(
        render_repair_history_markdown(stage_timing_payload),
        encoding="utf-8",
    )
    _write_runtime_approval_analysis_placeholder(ctx)
    _persist_state(
        ctx=ctx,
        status="blocked",
        next_action="answer-questions",
        current_stage=_state_current_stage(ctx.bundle_root),
        completed_stages=_state_completed_stages(ctx.bundle_root),
        extra=_preserved_state_extras(ctx),
    )
    target_workspace_evidence_paths = _write_target_workspace_evidence(ctx)
    next_flow_lineage = _write_next_flow_lineage_artifact(ctx=ctx, status="blocked")
    _, _, next_flow_checkpoint = _write_next_flow_checkpoint_artifacts(
        ctx=ctx,
        status="blocked",
        first_failure_note=first_failure_note,
        next_flow_lineage=next_flow_lineage,
    )
    _record_terminal_decision_step(
        ctx=ctx,
        status="blocked",
        evidence_paths=target_workspace_evidence_paths,
    )
    _write_harness_metadata(
        ctx=ctx,
        status="blocked",
    )
    _write_json(
        ctx.bundle_root / GRADER_FILENAME,
        _grader_payload(
            ctx=ctx,
            status="blocked",
            summary=summary,
            next_flow_checkpoint=next_flow_checkpoint,
            first_failure_note=first_failure_note,
        ),
    )
    write_eval_summary_markdown(
        path=ctx.bundle_root / SUMMARY_REPORT_FILENAME,
        scenario_rows=(
            build_scenario_summary_row(
                verdict=verdict,
                duration_seconds=max(time.monotonic() - ctx.started, 0.0),
                failure_boundary="scenario-verification",
            ),
        ),
    )
    _write_run_transcript_from_flow(ctx=ctx, exit_code=1)
    return BlackBoxLiveE2EResult(
        scenario_id=ctx.scenario.scenario_id,
        run_id=ctx.run_id,
        runtime_id=ctx.runtime_id,
        status="blocked",
        bundle_root=ctx.bundle_root,
        flow_report_path=ctx.bundle_root / FLOW_REPORT_FILENAME,
        verdict_path=ctx.bundle_root / VERDICT_FILENAME,
        summary_path=ctx.bundle_root / SUMMARY_REPORT_FILENAME,
        first_failure_note=first_failure_note,
        operator_action_request_path=ctx.bundle_root / OPERATOR_REQUEST_MARKDOWN_FILENAME,
    )


def run_black_box_live_e2e(
    *,
    scenario_path: Path,
    runtime_id: str,
    work_root: Path | None = None,
    report_root: Path = Path(".aidd/reports/evals"),
    run_id: str | None = None,
    enable_next_flow_follow_up_proof: bool = False,
) -> BlackBoxLiveE2EResult:
    resolved_work_root = (work_root or _default_work_root()).resolve(strict=False)
    resolved_report_root = report_root.resolve(strict=False)
    ctx = _load_or_create_context(
        scenario_path=scenario_path,
        runtime_id=runtime_id,
        work_root=resolved_work_root,
        report_root=resolved_report_root,
        run_id=run_id,
        enable_next_flow_follow_up_proof=enable_next_flow_follow_up_proof,
    )
    try:
        with _live_interruption_handlers():
            return _run_black_box_live_e2e_with_context(ctx)
    except LiveE2EInterrupted as exc:
        _record_interruption(ctx=ctx, interruption=exc)
        raise


def _run_black_box_live_e2e_with_context(ctx: FlowContext) -> BlackBoxLiveE2EResult:
    status = _state_status(ctx.bundle_root)
    if status == "manual-quality-stop":
        return _manual_quality_stop_result(ctx)
    if status in TERMINAL_STATUSES:
        terminal_status = cast(VerdictStatus, status)
        return _finalize_reports(
            ctx=ctx,
            status=terminal_status,
            summary=(
                "Refreshed terminal black-box live E2E reports from existing "
                "execution artifact evidence."
            ),
            verification_failed=terminal_status != "pass",
            teardown_result=None,
            teardown_error=None,
        )
    quality_gate = _quality_review_gate(ctx)
    if quality_gate == "awaiting-quality-review":
        return _awaiting_quality_review_result(ctx)
    if quality_gate == "manual-quality-stop":
        return _manual_quality_stop_result(ctx)
    try:
        _prepare_target_repository(ctx)
    except Exception as exc:
        return _finalize_reports(
            ctx=ctx,
            status="infra-fail",
            summary=f"Target repository setup failed before black-box stage execution: {exc}",
            verification_failed=True,
            teardown_result=None,
            teardown_error=None,
        )
    try:
        _install_aidd(ctx)
    except Exception as exc:
        install_status: VerdictStatus = (
            "infra-fail" if _state_status(ctx.bundle_root) == "infra-fail" else "fail"
        )
        return _finalize_reports(
            ctx=ctx,
            status=install_status,
            summary=f"AIDD installation failed before black-box stage execution: {exc}",
            verification_failed=True,
            teardown_result=None,
            teardown_error=None,
        )
    try:
        _bootstrap_target_workspace(ctx)
    except Exception as exc:
        return _finalize_reports(
            ctx=ctx,
            status="infra-fail",
            summary=f"Public AIDD bootstrap failed before black-box stage execution: {exc}",
            verification_failed=True,
            teardown_result=None,
            teardown_error=None,
        )
    try:
        _run_setup(ctx)
    except HarnessSetupError as exc:
        return _finalize_reports(
            ctx=ctx,
            status="infra-fail",
            summary=f"Scenario setup failed before black-box stage execution: {exc}",
            verification_failed=True,
            teardown_result=None,
            teardown_error=None,
        )
    stage_classification = _run_stage_loop(ctx)
    if stage_classification == "awaiting-quality-review":
        return _awaiting_quality_review_result(ctx)
    if stage_classification == "manual-quality-stop":
        return _manual_quality_stop_result(ctx)
    if stage_classification == "blocked":
        return _blocked_result(ctx)
    if stage_classification == "fail":
        teardown_result, teardown_error = _run_teardown(ctx)
        return _finalize_reports(
            ctx=ctx,
            status="fail",
            summary="A public stage run failed during black-box live E2E execution.",
            verification_failed=True,
            teardown_result=teardown_result,
            teardown_error=teardown_error,
        )

    interview_flow_failure = _required_interview_flow_failure(ctx)
    if interview_flow_failure is not None:
        _record_step(
            ctx=ctx,
            action="verify",
            classification="fail",
            decision=interview_flow_failure,
            plan="Validate manifest-specific interview flow requirements.",
        )
        teardown_result, teardown_error = _run_teardown(ctx)
        return _finalize_reports(
            ctx=ctx,
            status="fail",
            summary="Required interview flow was not observed during black-box live E2E.",
            verification_failed=True,
            teardown_result=teardown_result,
            teardown_error=teardown_error,
        )

    verification_failed = False
    try:
        _run_verify(ctx)
    except HarnessVerificationError:
        verification_failed = True
        teardown_result, teardown_error = _run_teardown(ctx)
        return _finalize_reports(
            ctx=ctx,
            status="fail",
            summary="Scenario verification failed after public stage execution.",
            verification_failed=True,
            teardown_result=teardown_result,
            teardown_error=teardown_error,
        )

    teardown_result, teardown_error = _run_teardown(ctx)
    return _finalize_reports(
        ctx=ctx,
        status="pass",
        summary="Black-box live E2E completed through public stage and inspection surfaces.",
        verification_failed=verification_failed,
        teardown_result=teardown_result,
        teardown_error=teardown_error,
    )


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a black-box live E2E evaluator against an AIDD live manifest.",
    )
    parser.add_argument("scenario", help="Path to a live scenario manifest.")
    parser.add_argument("--runtime", required=True, help="Runtime id.")
    parser.add_argument(
        "--work-root",
        default=_default_work_root().as_posix(),
        help=(
            "Temp execution root for source snapshot, wheel build, install home, "
            "and target clone."
        ),
    )
    parser.add_argument(
        "--report-root",
        default=".aidd/reports/evals",
        help="Durable report root that receives one evidence bundle per run id.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Explicit blocked run id to resume; omitted always creates a fresh run.",
    )
    parser.add_argument(
        "--enable-next-flow-follow-up-proof",
        action="store_true",
        help=(
            "Manual-only option: create a follow-up draft from terminal QA findings "
            "and record next-flow-lineage.json without launching a child live flow."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = run_black_box_live_e2e(
            scenario_path=Path(args.scenario),
            runtime_id=str(args.runtime),
            work_root=Path(args.work_root),
            report_root=Path(args.report_root),
            run_id=None if args.run_id is None else str(args.run_id),
            enable_next_flow_follow_up_proof=bool(args.enable_next_flow_follow_up_proof),
        )
    except ValueError as exc:
        print(f"black-box live e2e: {exc}", file=sys.stderr)
        return 2
    except LiveE2EInterrupted as exc:
        print(f"black-box live e2e interrupted: {exc}", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"black-box live e2e failed: {exc}", file=sys.stderr)
        return 1

    print(
        "AIDD black-box live E2E: "
        f"scenario={result.scenario_id} runtime={result.runtime_id}"
    )
    print(f"Status: {result.status}")
    print(f"Run id: {result.run_id}")
    print(f"Bundle root: {result.bundle_root.as_posix()}")
    print(f"Flow report: {result.flow_report_path.as_posix()}")
    print(f"Verdict path: {result.verdict_path.as_posix()}")
    if result.operator_action_request_path is not None and result.status == "blocked":
        print(f"Operator action request: {result.operator_action_request_path.as_posix()}")
    if (
        result.quality_review_request_path is not None
        and result.status == "awaiting-quality-review"
    ):
        print(f"Required quality audit: {result.quality_review_request_path.as_posix()}")
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

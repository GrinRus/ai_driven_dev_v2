from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aidd.core.stages import STAGES
from aidd.evals.self_repair_probes import probes_for_stage, validate_probe_catalog

if TYPE_CHECKING:
    from aidd.harness.install_artifact import HarnessInstallResult
    from aidd.harness.result_bundle import ResultBundleLayout
    from aidd.harness.runner import (
        HarnessAiddRunResult,
        HarnessQualityResult,
        HarnessSetupResult,
        HarnessTeardownResult,
        HarnessVerificationResult,
    )
    from aidd.harness.scenarios import Scenario


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_utc_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _duration_seconds(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None:
        return None
    return max((end - start).total_seconds(), 0.0)


def _step_payload(
    *,
    name: str,
    duration_seconds: float,
    status: str,
    command_count: int = 0,
    exit_code: int | None = None,
    timed_out: bool = False,
    timeout_seconds: float | None = None,
) -> dict[str, object]:
    return {
        "command_count": command_count,
        "duration_seconds": duration_seconds,
        "exit_code": exit_code,
        "status": status,
        "step": name,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
    }


def _latest_run_root(*, workspace_root: Path | None, work_item: str) -> Path | None:
    if workspace_root is None:
        return None
    runs_root = workspace_root / "reports" / "runs" / work_item
    if not runs_root.exists() or not runs_root.is_dir():
        return None
    candidates = tuple(path for path in runs_root.iterdir() if path.is_dir())
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, path.name))[-1]


def _status_history_entries(stage_metadata: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_history = stage_metadata.get("status_history")
    if not isinstance(raw_history, list):
        return tuple()
    return tuple(entry for entry in raw_history if isinstance(entry, dict))


def _first_repair_reason_from_text(text: str) -> str | None:
    for line in text.splitlines():
        normalized = line.strip()
        if normalized.startswith("- `"):
            return normalized
    return None


def _fallback_repair_reason(work_item_stage_root: Path | None) -> str | None:
    if work_item_stage_root is None:
        return None
    repair_brief_path = work_item_stage_root / "repair-brief.md"
    if not repair_brief_path.exists():
        return None
    return (
        _first_repair_reason_from_text(
            repair_brief_path.read_text(encoding="utf-8", errors="replace")
        )
        or "repair brief present"
    )


def _repair_reason_for_attempt(
    *,
    stage_root: Path,
    attempt_number: int,
    work_item_stage_root: Path | None,
) -> str | None:
    if attempt_number <= 1:
        return None
    repair_context_path = (
        stage_root / "attempts" / f"attempt-{attempt_number:04d}" / "repair-context.md"
    )
    if repair_context_path.exists():
        reason = _first_repair_reason_from_text(
            repair_context_path.read_text(encoding="utf-8", errors="replace")
        )
        if reason is not None:
            return reason
        return "repair context present"
    return _fallback_repair_reason(work_item_stage_root)


_STATUS_HEADING_PATTERN = re.compile(r"^#{1,6}\s+Status\s*$", re.IGNORECASE | re.MULTILINE)
_STATUS_SECTION_PATTERN = re.compile(
    r"^#{1,6}\s+Status\s*\n+(?P<body>.*?)(?=\n#{1,6}\s+|\Z)",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
_CANONICAL_FAILURE_CODE_PATTERN = re.compile(r"- `(?P<code>[A-Z][A-Z0-9_-]+)`")


def _stage_result_status(stage_result_text: str) -> str | None:
    match = _STATUS_SECTION_PATTERN.search(stage_result_text)
    if match is None:
        return None
    body = match.group("body").strip().lower()
    for status in ("succeeded", "failed", "blocked", "needs-input"):
        if re.search(rf"\b{re.escape(status)}\b", body):
            return status
    return None


def _validator_report_has_open_findings(validator_report_text: str) -> bool:
    normalized = validator_report_text.lower()
    return (
        "verdict: `fail`" in normalized
        or "repair required for progression: yes" in normalized
        or "blocking issues: yes" in normalized
    )


def _first_validator_failure_code(work_item_stage_root: Path | None) -> str | None:
    if work_item_stage_root is None:
        return None
    validator_report_text = _read_text(work_item_stage_root / "validator-report.md")
    match = _CANONICAL_FAILURE_CODE_PATTERN.search(validator_report_text)
    return None if match is None else match.group("code")


def _terminal_docs_consistent(work_item_stage_root: Path | None) -> bool | None:
    if work_item_stage_root is None:
        return None

    stage_result_text = _read_text(work_item_stage_root / "stage-result.md")
    validator_report_text = _read_text(work_item_stage_root / "validator-report.md")
    repair_brief_text = _read_text(work_item_stage_root / "repair-brief.md")
    if not stage_result_text and not validator_report_text and not repair_brief_text:
        return None

    status_headings = _STATUS_HEADING_PATTERN.findall(stage_result_text)
    if len(status_headings) > 1:
        return False

    stage_status = _stage_result_status(stage_result_text)
    stage_result_normalized = stage_result_text.lower()
    if _validator_report_has_open_findings(validator_report_text):
        if stage_status == "succeeded":
            return False
        if "validator verdict: `pass`" in stage_result_normalized:
            return False

    repair_brief_normalized = repair_brief_text.lower()
    if (
        "repair-budget-exhausted" in repair_brief_normalized
        or "rerun allowed after this attempt: `no`" in repair_brief_normalized
        or "rerun allowed after this attempt: no" in repair_brief_normalized
    ) and stage_status != "failed":
        return False

    return True


def _attempt_runtime_exit(stage_root: Path, attempt_number: int) -> dict[str, Any]:
    attempt_path = stage_root / "attempts" / f"attempt-{attempt_number:04d}" / "runtime-exit.json"
    return _read_json(attempt_path) if attempt_path.exists() else {}


def _stage_attempts(
    stage_root: Path,
    stage_metadata: dict[str, Any],
    work_item_stage_root: Path | None = None,
) -> tuple[dict[str, object], ...]:
    history = _status_history_entries(stage_metadata)
    attempts: list[dict[str, object]] = []
    attempt_number = 0
    for index, entry in enumerate(history):
        if entry.get("status") != "executing":
            continue

        attempt_number += 1
        started_at = _parse_utc_timestamp(entry.get("changed_at_utc"))
        runtime_finished_at: datetime | None = None
        validation_result = "unknown"
        terminal_status = str(stage_metadata.get("status", "unknown"))
        for later in history[index + 1 :]:
            later_status = str(later.get("status", "")).strip()
            if runtime_finished_at is None and later_status == "validating":
                runtime_finished_at = _parse_utc_timestamp(later.get("changed_at_utc"))
                continue
            if runtime_finished_at is not None and later_status != "validating":
                validation_result = later_status or "unknown"
                break

        runtime_exit = _attempt_runtime_exit(stage_root, attempt_number)
        attempts.append(
            {
                "attempt": attempt_number,
                "repair_reason": _repair_reason_for_attempt(
                    stage_root=stage_root,
                    attempt_number=attempt_number,
                    work_item_stage_root=work_item_stage_root,
                ),
                "runtime_exit_classification": runtime_exit.get("exit_classification"),
                "runtime_exit_code": runtime_exit.get("exit_code"),
                "runtime_seconds": _duration_seconds(started_at, runtime_finished_at),
                "timed_out": str(runtime_exit.get("exit_classification")) == "timeout",
                "terminal_status": terminal_status,
                "validation_result": validation_result,
            }
        )
    return tuple(attempts)


def _stage_scope(scenario: Scenario) -> tuple[str, ...]:
    start = scenario.run.stage_start or STAGES[0]
    end = scenario.run.stage_end or STAGES[-1]
    if start not in STAGES or end not in STAGES:
        return STAGES
    start_index = STAGES.index(start)
    end_index = STAGES.index(end)
    if start_index > end_index:
        return STAGES
    return STAGES[start_index : end_index + 1]


def build_stage_timing_payload(
    *,
    scenario: Scenario,
    run_id: str,
    runtime_id: str,
    work_item: str,
    workspace_root: Path | None,
    total_duration_seconds: float,
    install_result: HarnessInstallResult | None = None,
    setup_result: HarnessSetupResult | None = None,
    aidd_run_result: HarnessAiddRunResult | None = None,
    verification_result: HarnessVerificationResult | None = None,
    quality_result: HarnessQualityResult | None = None,
    teardown_result: HarnessTeardownResult | None = None,
) -> dict[str, object]:
    latest_run_root = _latest_run_root(workspace_root=workspace_root, work_item=work_item)
    stage_payloads: list[dict[str, object]] = []
    stage_attempt_counts: dict[str, int] = {}
    for stage in _stage_scope(scenario):
        stage_root = None if latest_run_root is None else latest_run_root / "stages" / stage
        metadata_path = None if stage_root is None else stage_root / "stage-metadata.json"
        metadata = _read_json(metadata_path) if metadata_path is not None else {}
        work_item_stage_root = (
            None
            if workspace_root is None
            else workspace_root / "workitems" / work_item / "stages" / stage
        )
        stage_reached = bool(metadata)
        attempts = (
            tuple()
            if stage_root is None or not stage_reached
            else _stage_attempts(
                stage_root,
                metadata,
                work_item_stage_root=work_item_stage_root,
            )
        )
        stage_attempt_counts[stage] = len(attempts)
        stage_payloads.append(
            {
                "attempt_count": len(attempts),
                "attempts": list(attempts),
                "final_failure_code": (
                    _first_validator_failure_code(work_item_stage_root)
                    if stage_reached
                    else None
                ),
                "stage": stage,
                "status": (
                    metadata.get("status", "not-reached") if stage_reached else "not-reached"
                ),
                "status_history": (
                    list(_status_history_entries(metadata)) if stage_reached else []
                ),
                "terminal_docs_consistent": (
                    _terminal_docs_consistent(work_item_stage_root)
                    if stage_reached
                    else None
                ),
            }
        )

    return {
        "run_id": run_id,
        "runtime_id": runtime_id,
        "scenario_id": scenario.scenario_id,
        "stage_scope": list(_stage_scope(scenario)),
        "stages": stage_payloads,
        "steps": [
            _step_payload(
                name="install",
                duration_seconds=install_result.duration_seconds if install_result else 0.0,
                status="completed" if install_result else "skipped",
                command_count=len(install_result.command_transcripts) if install_result else 0,
            ),
            _step_payload(
                name="setup",
                duration_seconds=setup_result.duration_seconds if setup_result else 0.0,
                status="completed" if setup_result else "skipped",
                command_count=len(setup_result.command_transcripts) if setup_result else 0,
            ),
            _step_payload(
                name="run",
                duration_seconds=aidd_run_result.duration_seconds if aidd_run_result else 0.0,
                status="completed" if aidd_run_result else "skipped",
                command_count=1 if aidd_run_result else 0,
                exit_code=aidd_run_result.exit_code if aidd_run_result else None,
                timed_out=aidd_run_result.timed_out if aidd_run_result else False,
                timeout_seconds=aidd_run_result.timeout_seconds if aidd_run_result else None,
            ),
            _step_payload(
                name="verify",
                duration_seconds=(
                    verification_result.duration_seconds if verification_result else 0.0
                ),
                status="completed" if verification_result else "skipped",
                command_count=(
                    len(verification_result.command_transcripts)
                    if verification_result
                    else 0
                ),
            ),
            _step_payload(
                name="quality",
                duration_seconds=quality_result.duration_seconds if quality_result else 0.0,
                status="completed" if quality_result else "skipped",
                command_count=len(quality_result.command_transcripts) if quality_result else 0,
            ),
            _step_payload(
                name="teardown",
                duration_seconds=teardown_result.duration_seconds if teardown_result else 0.0,
                status="completed" if teardown_result else "skipped",
                command_count=len(teardown_result.command_transcripts) if teardown_result else 0,
            ),
        ],
        "summary": {
            "stage_attempt_counts": stage_attempt_counts,
            "total_duration_seconds": total_duration_seconds,
            "workspace_run_root": None if latest_run_root is None else latest_run_root.as_posix(),
        },
        "work_item": work_item,
    }


def _format_seconds(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.3f}"
    return "n/a"


def _format_optional(value: object) -> str:
    return "n/a" if value is None else str(value)


def render_stage_timing_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Stage Timing",
        "",
        "## Harness Steps",
        "",
        "| Step | Status | Duration (s) | Commands | Exit Code | Timeout (s) |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    raw_steps = payload.get("steps", [])
    step_items = raw_steps if isinstance(raw_steps, list) else []
    for raw_step in step_items:
        if not isinstance(raw_step, dict):
            continue
        lines.append(
            "| "
            f"`{raw_step.get('step', 'unknown')}` | "
            f"`{raw_step.get('status', 'unknown')}` | "
            f"{_format_seconds(raw_step.get('duration_seconds'))} | "
            f"{raw_step.get('command_count', 0)} | "
            f"{raw_step.get('exit_code', 'n/a')} | "
            f"{_format_seconds(raw_step.get('timeout_seconds'))} |"
        )

    lines.extend(
        (
            "",
            "## Stage Attempts",
            "",
            (
                "| Stage | Attempt | Runtime (s) | Runtime Exit | Timeout | "
                "Validation Result | Repair Reason | Terminal Status | Terminal Docs |"
            ),
            "| --- | ---: | ---: | --- | --- | --- | --- | --- | --- |",
        )
    )
    raw_stages = payload.get("stages", [])
    stage_items = raw_stages if isinstance(raw_stages, list) else []
    for raw_stage in stage_items:
        if not isinstance(raw_stage, dict):
            continue
        attempts = raw_stage.get("attempts")
        if not isinstance(attempts, list) or not attempts:
            lines.append(
                "| "
                f"`{raw_stage.get('stage', 'unknown')}` | "
                "0 | n/a | n/a | n/a | `not-reached` | n/a | "
                f"`{raw_stage.get('status', 'not-reached')}` | "
                f"`{_format_optional(raw_stage.get('terminal_docs_consistent'))}` |"
            )
            continue
        for raw_attempt in attempts:
            if not isinstance(raw_attempt, dict):
                continue
            repair_reason = str(raw_attempt.get("repair_reason") or "n/a").replace("|", "\\|")
            lines.append(
                "| "
                f"`{raw_stage.get('stage', 'unknown')}` | "
                f"{raw_attempt.get('attempt', 'n/a')} | "
                f"{_format_seconds(raw_attempt.get('runtime_seconds'))} | "
                f"`{raw_attempt.get('runtime_exit_classification', 'unknown')}`/"
                f"`{raw_attempt.get('runtime_exit_code', 'n/a')}` | "
                f"`{raw_attempt.get('timed_out', False)}` | "
                f"`{raw_attempt.get('validation_result', 'unknown')}` | "
                f"{repair_reason} | "
                f"`{raw_attempt.get('terminal_status', 'unknown')}` | "
                f"`{_format_optional(raw_stage.get('terminal_docs_consistent'))}` |"
            )
    lines.append("")
    return "\n".join(lines)


def render_self_repair_matrix_markdown(payload: dict[str, object]) -> str:
    matrix_payload = (
        payload
        if isinstance(payload.get("matrix"), list)
        else build_self_repair_matrix_payload(payload)
    )
    lines = [
        "# Self-Repair Matrix",
        "",
        (
            "| Stage | Attempts Used | Initial Result | Repair Success | "
            "Avg Runtime (s) | Final Status | Final Failure | Terminal Docs |"
        ),
        "| --- | ---: | --- | --- | ---: | --- | --- | --- |",
    ]
    raw_rows = matrix_payload.get("matrix", [])
    row_items = raw_rows if isinstance(raw_rows, list) else []
    for raw_row in row_items:
        if not isinstance(raw_row, dict):
            continue
        repair_success_raw = raw_row.get("repair_success")
        repair_success = "n/a" if repair_success_raw is None else str(bool(repair_success_raw))
        lines.append(
            "| "
            f"`{raw_row.get('stage', 'unknown')}` | "
            f"{raw_row.get('attempts_used', 0)} | "
            f"`{raw_row.get('initial_verdict', 'unknown')}` | "
            f"`{repair_success}` | "
            f"{_format_seconds(raw_row.get('average_attempt_runtime_seconds'))} | "
            f"`{raw_row.get('final_status', 'not-reached')}` | "
            f"`{_format_optional(raw_row.get('final_failure_code'))}` | "
            f"`{_format_optional(raw_row.get('terminal_docs_consistent'))}` |"
        )

    lines.extend(
        (
            "",
            "## Deterministic Probe Coverage",
            "",
            (
                "| Stage | Probe | Initial Verdict | Repair Success | Attempts Used | "
                "Final Failure | Terminal Docs | Evaluation Source | Description |"
            ),
            "| --- | --- | --- | --- | ---: | --- | --- | --- | --- |",
        )
    )
    for raw_row in row_items:
        if not isinstance(raw_row, dict):
            continue
        raw_probes = raw_row.get("probes")
        probes = raw_probes if isinstance(raw_probes, list) else []
        for raw_probe in probes:
            if not isinstance(raw_probe, dict):
                continue
            description = str(raw_probe.get("description", "")).replace("|", "\\|")
            lines.append(
                "| "
                f"`{raw_probe.get('stage', raw_row.get('stage', 'unknown'))}` | "
                f"`{raw_probe.get('probe_id', 'unknown')}` | "
                f"`{raw_probe.get('initial_verdict', 'unknown')}` | "
                f"`{_format_optional(raw_probe.get('repair_success'))}` | "
                f"{raw_probe.get('attempts_used', 0)} | "
                f"`{_format_optional(raw_probe.get('final_failure_code'))}` | "
                f"`{_format_optional(raw_probe.get('terminal_docs_consistent'))}` | "
                f"`{raw_probe.get('evaluation_source', 'unknown')}` | "
                f"{description} |"
            )
    lines.append("")
    return "\n".join(lines)


def build_self_repair_matrix_payload(payload: dict[str, object]) -> dict[str, object]:
    validate_probe_catalog()
    raw_stages = payload.get("stages", [])
    stage_items = raw_stages if isinstance(raw_stages, list) else []
    matrix_rows: list[dict[str, object]] = []
    for raw_stage in stage_items:
        if not isinstance(raw_stage, dict):
            continue
        attempts = raw_stage.get("attempts")
        attempt_dicts = (
            [item for item in attempts if isinstance(item, dict)]
            if isinstance(attempts, list)
            else []
        )
        runtimes = [
            float(item["runtime_seconds"])
            for item in attempt_dicts
            if isinstance(item.get("runtime_seconds"), (int, float))
        ]
        initial_verdict = (
            str(attempt_dicts[0].get("validation_result", "unknown"))
            if attempt_dicts
            else "not-reached"
        )
        final_status = str(raw_stage.get("status", "not-reached"))
        repair_success = (
            True
            if len(attempt_dicts) > 1 and final_status == "succeeded"
            else False
            if len(attempt_dicts) > 1
            else None
        )
        final_failure_code = (
            None
            if final_status == "succeeded"
            else raw_stage.get("final_failure_code") or final_status
        )
        stage_name = str(raw_stage.get("stage", "unknown"))
        terminal_docs_consistent = raw_stage.get("terminal_docs_consistent")
        probes = [
            {
                "attempts_used": len(attempt_dicts),
                "description": probe.description,
                "evaluation_source": (
                    "run-artifact-observation" if attempt_dicts else "not-run"
                ),
                "final_failure_code": final_failure_code,
                "initial_verdict": initial_verdict,
                "probe_id": probe.probe_id,
                "repair_success": repair_success,
                "stage": probe.stage,
                "terminal_docs_consistent": terminal_docs_consistent,
            }
            for probe in probes_for_stage(stage_name)
        ]
        matrix_rows.append(
            {
                "attempts_used": len(attempt_dicts),
                "average_attempt_runtime_seconds": (
                    sum(runtimes) / len(runtimes) if runtimes else None
                ),
                "final_failure_code": final_failure_code,
                "final_status": final_status,
                "initial_verdict": initial_verdict,
                "probes": probes,
                "repair_success": repair_success,
                "stage": stage_name,
                "terminal_docs_consistent": terminal_docs_consistent,
            }
        )
    deterministic_probe_count = 0
    for row in matrix_rows:
        raw_probes = row.get("probes")
        if isinstance(raw_probes, list):
            deterministic_probe_count += len(raw_probes)
    return {
        "deterministic_probe_count": deterministic_probe_count,
        "matrix": matrix_rows,
        "run_id": payload.get("run_id"),
        "runtime_id": payload.get("runtime_id"),
        "scenario_id": payload.get("scenario_id"),
    }


def write_stage_timing_artifacts(
    *,
    layout: ResultBundleLayout,
    payload: dict[str, object],
) -> tuple[Path, Path, Path, Path]:
    self_repair_matrix_payload = build_self_repair_matrix_payload(payload)
    layout.stage_timing_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    layout.stage_timing_markdown_path.write_text(
        render_stage_timing_markdown(payload),
        encoding="utf-8",
    )
    layout.self_repair_matrix_json_path.write_text(
        json.dumps(self_repair_matrix_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    layout.self_repair_matrix_path.write_text(
        render_self_repair_matrix_markdown(self_repair_matrix_payload),
        encoding="utf-8",
    )
    return (
        layout.stage_timing_json_path,
        layout.stage_timing_markdown_path,
        layout.self_repair_matrix_json_path,
        layout.self_repair_matrix_path,
    )


__all__ = [
    "build_stage_timing_payload",
    "build_self_repair_matrix_payload",
    "render_self_repair_matrix_markdown",
    "render_stage_timing_markdown",
    "write_stage_timing_artifacts",
]

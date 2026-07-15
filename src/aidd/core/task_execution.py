from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from aidd.core.allowed_write_scope import (
    AllowedWriteScopeError,
    resolve_allowed_write_scope,
)
from aidd.core.identifiers import contained_component_path
from aidd.core.run_store import (
    load_stage_metadata,
    next_attempt_number,
    persist_stage_status,
    run_attempt_root,
    run_stage_root,
)
from aidd.core.stage_models import StageExecutionState, StageOutputDiscovery
from aidd.core.state_machine import StageState
from aidd.core.task_attempt_lifecycle import (
    TaskExecutionContext,
    TaskResumeBlockedError,
    complete_task_attempt,
    copy_interview_evidence,
    existing_attempts,
    load_task_execution_plan,
    prepare_task_attempt,
    published_tasklist_path,
    reconcile_staging_attempts,
    reconcile_task_execution_state,
    write_task_selection_context,
)
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    persist_task_ledger,
)
from aidd.core.task_plan import TaskPlan
from aidd.validators.models import ValidationFinding, ValidationIssueLocation


@dataclass(frozen=True, slots=True)
class TaskFinalizationContext:
    ledger: TaskLedger
    attempt_path: Path
    attempt_number: int


def _finalization_attempts_root(*, workspace_root: Path, work_item: str, run_id: str) -> Path:
    finalization_root = contained_component_path(
        run_stage_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        ),
        "finalization",
        boundary_root=workspace_root,
        label="finalization directory",
    )
    return contained_component_path(
        finalization_root,
        "attempts",
        boundary_root=workspace_root,
        label="finalization attempts directory",
    )


def prepare_task_finalization(
    *, workspace_root: Path, work_item: str, run_id: str, ledger: TaskLedger
) -> TaskFinalizationContext:
    if not ledger.all_succeeded():
        raise ValueError("Cannot finalize implementation before every task succeeds.")
    if ledger.finalization.status is TaskFinalizationStatus.SUCCEEDED:
        raise ValueError("Implementation task finalization has already succeeded.")
    if ledger.finalization.status is TaskFinalizationStatus.EXECUTING:
        ledger = ledger.transition_finalization(
            TaskFinalizationStatus.FAILED,
            blocker="Aggregate finalization was interrupted before a terminal result.",
        )
    attempts_root = _finalization_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    reconcile_staging_attempts(attempts_root, task_id="finalization")
    existing = existing_attempts(attempts_root)
    number = max((ledger.finalization.attempt_count, *(item for item, _ in existing))) + 1
    attempts_root.mkdir(parents=True, exist_ok=True)
    staging = attempts_root / f".attempt-{number:04d}-{uuid4().hex}.staging"
    staging.mkdir()
    (staging / "finalization-state.json").write_text(
        json.dumps(
            {"schema_version": 1, "attempt_number": number, "status": "executing"},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    attempt_path = contained_component_path(
        attempts_root,
        f"attempt-{number:04d}",
        boundary_root=workspace_root,
        label="finalization attempt id",
    )
    staging.replace(attempt_path)
    relative_path = attempt_path.relative_to(workspace_root).as_posix()
    ledger = ledger.transition_finalization(
        TaskFinalizationStatus.EXECUTING,
        attempt_number=number,
        latest_attempt_path=relative_path,
    )
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    return TaskFinalizationContext(
        ledger=ledger,
        attempt_path=attempt_path,
        attempt_number=number,
    )


def complete_task_finalization(
    *,
    context: TaskFinalizationContext,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    succeeded: bool,
    blocker: str | None = None,
) -> TaskLedger:
    status = TaskFinalizationStatus.SUCCEEDED if succeeded else TaskFinalizationStatus.FAILED
    ledger = context.ledger.transition_finalization(status, blocker=blocker)
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    (context.attempt_path / "finalization-state.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "attempt_number": context.attempt_number,
                "status": status.value,
                "blocker": blocker,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return ledger


def _git_status(project_root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        (
            "git",
            "-C",
            project_root.as_posix(),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ()
    return tuple(line for line in completed.stdout.splitlines() if line.strip())


def _hash_repository_file(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(b"symlink\0")
        digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
        return digest.hexdigest()
    if not path.exists():
        return "missing"
    if not path.is_file():
        return "non-file"
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repository_file_snapshot(project_root: Path) -> dict[str, str]:
    completed = subprocess.run(
        (
            "git",
            "-C",
            project_root.as_posix(),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ),
        check=False,
        capture_output=True,
    )
    snapshot: dict[str, str] = {}
    if completed.returncode != 0:
        for candidate in project_root.rglob("*"):
            relative = candidate.relative_to(project_root)
            if not relative.parts or relative.parts[0] in {".aidd", ".git"}:
                continue
            if candidate.is_file() or candidate.is_symlink():
                snapshot[relative.as_posix()] = _hash_repository_file(candidate)
        return snapshot
    for raw_path in completed.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative_path = raw_path.decode("utf-8", errors="surrogateescape")
        if relative_path == ".aidd" or relative_path.startswith(".aidd/"):
            continue
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Repository snapshot path escapes project root: {relative_path}.")
        snapshot[relative_path] = _hash_repository_file(project_root / relative_path)
    return snapshot


def _snapshot_payload(*, project_root: Path, task_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "task_id": task_id,
        "status": list(_git_status(project_root)),
        "files": _repository_file_snapshot(project_root),
    }


def prepare_task_execution(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    task_id: str,
    project_root: Path,
) -> TaskExecutionContext:
    return prepare_task_attempt(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        task_id=task_id,
        project_root=project_root,
        repository_baseline=_snapshot_payload,
    )


def _snapshot_global_attempts(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> None:
    end = next_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
    )
    for attempt_number in range(context.global_attempt_start, end):
        source = run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
            attempt_number=attempt_number,
        )
        if source.exists():
            destination = context.task_attempt_path / f"stage-attempt-{attempt_number:04d}"
            shutil.copytree(source, destination)
            input_bundle = destination / "input-bundle.md"
            if (
                input_bundle.exists()
                and not (context.task_attempt_path / "input-bundle.md").exists()
            ):
                shutil.copy2(input_bundle, context.task_attempt_path / "input-bundle.md")
            runtime_log = destination / "runtime.log"
            if runtime_log.exists():
                shutil.copy2(runtime_log, context.task_attempt_path / "runtime.log")
            repair_context = destination / "repair-context.md"
            if repair_context.exists():
                shutil.copy2(repair_context, context.task_attempt_path / "repair-context.md")


def _reported_touched_paths(report: str) -> tuple[str, ...]:
    paths: list[str] = []
    for line in _section(report, "Touched files").splitlines():
        if not line.strip().startswith("-") or line.strip().casefold() == "- none":
            continue
        match = re.search(r"`([^`]+)`", line)
        if match is not None:
            paths.append(match.group(1).strip().strip("/"))
    return tuple(dict.fromkeys(paths))


def _task_diff_evidence(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    project_root: Path,
    report: str | None,
) -> tuple[dict[str, object], tuple[str, ...]]:
    baseline_payload = json.loads(
        (context.task_attempt_path / "repository-baseline.json").read_text(encoding="utf-8")
    )
    baseline_files = baseline_payload.get("files", {})
    if not isinstance(baseline_files, dict):
        baseline_files = {}
    final_files = _repository_file_snapshot(project_root)
    observed = tuple(
        sorted(
            path
            for path in set(baseline_files) | set(final_files)
            if baseline_files.get(path) != final_files.get(path)
        )
    )
    reported = _reported_touched_paths(report or "")
    issues: list[str] = []
    missing_from_report = sorted(set(observed) - set(reported))
    unsupported_report_paths = sorted(set(reported) - set(observed))
    if missing_from_report:
        issues.append(
            "Observed task-local paths missing from implementation report: "
            + ", ".join(missing_from_report)
            + "."
        )
    if unsupported_report_paths:
        issues.append(
            "Implementation report paths absent from the task-local diff: "
            + ", ".join(unsupported_report_paths)
            + "."
        )
    allowed_scope = None
    try:
        allowed_scope = resolve_allowed_write_scope(workspace_root, work_item)
    except AllowedWriteScopeError as exc:
        issues.extend(f"Allowed write scope: {issue}" for issue in exc.issues)
    allowed_scope_paths = list(allowed_scope.prefixes) if allowed_scope is not None else []

    def _globally_allowed(path: str) -> bool:
        if allowed_scope is None:
            return True
        try:
            return allowed_scope.allows(path)
        except AllowedWriteScopeError:
            return False

    task_scope_paths = list(context.task.scope_paths)
    task_scope_outside_global = sorted(
        path
        for path in task_scope_paths
        if allowed_scope is not None and not _globally_allowed(path)
    )
    if task_scope_outside_global:
        issues.append(
            "Task-local scope is outside the global allowed write scope: "
            + ", ".join(task_scope_outside_global)
            + "."
        )
    out_of_scope = sorted(
        path
        for path in observed
        if not any(
            path == allowed or path.startswith(f"{allowed}/") for allowed in task_scope_paths
        )
        or (allowed_scope is not None and not _globally_allowed(path))
    )
    if out_of_scope:
        issues.append(
            "Observed task-local paths outside allowed write scope: "
            + ", ".join(out_of_scope)
            + "."
        )
    return (
        {
            "schema_version": 1,
            "task_id": context.task.id,
            "observed_touched_paths": list(observed),
            "reported_touched_paths": list(reported),
            "task_scope_paths": task_scope_paths,
            "allowed_scope_paths": allowed_scope_paths,
            "issues": issues,
        },
        tuple(issues),
    )


def task_validation_findings(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    project_root: Path,
    execution_state: StageExecutionState,
    discovery: StageOutputDiscovery,
) -> tuple[ValidationFinding, ...]:
    del discovery
    report_path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "implementation-report.md"
    )
    report = report_path.read_text(encoding="utf-8") if report_path.exists() else None
    payload, issues = _task_diff_evidence(
        context=context,
        workspace_root=workspace_root,
        work_item=work_item,
        project_root=project_root,
        report=report,
    )
    (execution_state.attempt_path / "task-diff.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    location = ValidationIssueLocation(
        workspace_relative_path=report_path.relative_to(workspace_root).as_posix()
    )
    return tuple(
        ValidationFinding(
            code=(
                "SEM-TASK-SCOPE-MISMATCH"
                if "scope" in issue.casefold()
                else "SEM-TASK-DIFF-MISMATCH"
            ),
            message=issue,
            severity="high",
            location=location,
        )
        for issue in issues
    )


def complete_task_execution(
    *,
    context: TaskExecutionContext,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    project_root: Path,
    succeeded: bool,
    blocker: str | None = None,
) -> TaskLedger:
    _snapshot_global_attempts(
        context=context,
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
    )
    implementation_report = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "implementation-report.md"
    )
    implementation_report_text: str | None = None
    if implementation_report.exists():
        implementation_report_text = implementation_report.read_text(encoding="utf-8")
        shutil.copy2(
            implementation_report,
            context.task_attempt_path / "implementation-report.md",
        )
    implement_stage_root = implementation_report.parent
    copy_interview_evidence(implement_stage_root, context.task_attempt_path)
    final_status = _snapshot_payload(project_root=project_root, task_id=context.task.id)
    (context.task_attempt_path / "repository-final.json").write_text(
        json.dumps(final_status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    task_diff, task_diff_issues = _task_diff_evidence(
        context=context,
        workspace_root=workspace_root,
        work_item=work_item,
        project_root=project_root,
        report=implementation_report_text,
    )
    (context.task_attempt_path / "task-diff.json").write_text(
        json.dumps(task_diff, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if succeeded and task_diff_issues:
        succeeded = False
        blocker = " ".join(task_diff_issues)
    status = TaskExecutionStatus.SUCCEEDED if succeeded else TaskExecutionStatus.FAILED
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
    )
    if not succeeded and metadata is not None and metadata.status == StageState.BLOCKED.value:
        status = TaskExecutionStatus.BLOCKED
    ledger = complete_task_attempt(
        context=context,
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        status=status,
        blocker=blocker,
    )
    if not ledger.all_succeeded():
        persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
            status=(StageState.PENDING.value if succeeded else StageState.BLOCKED.value),
        )
    return ledger


def _section(markdown: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        markdown,
        flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group("body").strip() if match is not None else ""


def render_aggregate_implementation_report(
    *,
    plan: TaskPlan,
    ledger: TaskLedger,
    workspace_root: Path,
) -> str:
    if not ledger.all_succeeded():
        raise ValueError("Cannot aggregate implementation evidence before every task succeeds.")
    summaries: list[str] = []
    touched: list[str] = []
    verification: list[str] = []
    follow_up: list[str] = []
    for task in plan.tasks:
        entry = ledger.entry(task.id)
        if entry.latest_attempt_path is None:
            raise ValueError(f"Task `{task.id}` has no attempt evidence path.")
        report_path = workspace_root / entry.latest_attempt_path / "implementation-report.md"
        report = report_path.read_text(encoding="utf-8")
        summaries.append(
            f"- `{task.id}`: {task.outcome} Evidence: "
            f"`{entry.latest_attempt_path}/implementation-report.md`."
        )
        for line in _section(report, "Touched files").splitlines():
            if line.strip().startswith("-") and line not in touched:
                touched.append(line)
        for line in _section(report, "Verification notes").splitlines():
            if line.strip().startswith("-"):
                verification.append(f"- `{task.id}` {line.strip()[1:].strip()}")
        for criterion in task.acceptance_criteria:
            verification.append(
                f"- `{task.id}` `{criterion.id}` -> covered by "
                f"`{entry.latest_attempt_path}/implementation-report.md`."
            )
        for line in _section(report, "Follow-up notes").splitlines():
            if line.strip().startswith("-") and "none" not in line.casefold():
                follow_up.append(f"- `{task.id}` {line.strip()[1:].strip()}")
    lines = [
        "# Implementation Report",
        "",
        "## Selected task",
        "",
        "- Task ids: " + ", ".join(f"`{task.id}`" for task in plan.tasks),
        "",
        "## Change summary",
        "",
        *summaries,
        "",
        "## Touched files",
        "",
        *(touched or ["- none"]),
        "",
        "## Verification notes",
        "",
        *verification,
        "",
        "## Follow-up notes",
        "",
        *(follow_up or ["- none"]),
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "TaskExecutionContext",
    "TaskResumeBlockedError",
    "complete_task_execution",
    "load_task_execution_plan",
    "prepare_task_execution",
    "published_tasklist_path",
    "reconcile_task_execution_state",
    "render_aggregate_implementation_report",
    "write_task_selection_context",
]

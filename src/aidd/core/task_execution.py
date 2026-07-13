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

from aidd.core.interview import stage_has_unresolved_blocking_questions
from aidd.core.run_store import (
    load_stage_metadata,
    next_attempt_number,
    persist_stage_status,
    run_attempt_root,
    run_stage_root,
)
from aidd.core.stage_models import StageExecutionState, StageOutputDiscovery
from aidd.core.stage_validation import update_stage_unblock_state
from aidd.core.state_machine import StageState
from aidd.core.task_ledger import (
    TaskExecutionStatus,
    TaskFinalizationStatus,
    TaskLedger,
    ensure_task_ledger,
    persist_task_ledger,
    task_root,
)
from aidd.core.task_plan import TaskCard, TaskPlan, parse_task_plan
from aidd.validators.models import ValidationFinding, ValidationIssueLocation


@dataclass(frozen=True, slots=True)
class TaskExecutionContext:
    plan: TaskPlan
    ledger: TaskLedger
    task: TaskCard
    global_attempt_start: int
    task_attempt_path: Path


class TaskResumeBlockedError(ValueError):
    """Raised when a blocked task still requires operator input."""


@dataclass(frozen=True, slots=True)
class TaskFinalizationContext:
    ledger: TaskLedger
    attempt_path: Path
    attempt_number: int


def published_tasklist_path(*, workspace_root: Path, work_item: str) -> Path:
    return (
        workspace_root / "workitems" / work_item / "stages" / "tasklist" / "output" / "tasklist.md"
    )


def load_task_execution_plan(*, workspace_root: Path, work_item: str) -> TaskPlan:
    path = published_tasklist_path(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    if not path.exists():
        raise ValueError(f"Published tasklist is missing: {path.as_posix()}.")
    return parse_task_plan(path.read_text(encoding="utf-8"))


def _task_selection_path(*, workspace_root: Path, work_item: str) -> Path:
    return workspace_root / "workitems" / work_item / "context" / "task-selection.md"


def _selected_task_id(*, workspace_root: Path, work_item: str) -> str | None:
    path = _task_selection_path(workspace_root=workspace_root, work_item=work_item)
    if not path.exists():
        return None
    match = re.search(r"Task id\s*:\s*`([^`]+)`", path.read_text(encoding="utf-8"))
    return match.group(1).upper() if match is not None else None


def write_task_selection_context(*, workspace_root: Path, work_item: str, task: TaskCard) -> Path:
    path = _task_selection_path(workspace_root=workspace_root, work_item=work_item)
    lines = [
        "# Task Selection",
        "",
        "## Selected task",
        "",
        f"- Task id: `{task.id}`",
        f"- Title: {task.title}",
        f"- Outcome: {task.outcome}",
        f"- Dominant deliverable: {task.dominant_deliverable}",
        f"- In scope: {task.in_scope}",
        "",
        "## Acceptance criteria",
        "",
    ]
    lines.extend(f"- `{criterion.id}`: {criterion.text}" for criterion in task.acceptance_criteria)
    lines.extend(
        [
            "",
            "## Dependencies",
            "",
            "- " + (", ".join(f"`{item}`" for item in task.dependencies) or "none"),
            "",
            "## Verification",
            "",
            f"- {task.verification}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _attempt_state_path(attempt_path: Path) -> Path:
    return attempt_path / "attempt-state.json"


def _write_attempt_state(
    attempt_path: Path,
    *,
    task_id: str,
    attempt_number: int,
    status: str,
    blocker: str | None = None,
) -> None:
    _attempt_state_path(attempt_path).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": task_id,
                "attempt_number": attempt_number,
                "status": status,
                "blocker": blocker,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _task_attempts_root(
    *, workspace_root: Path, work_item: str, run_id: str, task_id: str
) -> Path:
    return (
        task_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            task_id=task_id,
        )
        / "attempts"
    )


def _existing_task_attempts(attempts_root: Path) -> tuple[tuple[int, Path], ...]:
    attempts: list[tuple[int, Path]] = []
    if not attempts_root.exists():
        return ()
    for path in attempts_root.glob("attempt-[0-9][0-9][0-9][0-9]"):
        try:
            number = int(path.name.removeprefix("attempt-"))
        except ValueError:
            continue
        attempts.append((number, path))
    return tuple(sorted(attempts))


def _reconcile_staging_attempts(
    attempts_root: Path,
    *,
    task_id: str,
) -> None:
    if not attempts_root.exists():
        return
    for staging in sorted(attempts_root.glob(".attempt-*-*.staging")):
        match = re.match(r"^\.attempt-(\d+)-", staging.name)
        if match is None:
            continue
        number = int(match.group(1))
        target = attempts_root / f"attempt-{number:04d}"
        if target.exists():
            shutil.rmtree(staging, ignore_errors=True)
            continue
        staging.replace(target)
        _write_attempt_state(
            target,
            task_id=task_id,
            attempt_number=number,
            status="abandoned",
            blocker="Task attempt was abandoned during atomic preparation.",
        )


def reconcile_task_execution_state(
    *, workspace_root: Path, work_item: str, run_id: str, ledger: TaskLedger
) -> TaskLedger:
    """Terminalize abandoned task attempts after the run lease has been acquired."""

    reconciled = ledger
    for entry in ledger.tasks:
        attempts_root = _task_attempts_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            task_id=entry.id,
        )
        _reconcile_staging_attempts(attempts_root, task_id=entry.id)
        attempts = _existing_task_attempts(attempts_root)
        for number, path in attempts:
            if number > entry.attempt_count:
                _write_attempt_state(
                    path,
                    task_id=entry.id,
                    attempt_number=number,
                    status="abandoned",
                    blocker="Task attempt was abandoned before ledger commit.",
                )
        if entry.status is not TaskExecutionStatus.EXECUTING:
            continue
        if entry.latest_attempt_path is not None:
            attempt_path = workspace_root / entry.latest_attempt_path
            if attempt_path.exists():
                _write_attempt_state(
                    attempt_path,
                    task_id=entry.id,
                    attempt_number=entry.attempt_count,
                    status="abandoned",
                    blocker="Task execution was interrupted before a terminal result.",
                )
        reconciled = reconciled.transition(
            entry.id,
            TaskExecutionStatus.FAILED,
            blocker="Task execution was interrupted; resume creates a new attempt.",
        )
    if reconciled != ledger:
        persist_task_ledger(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            ledger=reconciled,
        )
    return reconciled


def _copy_interview_evidence(stage_root: Path, attempt_path: Path) -> None:
    for name in ("questions.md", "answers.md"):
        source = stage_root / name
        if source.exists():
            shutil.copy2(source, attempt_path / name)


def _finalization_attempts_root(
    *, workspace_root: Path, work_item: str, run_id: str
) -> Path:
    return (
        run_stage_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        )
        / "finalization"
        / "attempts"
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
    _reconcile_staging_attempts(attempts_root, task_id="finalization")
    existing = _existing_task_attempts(attempts_root)
    number = max(
        (ledger.finalization.attempt_count, *(item for item, _ in existing))
    ) + 1
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
    attempt_path = attempts_root / f"attempt-{number:04d}"
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
    status = (
        TaskFinalizationStatus.SUCCEEDED if succeeded else TaskFinalizationStatus.FAILED
    )
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
            raise ValueError(
                f"Repository snapshot path escapes project root: {relative_path}."
            )
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
    plan = load_task_execution_plan(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    ledger = ensure_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        plan=plan,
    )
    ledger = reconcile_task_execution_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    task = plan.by_id().get(task_id)
    if task is None:
        raise ValueError(f"Unknown task id `{task_id}`.")
    entry = ledger.entry(task_id)
    if entry.status is TaskExecutionStatus.SUCCEEDED:
        raise ValueError(f"Task `{task_id}` has already succeeded.")
    resume_blocked_task = entry.status is TaskExecutionStatus.BLOCKED
    if resume_blocked_task:
        unblock = update_stage_unblock_state(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        )
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        )
        resumed_preparing = (
            metadata is not None
            and metadata.status == StageState.PREPARING.value
            and any(change.status == StageState.BLOCKED.value for change in metadata.status_history)
            and not stage_has_unresolved_blocking_questions(
                workspace_root=workspace_root,
                work_item=work_item,
                stage="implement",
            )
        )
        if not unblock.unblocked and not resumed_preparing:
            raise TaskResumeBlockedError(
                f"Task `{task_id}` is still blocked by unresolved questions or approvals."
            )
    attempts_root = _task_attempts_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        task_id=task_id,
    )
    _reconcile_staging_attempts(attempts_root, task_id=task_id)
    existing_attempts = _existing_task_attempts(attempts_root)
    task_attempt_number = max(
        (entry.attempt_count, *(number for number, _ in existing_attempts))
    ) + 1
    attempts_root.mkdir(parents=True, exist_ok=True)
    staging_path = attempts_root / f".attempt-{task_attempt_number:04d}-{uuid4().hex}.staging"
    staging_path.mkdir()
    baseline = _snapshot_payload(project_root=project_root, task_id=task_id)
    (staging_path / "repository-baseline.json").write_text(
        json.dumps(baseline, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_attempt_state(
        staging_path,
        task_id=task_id,
        attempt_number=task_attempt_number,
        status="preparing",
    )
    task_attempt_path = attempts_root / f"attempt-{task_attempt_number:04d}"
    staging_path.replace(task_attempt_path)
    implement_stage_root = (
        workspace_root / "workitems" / work_item / "stages" / "implement"
    )
    for document_name in (
        "implementation-report.md",
        "stage-result.md",
        "validator-report.md",
        "repair-brief.md",
    ):
        (implement_stage_root / document_name).unlink(missing_ok=True)
    preserve_interview = resume_blocked_task or _selected_task_id(
        workspace_root=workspace_root,
        work_item=work_item,
    ) == task_id
    if preserve_interview:
        _copy_interview_evidence(implement_stage_root, task_attempt_path)
    else:
        for document_name in ("questions.md", "answers.md"):
            (implement_stage_root / document_name).unlink(missing_ok=True)
    write_task_selection_context(
        workspace_root=workspace_root,
        work_item=work_item,
        task=task,
    )
    workspace_relative_attempt = task_attempt_path.relative_to(workspace_root).as_posix()
    ledger = ledger.transition(
        task_id,
        TaskExecutionStatus.EXECUTING,
        attempt_number=task_attempt_number,
        latest_attempt_path=workspace_relative_attempt,
    )
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
    )
    _write_attempt_state(
        task_attempt_path,
        task_id=task_id,
        attempt_number=task_attempt_number,
        status="executing",
    )
    return TaskExecutionContext(
        plan=plan,
        ledger=ledger,
        task=task,
        global_attempt_start=next_attempt_number(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
        ),
        task_attempt_path=task_attempt_path,
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
            if input_bundle.exists() and not (
                context.task_attempt_path / "input-bundle.md"
            ).exists():
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
    scope_path = workspace_root / "workitems" / work_item / "context" / "allowed-write-scope.md"
    allowed_scope_paths: list[str] = []
    if scope_path.exists():
        for value in re.findall(
            r"`([^`]+)`",
            scope_path.read_text(encoding="utf-8", errors="replace"),
        ):
            normalized = value.strip().strip("/")
            if normalized:
                allowed_scope_paths.append(normalized)
    task_scope_paths = list(context.task.scope_paths)
    task_scope_outside_global = sorted(
        path
        for path in task_scope_paths
        if allowed_scope_paths
        and not any(
            path == allowed
            or path.startswith(f"{allowed}/")
            or allowed.startswith(f"{path}/")
            for allowed in allowed_scope_paths
        )
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
        or (
            allowed_scope_paths
            and not any(
                path == allowed or path.startswith(f"{allowed}/")
                for allowed in allowed_scope_paths
            )
        )
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
    _copy_interview_evidence(implement_stage_root, context.task_attempt_path)
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
    workspace_relative_attempt = context.task_attempt_path.relative_to(workspace_root).as_posix()
    status = TaskExecutionStatus.SUCCEEDED if succeeded else TaskExecutionStatus.FAILED
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
    )
    if (
        not succeeded
        and metadata is not None
        and metadata.status == StageState.BLOCKED.value
    ):
        status = TaskExecutionStatus.BLOCKED
    ledger = context.ledger.transition(
        context.task.id,
        status,
        latest_attempt_path=workspace_relative_attempt,
        blocker=blocker,
    )
    _write_attempt_state(
        context.task_attempt_path,
        task_id=context.task.id,
        attempt_number=ledger.entry(context.task.id).attempt_count,
        status=status.value,
        blocker=blocker,
    )
    persist_task_ledger(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        ledger=ledger,
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
    "complete_task_execution",
    "load_task_execution_plan",
    "prepare_task_execution",
    "published_tasklist_path",
    "render_aggregate_implementation_report",
    "write_task_selection_context",
]

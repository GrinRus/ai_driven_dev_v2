from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import uuid4

from aidd.core.attempt_lineage import (
    AttemptKind,
    AttemptLineage,
    AttemptScope,
    FinalizationAttemptState,
)
from aidd.core.identifiers import contained_component_path
from aidd.core.markdown import extract_h2_section
from aidd.core.project_set import PROJECT_SET_CONTEXT_FILENAME
from aidd.core.run_store import load_run_manifest, load_stage_metadata, run_stage_root
from aidd.core.task_attempt_lifecycle import existing_attempts, reconcile_staging_attempts
from aidd.core.task_ledger import (
    TaskFinalizationStatus,
    TaskLedger,
    persist_task_ledger,
)
from aidd.core.task_plan import TaskExecutionMode, TaskPlan
from aidd.core.workspace import work_item_context_root

OUTSIDE_PROJECT_SET_EVIDENCE_FILENAME = "outside-project-set.md"
_PROJECT_SET_ROW_PATTERN = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|")


@dataclass(frozen=True, slots=True)
class TaskFinalizationContext:
    ledger: TaskLedger
    attempt_path: Path
    attempt_number: int
    lineage: AttemptLineage | None = None


def _declared_project_set_roots(*, workspace_root: Path, work_item: str) -> tuple[str, ...]:
    context_path = (
        work_item_context_root(root=workspace_root, work_item=work_item)
        / PROJECT_SET_CONTEXT_FILENAME
    )
    if not context_path.is_file():
        return ()
    roots: list[str] = []
    for line in context_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _PROJECT_SET_ROW_PATTERN.match(line.strip())
        if match is None:
            continue
        raw_root = match.group(2).strip().strip("/")
        if raw_root in {"", "."}:
            roots.append("")
            continue
        relative = PurePosixPath(raw_root)
        if relative.is_absolute() or ".." in relative.parts or "\\" in raw_root:
            raise ValueError(
                "Project-set context contains an unsafe repository-relative root: "
                f"{raw_root}."
            )
        roots.append(relative.as_posix())
    unique_roots = tuple(dict.fromkeys(roots))
    if not unique_roots:
        raise ValueError(
            f"Project-set context does not declare any roots: {context_path.as_posix()}."
        )
    return unique_roots


def _path_is_in_project_set(path: str, roots: tuple[str, ...]) -> bool:
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts or "\\" in path:
        raise ValueError(f"Task diff contains an unsafe repository-relative path: {path}.")
    normalized = relative.as_posix()
    return any(
        not root or normalized == root or normalized.startswith(f"{root}/")
        for root in roots
    )


def outside_project_set_changes(
    *, workspace_root: Path, work_item: str, ledger: TaskLedger
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return observed task paths that are outside the declared project-set roots.

    Task snapshots are captured relative to the selected repository root. This helper
    reads only those durable task-diff artifacts, so a finalization retry evaluates the
    same evidence instead of taking a new mutable working-tree snapshot.
    """

    roots = _declared_project_set_roots(workspace_root=workspace_root, work_item=work_item)
    if not roots:
        return ()
    outside: dict[str, set[str]] = {}
    resolved_workspace = workspace_root.resolve(strict=False)
    for entry in ledger.tasks:
        if entry.latest_attempt_path is None:
            raise ValueError(f"Task `{entry.id}` is missing its latest attempt path.")
        attempt_path = (workspace_root / entry.latest_attempt_path).resolve(strict=False)
        if not attempt_path.is_relative_to(resolved_workspace):
            raise ValueError(
                f"Task attempt path escapes workspace root for `{entry.id}`: "
                f"{entry.latest_attempt_path}."
            )
        diff_path = attempt_path / "task-diff.json"
        if not diff_path.is_file():
            raise ValueError(
                f"Task diff evidence is missing for `{entry.id}`: {diff_path.as_posix()}."
            )
        try:
            payload = json.loads(diff_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Task diff evidence is unreadable for `{entry.id}`: {diff_path.as_posix()}."
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Task diff evidence must be an object for `{entry.id}`.")
        if payload.get("schema_version") != 1 or payload.get("task_id") != entry.id:
            raise ValueError(
                f"Task diff evidence identity is invalid for `{entry.id}`."
            )
        observed = payload.get("observed_touched_paths")
        if not isinstance(observed, list) or not all(isinstance(path, str) for path in observed):
            raise ValueError(
                f"Task diff evidence has invalid observed paths for `{entry.id}`."
            )
        for path in observed:
            if not _path_is_in_project_set(path, roots):
                outside.setdefault(path, set()).add(entry.id)
    return tuple(
        (path, tuple(sorted(task_ids))) for path, task_ids in sorted(outside.items())
    )


def render_outside_project_set_evidence(
    *,
    work_item: str,
    changes: tuple[tuple[str, tuple[str, ...]], ...],
) -> str:
    lines = [
        "# Outside Project-Set Evidence",
        "",
        "- Work item: `" + work_item + "`",
        "- Status: `blocked`",
        "- Aggregate implementation finalization is fail-closed until these paths are reviewed.",
        "",
        "## Outside-set changes",
        "",
    ]
    lines.extend(
        f"- `{path}` (observed by task(s): {', '.join(f'`{task_id}`' for task_id in task_ids)})"
        for path, task_ids in changes
    )
    lines.append("")
    return "\n".join(lines)


def aggregate_execution_mode(plan: TaskPlan) -> TaskExecutionMode:
    """Return the effective repository mode for system-owned aggregate evidence."""

    if any(
        task.execution_mode is TaskExecutionMode.REPOSITORY_CHANGE for task in plan.tasks
    ):
        return TaskExecutionMode.REPOSITORY_CHANGE
    return TaskExecutionMode.VERIFICATION_ONLY


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
    load_run_manifest(workspace_root=workspace_root, work_item=work_item, run_id=run_id)
    load_stage_metadata(
        workspace_root=workspace_root, work_item=work_item, run_id=run_id, stage="implement"
    )
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
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    lineage = AttemptLineage(
        scope=AttemptScope.FINALIZATION,
        attempt_kind=AttemptKind.FINALIZATION,
        attempt_number=number,
    )
    state = FinalizationAttemptState(
        attempt_number=number,
        status="executing",
        created_at_utc=timestamp,
        updated_at_utc=timestamp,
        lineage=lineage,
    )
    (staging / "finalization-state.json").write_text(
        json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    attempt_path = contained_component_path(
        attempts_root,
        f"attempt-{number:04d}",
        boundary_root=workspace_root,
        label="finalization attempt id",
    )
    staging.replace(attempt_path)
    ledger = ledger.transition_finalization(
        TaskFinalizationStatus.EXECUTING,
        attempt_number=number,
        latest_attempt_path=attempt_path.relative_to(workspace_root).as_posix(),
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
        lineage=lineage,
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
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    state_path = context.attempt_path / "finalization-state.json"
    created_at_utc = timestamp
    lineage = AttemptLineage(
        scope=AttemptScope.FINALIZATION,
        attempt_kind=AttemptKind.FINALIZATION,
        attempt_number=context.attempt_number,
    )
    try:
        existing_payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError):
        existing = None
    else:
        existing = FinalizationAttemptState.from_dict(existing_payload)
    if existing is not None:
        if existing.created_at_utc is not None and existing.created_at_utc.strip():
            created_at_utc = existing.created_at_utc
        if existing.lineage is not None:
            lineage = existing.lineage
    state = FinalizationAttemptState(
        attempt_number=context.attempt_number,
        status=status.value,
        blocker=blocker,
        created_at_utc=created_at_utc,
        updated_at_utc=timestamp,
        lineage=lineage,
    )
    (context.attempt_path / "finalization-state.json").write_text(
        json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ledger


def _section_bullets(markdown: str, heading: str) -> tuple[str, ...]:
    """Return top-level bullets with wrapped Markdown lines joined together.

    Runtime-authored implementation reports often wrap a verification item over
    several physical lines.  Treat only column-zero ``- `` markers as new items;
    indented lines remain part of the preceding item so command and result
    evidence cannot be split into unverifiable fragments during aggregation.
    """

    section = extract_h2_section(markdown, heading)
    bullets: list[str] = []
    current: str | None = None
    for raw_line in section.splitlines():
        if raw_line.startswith("- "):
            if current is not None:
                bullets.append(current)
            current = raw_line[2:].strip()
        elif current is not None and raw_line.strip():
            current += " " + raw_line.strip()
    if current is not None:
        bullets.append(current)
    return tuple(bullets)


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
        for line in extract_h2_section(report, "Touched files").splitlines():
            normalized_line = line.strip()
            if (
                normalized_line.startswith("-")
                and normalized_line.casefold() != "- none"
                and normalized_line not in touched
            ):
                touched.append(normalized_line)
        verification_section = (
            "Verification" if extract_h2_section(report, "Verification") else "Verification notes"
        )
        for bullet in _section_bullets(report, verification_section):
            verification.append(f"- `{task.id}` {bullet}")
        for criterion in task.acceptance_criteria:
            verification.append(
                f"- `{task.id}` `{criterion.id}` -> covered by "
                f"`{entry.latest_attempt_path}/implementation-report.md`."
            )
        for line in extract_h2_section(report, "Follow-up notes").splitlines():
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
    "OUTSIDE_PROJECT_SET_EVIDENCE_FILENAME",
    "TaskFinalizationContext",
    "aggregate_execution_mode",
    "complete_task_finalization",
    "outside_project_set_changes",
    "prepare_task_finalization",
    "render_aggregate_implementation_report",
    "render_outside_project_set_evidence",
]

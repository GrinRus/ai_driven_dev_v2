from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from aidd.core.run_store import run_attempt_root, write_json_payload

TASK_ATTEMPT_REFERENCES_FILENAME = "stage-attempt-references.json"
_LEGACY_STAGE_ATTEMPT_RE = re.compile(r"^stage-attempt-(\d{4})$")


@dataclass(frozen=True, slots=True)
class TaskStageAttemptReference:
    attempt_number: int
    path: str

    def to_dict(self) -> dict[str, object]:
        return {"attempt_number": self.attempt_number, "path": self.path}

    @classmethod
    def from_dict(cls, payload: object) -> TaskStageAttemptReference:
        if not isinstance(payload, dict):
            raise ValueError("Task stage-attempt reference must be a JSON object.")
        attempt_number = payload.get("attempt_number")
        path = payload.get("path")
        if (
            not isinstance(attempt_number, int)
            or isinstance(attempt_number, bool)
            or attempt_number < 1
        ):
            raise ValueError("Task stage-attempt reference number must be a positive integer.")
        if not isinstance(path, str) or not path:
            raise ValueError("Task stage-attempt reference path must be a non-empty string.")
        _validate_relative_posix_path(path)
        return cls(attempt_number=attempt_number, path=path)


@dataclass(frozen=True, slots=True)
class TaskAttemptEvidenceReferences:
    task_id: str
    task_attempt_number: int
    stage_attempts: tuple[TaskStageAttemptReference, ...]
    stage: str = "implement"
    schema_version: int = 1

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "task_attempt_number": self.task_attempt_number,
            "stage": self.stage,
            "stage_attempts": [reference.to_dict() for reference in self.stage_attempts],
        }

    @classmethod
    def from_dict(cls, payload: object) -> TaskAttemptEvidenceReferences:
        if not isinstance(payload, dict):
            raise ValueError("Task attempt evidence references must be a JSON object.")
        if payload.get("schema_version") != 1:
            raise ValueError("Unsupported task attempt evidence reference schema version.")
        task_id = payload.get("task_id")
        task_attempt_number = payload.get("task_attempt_number")
        stage = payload.get("stage")
        raw_attempts = payload.get("stage_attempts")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("Task attempt evidence task_id must be a non-empty string.")
        if (
            not isinstance(task_attempt_number, int)
            or isinstance(task_attempt_number, bool)
            or task_attempt_number < 1
        ):
            raise ValueError("Task attempt evidence number must be a positive integer.")
        if stage != "implement":
            raise ValueError("Task attempt evidence stage must be `implement`.")
        if not isinstance(raw_attempts, list):
            raise ValueError("Task attempt evidence stage_attempts must be a list.")
        references = tuple(TaskStageAttemptReference.from_dict(item) for item in raw_attempts)
        numbers = tuple(reference.attempt_number for reference in references)
        if numbers != tuple(sorted(set(numbers))):
            raise ValueError("Task stage-attempt references must be unique and ordered.")
        return cls(
            task_id=task_id,
            task_attempt_number=task_attempt_number,
            stage_attempts=references,
        )


@dataclass(frozen=True, slots=True)
class ResolvedTaskAttemptEvidence:
    layout: str
    stage_attempts: tuple[TaskStageAttemptReference, ...]


def _validate_relative_posix_path(value: str) -> None:
    if "\\" in value or value.endswith("/") or "//" in value:
        raise ValueError("Task stage-attempt reference must be a normalized POSIX path.")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("Task stage-attempt reference must stay workspace-relative.")


def _validate_artifact_index(
    *,
    attempt_path: Path,
    work_item: str,
    run_id: str,
    attempt_number: int,
) -> None:
    index_path = attempt_path / "artifact-index.json"
    if not index_path.exists():
        return
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Referenced artifact index is invalid: {index_path.as_posix()}.") from exc
    if not isinstance(payload, dict) or (
        payload.get("work_item_id") != work_item
        or payload.get("run_id") != run_id
        or payload.get("stage") != "implement"
        or payload.get("attempt_number") != attempt_number
    ):
        raise ValueError(
            f"Referenced artifact index identity does not match attempt {attempt_number}."
        )


def _resolve_reference(
    reference: TaskStageAttemptReference,
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
) -> Path:
    expected = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="implement",
        attempt_number=reference.attempt_number,
    )
    expected_relative = expected.relative_to(workspace_root).as_posix()
    if reference.path != expected_relative:
        raise ValueError(
            "Task stage-attempt reference does not match its canonical run attempt path."
        )
    if not expected.is_dir():
        raise ValueError(f"Referenced stage attempt does not exist: {reference.path}.")
    resolved_workspace = workspace_root.resolve(strict=True)
    resolved_attempt = expected.resolve(strict=True)
    if not resolved_attempt.is_relative_to(resolved_workspace):
        raise ValueError(f"Referenced stage attempt escapes workspace root: {reference.path}.")
    _validate_artifact_index(
        attempt_path=expected,
        work_item=work_item,
        run_id=run_id,
        attempt_number=reference.attempt_number,
    )
    return expected


def write_task_attempt_references(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    task_id: str,
    task_attempt_number: int,
    task_attempt_path: Path,
    stage_attempt_numbers: tuple[int, ...],
) -> Path:
    references: list[TaskStageAttemptReference] = []
    for attempt_number in stage_attempt_numbers:
        attempt_path = run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage="implement",
            attempt_number=attempt_number,
        )
        if not attempt_path.exists():
            continue
        reference = TaskStageAttemptReference(
            attempt_number=attempt_number,
            path=attempt_path.relative_to(workspace_root).as_posix(),
        )
        _resolve_reference(
            reference,
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        )
        references.append(reference)
    manifest = TaskAttemptEvidenceReferences(
        task_id=task_id,
        task_attempt_number=task_attempt_number,
        stage_attempts=tuple(references),
    )
    path = task_attempt_path / TASK_ATTEMPT_REFERENCES_FILENAME
    write_json_payload(path, manifest.to_dict())
    return path


def load_task_attempt_references(
    *,
    path: Path,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    task_id: str,
    task_attempt_number: int,
) -> TaskAttemptEvidenceReferences:
    try:
        manifest = TaskAttemptEvidenceReferences.from_dict(
            json.loads(path.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError) as exc:
        raise ValueError(f"Task attempt evidence manifest is invalid: {path.as_posix()}.") from exc
    if manifest.task_id != task_id or manifest.task_attempt_number != task_attempt_number:
        raise ValueError("Task attempt evidence manifest identity does not match its task attempt.")
    for reference in manifest.stage_attempts:
        _resolve_reference(
            reference,
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        )
    return manifest


def resolve_task_attempt_evidence(
    *,
    task_attempt_path: Path,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    task_id: str,
    task_attempt_number: int,
) -> ResolvedTaskAttemptEvidence:
    manifest_path = task_attempt_path / TASK_ATTEMPT_REFERENCES_FILENAME
    if manifest_path.exists():
        manifest = load_task_attempt_references(
            path=manifest_path,
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            task_id=task_id,
            task_attempt_number=task_attempt_number,
        )
        return ResolvedTaskAttemptEvidence(
            layout="references",
            stage_attempts=manifest.stage_attempts,
        )
    legacy: list[TaskStageAttemptReference] = []
    for candidate in sorted(task_attempt_path.glob("stage-attempt-[0-9][0-9][0-9][0-9]")):
        match = _LEGACY_STAGE_ATTEMPT_RE.fullmatch(candidate.name)
        if match is None or not candidate.is_dir():
            continue
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(workspace_root.resolve(strict=True)):
            raise ValueError("Legacy task stage-attempt evidence escapes workspace root.")
        legacy.append(
            TaskStageAttemptReference(
                attempt_number=int(match.group(1)),
                path=candidate.relative_to(workspace_root).as_posix(),
            )
        )
    return ResolvedTaskAttemptEvidence(layout="legacy", stage_attempts=tuple(legacy))


__all__ = [
    "TASK_ATTEMPT_REFERENCES_FILENAME",
    "ResolvedTaskAttemptEvidence",
    "TaskAttemptEvidenceReferences",
    "TaskStageAttemptReference",
    "load_task_attempt_references",
    "resolve_task_attempt_evidence",
    "write_task_attempt_references",
]

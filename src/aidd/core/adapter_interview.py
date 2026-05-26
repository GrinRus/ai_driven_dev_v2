"""Narrow interview persistence API exposed to runtime adapters."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aidd.core.interview import (
    AdapterQuestionEvent,
    QuestionPolicy,
    load_answers_document,
    load_questions_document,
    persist_answers_document,
    persist_questions_document,
    resolved_question_ids,
    unresolved_blocking_questions,
)
from aidd.core.run_store import run_stage_metadata_path


@dataclass(frozen=True, slots=True)
class AdapterQuestionMetadataPersistence:
    stage_metadata_path: Path
    metadata_updated: bool


def _format_utc_timestamp() -> str:
    return (
        datetime.now(UTC)
        .astimezone(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _workspace_relative_path(workspace_root: Path, path: Path) -> str:
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = path.resolve(strict=False)
    return resolved_path.relative_to(resolved_workspace).as_posix()


def persist_adapter_question_metadata(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    metadata_key: str,
    questions_path: Path,
    unresolved_blocking_question_ids: Iterable[str],
) -> AdapterQuestionMetadataPersistence:
    if not metadata_key.strip():
        raise ValueError("Question metadata key must not be empty.")

    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if not metadata_path.exists():
        return AdapterQuestionMetadataPersistence(
            stage_metadata_path=metadata_path,
            metadata_updated=False,
        )

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload[metadata_key] = {
        "questions_path": _workspace_relative_path(workspace_root, questions_path),
        "unresolved_blocking_question_ids": list(unresolved_blocking_question_ids),
    }
    payload["updated_at_utc"] = _format_utc_timestamp()
    metadata_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return AdapterQuestionMetadataPersistence(
        stage_metadata_path=metadata_path,
        metadata_updated=True,
    )

__all__ = [
    "AdapterQuestionEvent",
    "AdapterQuestionMetadataPersistence",
    "QuestionPolicy",
    "load_answers_document",
    "load_questions_document",
    "persist_adapter_question_metadata",
    "persist_answers_document",
    "persist_questions_document",
    "resolved_question_ids",
    "unresolved_blocking_questions",
]

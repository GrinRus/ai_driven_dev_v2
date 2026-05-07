from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from aidd.core.adapter_interview import (
    AdapterQuestionEvent,
    QuestionPolicy,
    persist_answers_document,
    persist_questions_document,
)
from aidd.runtime_logs.events import (
    RuntimeEventArtifacts as RuntimeEventArtifacts,
)
from aidd.runtime_logs.events import (
    normalize_structured_events as normalize_structured_events,
)
from aidd.runtime_logs.events import (
    persist_runtime_event_artifacts as persist_runtime_event_artifacts,
)
from aidd.runtime_logs.events import (
    structured_runtime_events as structured_runtime_events,
)

_QUESTION_ID_PATTERN = re.compile(r"^Q[\w-]*$")


@dataclass(frozen=True, slots=True)
class RuntimeQuestionDetection:
    question_events: tuple[AdapterQuestionEvent, ...]
    pause_detected: bool


def _question_policy_from_event(event: Mapping[str, object]) -> QuestionPolicy:
    policy_value = event.get("policy")
    if isinstance(policy_value, str):
        normalized = policy_value.strip().lower()
        if normalized in {"non-blocking", "non_blocking", "nonblocking"}:
            return QuestionPolicy.NON_BLOCKING
        if normalized == "blocking":
            return QuestionPolicy.BLOCKING

    blocking_value = event.get("blocking")
    if isinstance(blocking_value, bool):
        return QuestionPolicy.BLOCKING if blocking_value else QuestionPolicy.NON_BLOCKING

    return QuestionPolicy.BLOCKING


def _question_id_from_event(event: Mapping[str, object]) -> str | None:
    for field_name in ("question_id", "questionId", "id"):
        raw_value = event.get(field_name)
        if not isinstance(raw_value, str):
            continue
        candidate = raw_value.strip()
        if _QUESTION_ID_PATTERN.match(candidate):
            return candidate
    return None


def _question_text_from_event(event: Mapping[str, object]) -> str | None:
    for field_name in ("question", "text", "prompt", "message"):
        raw_value = event.get(field_name)
        if isinstance(raw_value, str) and raw_value.strip():
            return raw_value.strip()
    return None


def detect_question_or_pause_events(
    *,
    normalized_events: tuple[dict[str, object], ...],
) -> RuntimeQuestionDetection:
    question_events: list[AdapterQuestionEvent] = []
    pause_detected = False

    for event in normalized_events:
        event_kind = str(event.get("event") or event.get("type") or "").strip().lower()
        pause_flag = bool(event.get("paused", False))
        is_question_kind = event_kind in {
            "question",
            "question_raised",
            "question-raised",
            "ask_user",
            "ask-user",
        }
        is_pause_kind = event_kind in {
            "pause",
            "paused",
            "awaiting_input",
            "awaiting-input",
            "input_required",
            "input-required",
        }
        if not (is_question_kind or is_pause_kind or pause_flag):
            continue

        event_pause_detected = is_pause_kind or pause_flag
        pause_detected = pause_detected or event_pause_detected
        question_text = _question_text_from_event(event)
        if question_text is None and event_pause_detected:
            question_text = "Runtime paused and requires operator input."
        if question_text is None:
            continue

        question_events.append(
            AdapterQuestionEvent(
                text=question_text,
                policy=_question_policy_from_event(event),
                question_id=_question_id_from_event(event),
            )
        )

    return RuntimeQuestionDetection(
        question_events=tuple(question_events),
        pause_detected=pause_detected,
    )


def persist_adapter_question_events(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    adapter_question_events: tuple[AdapterQuestionEvent, ...],
) -> Path | None:
    if not adapter_question_events:
        return None
    questions_path = persist_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        adapter_question_events=adapter_question_events,
    )
    _ensure_empty_answers_document_for_native_questions(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    return questions_path


def _ensure_empty_answers_document_for_native_questions(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> None:
    stage_root = workspace_root / "workitems" / work_item / "stages" / stage
    answers_path = stage_root / "answers.md"
    misplaced_answers_path = stage_root / "output" / "answers.md"
    if answers_path.exists() or misplaced_answers_path.exists():
        return
    persist_answers_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )


__all__ = [
    "RuntimeEventArtifacts",
    "RuntimeQuestionDetection",
    "detect_question_or_pause_events",
    "normalize_structured_events",
    "persist_adapter_question_events",
    "persist_runtime_event_artifacts",
    "structured_runtime_events",
]

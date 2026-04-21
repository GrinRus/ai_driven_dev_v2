from __future__ import annotations

import re
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class QuestionPolicy(StrEnum):
    BLOCKING = "blocking"
    NON_BLOCKING = "non-blocking"


_QUESTION_ID_PATTERN = re.compile(r"^Q[\w-]*$")
_QUESTION_LINE_PATTERN = re.compile(
    r"^\s*-\s+`?(Q[\w-]+)`?\s+`?\[(blocking|non-blocking)\]`?\s+(.+?)\s*$"
)
_QUESTION_ID_NUMERIC_SUFFIX_PATTERN = re.compile(r"^Q(\d+)$")


@dataclass(frozen=True, slots=True)
class InterviewQuestion:
    question_id: str
    text: str
    policy: QuestionPolicy

    def __post_init__(self) -> None:
        normalized_id = self.question_id.strip()
        if not normalized_id:
            raise ValueError("Question id must not be empty.")
        if _QUESTION_ID_PATTERN.match(normalized_id) is None:
            raise ValueError(
                "Question id must use a stable `Q`-prefixed token (for example `Q1`, `Q2`)."
            )
        object.__setattr__(self, "question_id", normalized_id)

        normalized_text = self.text.strip()
        if not normalized_text:
            raise ValueError("Question text must not be empty.")
        object.__setattr__(self, "text", normalized_text)


@dataclass(frozen=True, slots=True)
class AdapterQuestionEvent:
    text: str
    policy: QuestionPolicy = QuestionPolicy.BLOCKING
    question_id: str | None = None

    def __post_init__(self) -> None:
        normalized_text = self.text.strip()
        if not normalized_text:
            raise ValueError("Adapter question event text must not be empty.")
        object.__setattr__(self, "text", normalized_text)

        if self.question_id is None:
            return

        normalized_id = self.question_id.strip()
        if not normalized_id:
            raise ValueError("Adapter question event id must not be blank when provided.")
        if _QUESTION_ID_PATTERN.match(normalized_id) is None:
            raise ValueError(
                "Adapter question event id must use a stable `Q`-prefixed token."
            )
        object.__setattr__(self, "question_id", normalized_id)


def question_policy_from_marker(marker: str) -> QuestionPolicy:
    normalized = marker.strip()
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1].strip()

    if normalized == QuestionPolicy.BLOCKING.value:
        return QuestionPolicy.BLOCKING
    if normalized == QuestionPolicy.NON_BLOCKING.value:
        return QuestionPolicy.NON_BLOCKING

    raise ValueError(
        "Question marker must be one of "
        "`[blocking]`, `[non-blocking]`, `blocking`, or `non-blocking`."
    )


def parse_questions_markdown(markdown_text: str) -> tuple[InterviewQuestion, ...]:
    parsed: list[InterviewQuestion] = []
    seen_ids: set[str] = set()

    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        if stripped.lower() == "- none":
            continue

        match = _QUESTION_LINE_PATTERN.match(stripped)
        if match is None:
            raise ValueError(
                "Invalid question entry at line "
                f"{line_number}: expected `- <QID> [blocking|non-blocking] <text>`."
            )

        question = InterviewQuestion(
            question_id=match.group(1),
            policy=question_policy_from_marker(match.group(2)),
            text=match.group(3),
        )
        if question.question_id in seen_ids:
            raise ValueError(
                f"Duplicate question id `{question.question_id}` in questions markdown content."
            )
        seen_ids.add(question.question_id)
        parsed.append(question)

    return tuple(parsed)


def render_questions_markdown(questions: Iterable[InterviewQuestion]) -> str:
    ordered = tuple(questions)
    lines = ["# Questions", "", "## Questions", ""]
    if not ordered:
        lines.append("- none")
    else:
        for question in ordered:
            lines.append(
                f"- `{question.question_id}` `[{question.policy.value}]` {question.text}"
            )
    lines.append("")
    return "\n".join(lines)


def unresolved_blocking_questions(
    *,
    questions: Iterable[InterviewQuestion],
    resolved_question_ids: Collection[str] = (),
) -> tuple[InterviewQuestion, ...]:
    resolved = {question_id.strip() for question_id in resolved_question_ids if question_id.strip()}
    return tuple(
        question
        for question in questions
        if question.policy == QuestionPolicy.BLOCKING and question.question_id not in resolved
    )


def interview_requires_input(
    *,
    questions: Iterable[InterviewQuestion],
    resolved_question_ids: Collection[str] = (),
) -> bool:
    return bool(
        unresolved_blocking_questions(
            questions=questions,
            resolved_question_ids=resolved_question_ids,
        )
    )


def _next_question_id(existing_ids: set[str]) -> str:
    next_numeric = 1
    for question_id in existing_ids:
        match = _QUESTION_ID_NUMERIC_SUFFIX_PATTERN.match(question_id)
        if match is None:
            continue
        next_numeric = max(next_numeric, int(match.group(1)) + 1)

    candidate = f"Q{next_numeric}"
    while candidate in existing_ids:
        next_numeric += 1
        candidate = f"Q{next_numeric}"
    return candidate


def _questions_from_events(
    *,
    events: Iterable[AdapterQuestionEvent],
    taken_ids: set[str],
) -> tuple[InterviewQuestion, ...]:
    parsed: list[InterviewQuestion] = []
    for event in events:
        question_id = event.question_id
        if question_id is None:
            question_id = _next_question_id(taken_ids)
        if question_id in taken_ids:
            continue
        parsed_question = InterviewQuestion(
            question_id=question_id,
            text=event.text,
            policy=event.policy,
        )
        taken_ids.add(parsed_question.question_id)
        parsed.append(parsed_question)
    return tuple(parsed)


def persist_questions_document(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    stage_output_questions_markdown: str | None = None,
    adapter_question_events: Iterable[AdapterQuestionEvent] = (),
) -> Path:
    questions_path = workspace_root / "workitems" / work_item / "stages" / stage / "questions.md"
    questions_path.parent.mkdir(parents=True, exist_ok=True)

    if stage_output_questions_markdown is not None:
        base_questions = parse_questions_markdown(stage_output_questions_markdown)
    elif questions_path.exists():
        base_questions = parse_questions_markdown(questions_path.read_text(encoding="utf-8"))
    else:
        base_questions = ()

    taken_ids = {question.question_id for question in base_questions}
    event_questions = _questions_from_events(events=adapter_question_events, taken_ids=taken_ids)
    merged = (*base_questions, *event_questions)

    questions_path.write_text(render_questions_markdown(merged), encoding="utf-8")
    return questions_path


def interview_supported() -> bool:
    return True

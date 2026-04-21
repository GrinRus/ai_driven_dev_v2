from __future__ import annotations

import re
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from enum import StrEnum


class QuestionPolicy(StrEnum):
    BLOCKING = "blocking"
    NON_BLOCKING = "non-blocking"


_QUESTION_ID_PATTERN = re.compile(r"^Q[\w-]*$")


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


def interview_supported() -> bool:
    return True

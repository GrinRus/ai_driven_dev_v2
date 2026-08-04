from __future__ import annotations

import re
from dataclasses import dataclass

INLINE_CODE_PATTERN = re.compile(r"(?<!`)`(?!`)(.*?)(?<!`)`(?!`)", flags=re.DOTALL)
PLACEHOLDER_PATTERN = re.compile(r"\b(TBD|TODO|TBA|N/A)\b|\.{3}", flags=re.IGNORECASE)
PLACEHOLDER_EXAMPLE_CONTEXT_PATTERN = re.compile(
    r"\b(placeholder|literal|token|sentinel|example|marker|entr(?:y|ies)|value)s?\b",
    flags=re.IGNORECASE,
)
PLACEHOLDER_NEGATED_EXAMPLE_PATTERN = re.compile(
    r"\b(no|not|none|without|free of)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class PlaceholderOccurrence:
    token: str
    line_number: int


def has_non_placeholder_text(text: str) -> bool:
    return not contains_placeholder_content(text)


def contains_placeholder_content(text: str) -> bool:
    return bool(find_placeholder_occurrences(text))


def find_placeholder_occurrences(text: str) -> tuple[PlaceholderOccurrence, ...]:
    placeholder_matches = tuple(PLACEHOLDER_PATTERN.finditer(text))
    if not placeholder_matches:
        return ()

    inline_code_matches = tuple(INLINE_CODE_PATTERN.finditer(text))
    occurrences: list[PlaceholderOccurrence] = []
    context_matches: list[re.Match[str]] = []
    for placeholder_match in placeholder_matches:
        inline_code_match = inline_code_match_for_placeholder(
            placeholder_match=placeholder_match,
            inline_code_matches=inline_code_matches,
        )
        if inline_code_match is None:
            if placeholder_outside_inline_code_is_content(text, placeholder_match):
                occurrences.append(
                    PlaceholderOccurrence(
                        token=placeholder_match.group(0),
                        line_number=text.count("\n", 0, placeholder_match.start()) + 1,
                    )
                )
            continue

        if inline_placeholder_requires_context(placeholder_match, inline_code_match):
            context_matches.append(placeholder_match)

    if context_matches and inline_placeholder_context_is_content(text):
        occurrences.extend(
            PlaceholderOccurrence(
                token=placeholder_match.group(0),
                line_number=text.count("\n", 0, placeholder_match.start()) + 1,
            )
            for placeholder_match in context_matches
        )

    return tuple(occurrences)


def inline_code_match_for_placeholder(
    *,
    placeholder_match: re.Match[str],
    inline_code_matches: tuple[re.Match[str], ...],
) -> re.Match[str] | None:
    return next(
        (
            code_match
            for code_match in inline_code_matches
            if code_match.start() <= placeholder_match.start()
            and placeholder_match.end() <= code_match.end()
        ),
        None,
    )


def placeholder_outside_inline_code_is_content(
    text: str,
    placeholder_match: re.Match[str],
) -> bool:
    if (
        placeholder_match.group(0) == "..."
        and not is_standalone_ellipsis_placeholder(text, placeholder_match)
    ):
        return False
    if is_negated_placeholder_example_line(text, placeholder_match):
        return False
    return True


def inline_placeholder_requires_context(
    placeholder_match: re.Match[str],
    inline_code_match: re.Match[str],
) -> bool:
    inline_code_text = inline_code_match.group(1).strip()
    return placeholder_match.group(0) != "..." or inline_code_text == "..."


def inline_placeholder_context_is_content(text: str) -> bool:
    text_without_inline_code = INLINE_CODE_PATTERN.sub("", text)
    if not text_without_inline_code.strip():
        return True

    return PLACEHOLDER_EXAMPLE_CONTEXT_PATTERN.search(text_without_inline_code) is None


def is_negated_placeholder_example_line(
    text: str,
    placeholder_match: re.Match[str],
) -> bool:
    line_start = text.rfind("\n", 0, placeholder_match.start()) + 1
    line_end = text.find("\n", placeholder_match.end())
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]

    for candidate in (line, placeholder_sentence_context(text, placeholder_match)):
        if PLACEHOLDER_EXAMPLE_CONTEXT_PATTERN.search(candidate) is None:
            continue
        if PLACEHOLDER_NEGATED_EXAMPLE_PATTERN.search(candidate) is None:
            continue

        candidate_without_placeholders = PLACEHOLDER_PATTERN.sub("", candidate)
        if re.search(r"[A-Za-z]{4,}", candidate_without_placeholders):
            return True

    return False


def placeholder_sentence_context(text: str, placeholder_match: re.Match[str]) -> str:
    sentence_start = 0
    for marker in ("\n\n", ". ", ".\n", "! ", "!\n", "? ", "?\n"):
        marker_index = text.rfind(marker, 0, placeholder_match.start())
        if marker_index != -1:
            sentence_start = max(sentence_start, marker_index + len(marker))

    sentence_end = len(text)
    for marker in ("\n\n", ". ", ".\n", "! ", "!\n", "? ", "?\n"):
        marker_index = text.find(marker, placeholder_match.end())
        if marker_index != -1:
            sentence_end = min(sentence_end, marker_index + len(marker.rstrip()))

    return text[sentence_start:sentence_end]


def is_standalone_ellipsis_placeholder(
    text: str,
    placeholder_match: re.Match[str],
) -> bool:
    line_start = text.rfind("\n", 0, placeholder_match.start()) + 1
    line_end = text.find("\n", placeholder_match.end())
    if line_end == -1:
        line_end = len(text)

    line = text[line_start:line_end]
    match_start = placeholder_match.start() - line_start
    match_end = placeholder_match.end() - line_start
    before = line[:match_start].strip(" \t-*_`\"'")
    after = line[match_end:].strip(" \t-*_`\"'")

    if before and after:
        return False

    normalized_line = line.strip()
    if re.fullmatch(r"[-*]?\s*`?\.{3}`?", normalized_line):
        return True

    return bool(
        re.search(
            r"\b(placeholder|fill|details|content|unknown|later|todo|tbd)\b",
            line,
            flags=re.IGNORECASE,
        )
    )


__all__ = [
    "PlaceholderOccurrence",
    "contains_placeholder_content",
    "find_placeholder_occurrences",
    "has_non_placeholder_text",
    "inline_code_match_for_placeholder",
    "inline_placeholder_context_is_content",
    "inline_placeholder_requires_context",
    "is_negated_placeholder_example_line",
    "is_standalone_ellipsis_placeholder",
    "placeholder_outside_inline_code_is_content",
    "placeholder_sentence_context",
]

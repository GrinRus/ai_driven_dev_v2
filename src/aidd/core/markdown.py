from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_PATTERN = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
_FENCE_PREFIXES = ("```", "~~~")
_INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
_STAGE_HEADING_REQUIREMENT_PATTERN = re.compile(
    r"required heading coverage in\s+`([^`]+)`\s*\((.+)\)",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class MarkdownHeading:
    level: int
    title: str
    line_number: int


def normalize_heading(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def extract_section_lines(markdown_text: str, heading: str) -> list[str]:
    target_heading = f"## {heading}".lower()
    in_section = False
    section_lines: list[str] = []

    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped.lower() == target_heading
            continue
        if in_section:
            section_lines.append(raw_line)

    return section_lines


def extract_inline_code_tokens(text: str) -> tuple[str, ...]:
    return tuple(token.strip() for token in _INLINE_CODE_PATTERN.findall(text) if token.strip())


def extract_bullets(markdown_text: str, heading: str) -> tuple[str, ...]:
    items: list[str] = []
    for line in extract_section_lines(markdown_text=markdown_text, heading=heading):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        bullet_body = stripped.removeprefix("- ").strip()
        inline_code_paths = extract_inline_code_tokens(bullet_body)
        if inline_code_paths:
            items.extend(inline_code_paths)
            continue
        fallback_item = bullet_body.strip("`")
        if fallback_item:
            items.append(fallback_item)
    return tuple(items)


def extract_paragraph(markdown_text: str, heading: str) -> str | None:
    lines = extract_section_lines(markdown_text=markdown_text, heading=heading)
    parts = [line.strip() for line in lines if line.strip()]
    if not parts:
        return None
    return " ".join(parts)


def extract_required_sections_from_document_contract(contract_text: str) -> tuple[str, ...]:
    sections: list[str] = []
    for line in extract_section_lines(contract_text, heading="Required sections"):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        sections.extend(extract_inline_code_tokens(stripped))
    return tuple(dict.fromkeys(section for section in sections if section))


def extract_stage_required_heading_map(stage_contract_text: str) -> dict[str, tuple[str, ...]]:
    requirements: dict[str, tuple[str, ...]] = {}
    for line in extract_section_lines(stage_contract_text, heading="Validation focus"):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue

        match = _STAGE_HEADING_REQUIREMENT_PATTERN.search(stripped)
        if match is None:
            continue

        document_name = match.group(1).strip()
        sections = extract_inline_code_tokens(match.group(2))
        if sections:
            requirements[document_name] = sections

    return requirements


def extract_markdown_headings(markdown_text: str) -> tuple[MarkdownHeading, ...]:
    headings: list[MarkdownHeading] = []
    in_fence = False
    active_fence_prefix: str | None = None

    for line_number, raw_line in enumerate(markdown_text.splitlines(), start=1):
        stripped = raw_line.lstrip()

        fence_prefix = next(
            (prefix for prefix in _FENCE_PREFIXES if stripped.startswith(prefix)),
            None,
        )
        if fence_prefix is not None:
            if not in_fence:
                in_fence = True
                active_fence_prefix = fence_prefix
            elif active_fence_prefix is not None and stripped.startswith(active_fence_prefix):
                in_fence = False
                active_fence_prefix = None
            continue

        if in_fence:
            continue

        leading_spaces = len(raw_line) - len(raw_line.lstrip(" "))
        if leading_spaces > 3:
            continue

        match = _HEADING_PATTERN.match(raw_line.lstrip(" "))
        if match is None:
            continue

        level = len(match.group(1))
        title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
        if not title:
            continue

        headings.append(MarkdownHeading(level=level, title=title, line_number=line_number))

    return tuple(headings)


@dataclass(frozen=True, slots=True)
class MarkdownSectionIndex:
    headings: tuple[MarkdownHeading, ...]
    markdown_lines: tuple[str, ...]
    headings_by_title: dict[str, tuple[tuple[int, MarkdownHeading], ...]]

    @classmethod
    def from_markdown(cls, markdown_text: str) -> MarkdownSectionIndex:
        headings = extract_markdown_headings(markdown_text)
        grouped: dict[str, list[tuple[int, MarkdownHeading]]] = {}
        for index, heading in enumerate(headings):
            grouped.setdefault(normalize_heading(heading.title), []).append((index, heading))
        return cls(
            headings=headings,
            markdown_lines=tuple(markdown_text.splitlines()),
            headings_by_title={
                title: tuple(matches) for title, matches in grouped.items()
            },
        )

    def matches(self, heading: str) -> tuple[tuple[int, MarkdownHeading], ...]:
        return self.headings_by_title.get(normalize_heading(heading), ())

    def first_match(
        self,
        candidates: tuple[str, ...],
    ) -> tuple[int, MarkdownHeading] | None:
        for candidate in candidates:
            matches = self.matches(candidate)
            if matches:
                return matches[0]
        return None

    def section_content(self, heading_index: int) -> str:
        heading = self.headings[heading_index]
        start_index = heading.line_number
        end_index = len(self.markdown_lines)

        for next_heading in self.headings[heading_index + 1 :]:
            if next_heading.level <= heading.level:
                end_index = next_heading.line_number - 1
                break

        return "\n".join(self.markdown_lines[start_index:end_index]).strip()

    def section_has_meaningful_content(self, heading_index: int) -> bool:
        heading = self.headings[heading_index]
        start_index = heading.line_number
        end_index = len(self.markdown_lines)

        for next_heading in self.headings[heading_index + 1 :]:
            if next_heading.level <= heading.level:
                end_index = next_heading.line_number - 1
                break

        return any(line.strip() for line in self.markdown_lines[start_index:end_index])

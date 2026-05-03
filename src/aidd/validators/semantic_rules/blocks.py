from __future__ import annotations

import re


def has_bullet_items(section_content: str) -> bool:
    return any(line.strip().startswith("- ") for line in section_content.splitlines())


def extract_bullet_items(section_content: str) -> tuple[str, ...]:
    return tuple(
        line.strip()[2:].strip()
        for line in section_content.splitlines()
        if line.strip().startswith("- ")
    )


def extract_markdown_list_items(section_content: str) -> tuple[str, ...]:
    items: list[str] = []
    for line in section_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
            continue
        ordered_match = re.match(r"\d+[.)]\s+(.+)", stripped)
        if ordered_match is not None:
            items.append(ordered_match.group(1).strip())
    return tuple(items)


def extract_top_level_bullet_blocks(section_content: str) -> tuple[str, ...]:
    blocks: list[list[str]] = []
    current_block: list[str] | None = None
    in_fenced_code = False

    for line in section_content.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fenced_code = not in_fenced_code
            if current_block is not None:
                current_block.append(stripped)
            continue

        if in_fenced_code:
            if current_block is not None:
                current_block.append(stripped)
            continue

        if line.startswith("- "):
            current_block = [line[2:].strip()]
            blocks.append(current_block)
            continue

        if current_block is not None:
            current_block.append(line.strip())

    return tuple(
        "\n".join(line for line in block if line).strip()
        for block in blocks
        if any(line.strip() for line in block)
    )


def extract_subheading_blocks(section_content: str, *, level: int) -> tuple[str, ...]:
    marker = f"{'#' * level} "
    blocks: list[list[str]] = []
    current_block: list[str] | None = None

    for line in section_content.splitlines():
        if line.startswith(marker):
            current_block = [line.strip()]
            blocks.append(current_block)
            continue

        if current_block is not None:
            current_block.append(line.strip())

    return tuple(
        "\n".join(line for line in block if line).strip()
        for block in blocks
        if any(line.strip() for line in block)
    )


def is_markdown_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) is not None for cell in cells
    )


def extract_markdown_table_rows(section_content: str) -> tuple[str, ...]:
    rows: list[str] = []
    headers: list[str] | None = None
    for line in section_content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            headers = None
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if is_markdown_table_separator(cells):
            continue
        if headers is None:
            headers = cells
            continue
        labeled_cells: list[str] = []
        for index, cell in enumerate(cells):
            if not cell:
                continue
            header = (
                headers[index]
                if index < len(headers) and headers[index]
                else f"Column {index + 1}"
            )
            labeled_cells.append(f"{header}: {cell}")
        if labeled_cells:
            rows.append(" | ".join(labeled_cells))
    return tuple(rows)


def extract_risk_blocks(section_content: str) -> tuple[str, ...]:
    subsection_blocks = extract_subheading_blocks(section_content, level=3)
    if subsection_blocks:
        return subsection_blocks
    bullet_blocks = extract_top_level_bullet_blocks(section_content)
    if bullet_blocks:
        return bullet_blocks
    return extract_markdown_table_rows(section_content)


def extract_implementation_verification_blocks(section_content: str) -> tuple[str, ...]:
    subsection_blocks = extract_subheading_blocks(section_content, level=3)
    if subsection_blocks:
        return subsection_blocks
    return extract_top_level_bullet_blocks(section_content)


__all__ = [
    "extract_bullet_items",
    "extract_implementation_verification_blocks",
    "extract_markdown_list_items",
    "extract_markdown_table_rows",
    "extract_risk_blocks",
    "extract_subheading_blocks",
    "extract_top_level_bullet_blocks",
    "has_bullet_items",
    "is_markdown_table_separator",
]

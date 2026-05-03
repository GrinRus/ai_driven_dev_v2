from __future__ import annotations

import re

CITATION_ID_PATTERN = re.compile(r"\[(S\d+)\]")
MILESTONE_ID_PATTERN = re.compile(r"\b(M\d+)\b", flags=re.IGNORECASE)
TASKLIST_TASK_ID_PATTERN = re.compile(
    r"\b([A-Z][A-Z0-9]{0,15}-\d+|T\d+)\b",
)


def extract_citation_ids(text: str) -> set[str]:
    return {match.group(1) for match in CITATION_ID_PATTERN.finditer(text)}


def extract_milestone_ids(text: str) -> set[str]:
    return {match.group(1).upper() for match in MILESTONE_ID_PATTERN.finditer(text)}


def extract_tasklist_task_ids(text: str) -> set[str]:
    task_ids = {match.group(1).upper() for match in TASKLIST_TASK_ID_PATTERN.finditer(text)}
    tl_ids = {task_id for task_id in task_ids if task_id.startswith("TL-")}
    if tl_ids:
        return tl_ids
    compact_t_ids = {task_id for task_id in task_ids if re.fullmatch(r"T\d+", task_id)}
    if compact_t_ids:
        return compact_t_ids
    return task_ids


__all__ = [
    "CITATION_ID_PATTERN",
    "MILESTONE_ID_PATTERN",
    "TASKLIST_TASK_ID_PATTERN",
    "extract_citation_ids",
    "extract_milestone_ids",
    "extract_tasklist_task_ids",
]

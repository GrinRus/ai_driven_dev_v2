from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aidd.core.allowed_write_scope import AllowedWriteScope, resolve_allowed_write_scope
from aidd.core.task_plan import TaskExecutionMode

_TASK_ID_LINE = re.compile(r"Task id\s*:\s*`([^`]+)`", re.IGNORECASE)
_EXECUTION_MODE_LINE = re.compile(r"Execution mode\s*:\s*`([^`]+)`", re.IGNORECASE)
_AC_ID = re.compile(
    r"^\s*-\s+`?((?:[A-Z][A-Z0-9]{0,15}-\d+|T\d+)-AC\d+)`?\s*:",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True, slots=True)
class ImplementationEvidenceContext:
    selected_task_id: str | None
    acceptance_ids: tuple[str, ...]
    allowed_write_scope: AllowedWriteScope | None
    authored_verification: str | None
    required_verification_commands: tuple[str, ...]
    execution_mode: TaskExecutionMode


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _section_content(document: str, heading: str) -> str:
    """Return one level-two Markdown section without mining prose references."""

    target = heading.casefold()
    lines = document.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        match = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if match is not None and match.group(1).strip("` ").casefold() == target:
            start = index + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        if re.match(r"^##\s+", lines[index].strip()):
            end = index
            break
    return "\n".join(lines[start:end])


def _verification_commands(*documents: str | None) -> tuple[str, ...]:
    command_prefixes = (
        "uv ",
        "pytest ",
        "python ",
        "ruff ",
        "mypy ",
        "git ",
        "npm ",
        "pnpm ",
        "yarn ",
        "cargo ",
        "go test",
    )
    commands: list[str] = []
    for document in documents:
        for value in re.findall(r"`([^`]+)`", document or ""):
            normalized = value.strip()
            if normalized.casefold().startswith(command_prefixes):
                commands.append(normalized)
    return tuple(dict.fromkeys(commands))


def load_implementation_evidence_context(
    *, workspace_root: Path, work_item: str
) -> ImplementationEvidenceContext:
    context_root = workspace_root / "workitems" / work_item / "context"
    selection = _read_optional(context_root / "task-selection.md")
    verification = _read_optional(context_root / "verification-output.md")
    selected_match = _TASK_ID_LINE.search(selection or "")
    execution_mode_match = _EXECUTION_MODE_LINE.search(selection or "")
    execution_mode = TaskExecutionMode.REPOSITORY_CHANGE
    if (
        execution_mode_match is not None
        and execution_mode_match.group(1).casefold()
        == TaskExecutionMode.VERIFICATION_ONLY.value
    ):
        execution_mode = TaskExecutionMode.VERIFICATION_ONLY
    acceptance_section = _section_content(selection or "", "Acceptance criteria")
    return ImplementationEvidenceContext(
        selected_task_id=(selected_match.group(1).upper() if selected_match else None),
        acceptance_ids=tuple(
            dict.fromkeys(match.group(1).upper() for match in _AC_ID.finditer(acceptance_section))
        ),
        allowed_write_scope=resolve_allowed_write_scope(workspace_root, work_item),
        authored_verification=verification,
        required_verification_commands=_verification_commands(selection, verification),
        execution_mode=execution_mode,
    )


__all__ = ["ImplementationEvidenceContext", "load_implementation_evidence_context"]

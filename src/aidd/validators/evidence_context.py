from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TASK_ID_LINE = re.compile(r"Task id\s*:\s*`([^`]+)`", re.IGNORECASE)
_AC_ID = re.compile(r"`?((?:[A-Z][A-Z0-9]{0,15}-\d+|T\d+)-AC\d+)`?")


@dataclass(frozen=True, slots=True)
class ImplementationEvidenceContext:
    selected_task_id: str | None
    acceptance_ids: tuple[str, ...]
    allowed_scope_paths: tuple[str, ...]
    authored_verification: str | None
    required_verification_commands: tuple[str, ...]


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _backticked_paths(text: str | None) -> tuple[str, ...]:
    if text is None:
        return ()
    values = []
    for value in re.findall(r"`([^`]+)`", text):
        normalized = value.strip().strip("/")
        if "/" in normalized or "." in Path(normalized).name:
            values.append(normalized)
    return tuple(dict.fromkeys(values))


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
    allowed_scope = _read_optional(context_root / "allowed-write-scope.md")
    verification = _read_optional(context_root / "verification-output.md")
    selected_match = _TASK_ID_LINE.search(selection or "")
    return ImplementationEvidenceContext(
        selected_task_id=(selected_match.group(1).upper() if selected_match else None),
        acceptance_ids=tuple(
            dict.fromkeys(match.group(1).upper() for match in _AC_ID.finditer(selection or ""))
        ),
        allowed_scope_paths=_backticked_paths(allowed_scope),
        authored_verification=verification,
        required_verification_commands=_verification_commands(selection, verification),
    )


__all__ = ["ImplementationEvidenceContext", "load_implementation_evidence_context"]

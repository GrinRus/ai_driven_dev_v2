from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType

from aidd.core.resources import default_document_contracts_root
from aidd.core.stages import is_valid_stage


class OwnershipRegistryError(ValueError):
    """Raised when the canonical document ownership matrix is invalid."""


class OwnershipClass(StrEnum):
    RUNTIME_CONTENT = "Runtime content"
    AIDD_WORKFLOW_RECORD = "AIDD workflow record"
    AIDD_CONTROL_DOCUMENT = "AIDD control document"
    INTERVIEW_LEDGER = "Interview ledger"
    RAW_CANDIDATE_EVIDENCE = "Raw candidate evidence"


@dataclass(frozen=True, slots=True)
class OwnershipMatrixRow:
    """One normalized row from the canonical ownership matrix."""

    path_pattern: str
    stages: tuple[str, ...] | None
    ownership_class: OwnershipClass
    create: str
    mutate: str
    validate: str
    publish: str
    ui_authoring: str

    def applies_to(self, stage: str) -> bool:
        if not is_valid_stage(stage):
            raise OwnershipRegistryError(f"Unknown stage: {stage}")
        return self.stages is None or stage in self.stages


@dataclass(frozen=True, slots=True)
class DocumentOwnershipRegistry:
    """Immutable, ownership-typed view of the canonical matrix."""

    rows: tuple[OwnershipMatrixRow, ...]

    def __post_init__(self) -> None:
        if not self.rows:
            raise OwnershipRegistryError("Ownership matrix must declare at least one row")
        paths = [row.path_pattern for row in self.rows]
        if len(paths) != len(set(paths)):
            raise OwnershipRegistryError("Ownership matrix contains duplicate path patterns")

    @property
    def by_path_pattern(self) -> Mapping[str, OwnershipMatrixRow]:
        return MappingProxyType({row.path_pattern: row for row in self.rows})

    def row_for(self, path_pattern: str) -> OwnershipMatrixRow:
        try:
            return self.by_path_pattern[path_pattern]
        except KeyError as exc:
            raise OwnershipRegistryError(
                f"Unknown document path pattern: {path_pattern}"
            ) from exc

    def for_stage(self, stage: str) -> tuple[OwnershipMatrixRow, ...]:
        if not is_valid_stage(stage):
            raise OwnershipRegistryError(f"Unknown stage: {stage}")
        return tuple(row for row in self.rows if row.applies_to(stage))

DEFAULT_OWNERSHIP_MATRIX_PATH = default_document_contracts_root() / "ownership-matrix.md"

_EXPECTED_HEADER = (
    "Declared document path pattern",
    "Stage(s)",
    "Ownership class",
    "Create",
    "Mutate",
    "Validate",
    "Publish",
    "UI authoring",
)
_HEADER_NORMALIZER = re.compile(r"\s+")
_HEADING_PATTERN = re.compile(r"^##[ \t]+(.+?)[ \t]*#*[ \t]*$")
_ANY_STAGE = "Any stage"
_BACKTICKED_VALUE = re.compile(r"^`([^`]+)`$")
_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")


def _stage_path(filename: str) -> str:
    return f"workitems/<id>/stages/<stage>/{filename}"


_EXPECTED_ROW_SHAPES: dict[str, tuple[tuple[str, ...] | None, OwnershipClass]] = {
    _stage_path("idea-brief.md"): (("idea",), OwnershipClass.RUNTIME_CONTENT),
    _stage_path("research-notes.md"): (("research",), OwnershipClass.RUNTIME_CONTENT),
    _stage_path("plan.md"): (("plan",), OwnershipClass.RUNTIME_CONTENT),
    _stage_path("review-spec-report.md"): (("review-spec",), OwnershipClass.RUNTIME_CONTENT),
    _stage_path("tasklist.md"): (("tasklist",), OwnershipClass.RUNTIME_CONTENT),
    _stage_path("implementation-report.md"): (("implement",), OwnershipClass.RUNTIME_CONTENT),
    _stage_path("review-report.md"): (("review",), OwnershipClass.RUNTIME_CONTENT),
    _stage_path("qa-report.md"): (("qa",), OwnershipClass.RUNTIME_CONTENT),
    _stage_path("questions.md"): (None, OwnershipClass.INTERVIEW_LEDGER),
    _stage_path("answers.md"): (None, OwnershipClass.INTERVIEW_LEDGER),
    _stage_path("stage-result.md"): (None, OwnershipClass.AIDD_WORKFLOW_RECORD),
    _stage_path("validator-report.md"): (None, OwnershipClass.AIDD_WORKFLOW_RECORD),
    _stage_path("repair-brief.md"): (None, OwnershipClass.AIDD_CONTROL_DOCUMENT),
    "workitems/<id>/stages/<stage>/operator-requests/request-<n>.md": (
        None,
        OwnershipClass.AIDD_CONTROL_DOCUMENT,
    ),
    "reports/runs/<id>/attempts/<attempt>/runtime.log": (
        None,
        OwnershipClass.RAW_CANDIDATE_EVIDENCE,
    ),
    "reports/runs/<id>/attempts/<attempt>/runtime.jsonl": (
        None,
        OwnershipClass.RAW_CANDIDATE_EVIDENCE,
    ),
    "reports/runs/<id>/attempts/<attempt>/events.jsonl": (
        None,
        OwnershipClass.RAW_CANDIDATE_EVIDENCE,
    ),
    "reports/runs/<id>/attempts/<attempt>/runtime-exit.json": (
        None,
        OwnershipClass.RAW_CANDIDATE_EVIDENCE,
    ),
    "reports/runs/<id>/attempts/<attempt>/operator-requests.jsonl": (
        None,
        OwnershipClass.RAW_CANDIDATE_EVIDENCE,
    ),
    "reports/runs/<id>/attempts/<attempt>/operator-decisions.jsonl": (
        None,
        OwnershipClass.RAW_CANDIDATE_EVIDENCE,
    ),
}


def _split_table_line(line: str, *, line_number: int) -> tuple[str, ...]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise OwnershipRegistryError(
            f"Malformed ownership matrix table row at line {line_number}: expected leading "
            "and trailing '|'."
        )
    cells = tuple(cell.strip() for cell in stripped[1:-1].split("|"))
    if len(cells) != len(_EXPECTED_HEADER):
        raise OwnershipRegistryError(
            f"Malformed ownership matrix table row at line {line_number}: expected "
            f"{len(_EXPECTED_HEADER)} cells, got {len(cells)}."
        )
    return cells


def _normalize_header(cells: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_HEADER_NORMALIZER.sub(" ", cell).strip().lower() for cell in cells)


def _parse_path_pattern(cell: str, *, line_number: int) -> str:
    match = _BACKTICKED_VALUE.fullmatch(cell)
    if match is None or not match.group(1).strip():
        raise OwnershipRegistryError(
            f"Missing or malformed document path pattern at line {line_number}"
        )
    return match.group(1).strip()


def _parse_stages(cell: str, *, line_number: int) -> tuple[str, ...] | None:
    if cell == _ANY_STAGE:
        return None
    match = _BACKTICKED_VALUE.fullmatch(cell)
    if match is None:
        raise OwnershipRegistryError(
            f"Unknown stage scope at line {line_number}: {cell or '<missing>'}"
        )
    stage = match.group(1).strip()
    if not is_valid_stage(stage):
        raise OwnershipRegistryError(f"Unknown stage at line {line_number}: {stage}")
    return (stage,)


def _parse_ownership_class(cell: str, *, line_number: int) -> OwnershipClass:
    try:
        return OwnershipClass(cell)
    except ValueError as exc:
        raise OwnershipRegistryError(
            f"Unknown ownership class at line {line_number}: {cell or '<missing>'}"
        ) from exc


def _canonical_section_lines(markdown_text: str) -> list[tuple[int, str]]:
    lines = markdown_text.splitlines()
    matches = [
        index
        for index, line in enumerate(lines)
        if (match := _HEADING_PATTERN.match(line.strip()))
        and match.group(1).strip().lower() == "canonical matrix"
    ]
    if len(matches) != 1:
        raise OwnershipRegistryError(
            "Ownership matrix must contain exactly one '## Canonical matrix' section"
        )
    start = matches[0] + 1
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].lstrip().startswith("## "):
            end = index
            break
    return [(index + 1, lines[index]) for index in range(start, end)]


def parse_ownership_matrix(
    markdown_text: str,
    *,
    expected_row_shapes: dict[str, tuple[tuple[str, ...] | None, OwnershipClass]]
    | None = None,
) -> DocumentOwnershipRegistry:
    """Parse and validate the canonical Markdown ownership matrix.

    Validation is intentionally strict: malformed cells, unknown stages/owners, duplicate or
    conflicting path patterns, and missing/extra canonical rows all stop loading before runtime
    execution can use an incomplete registry.
    """

    expected = _EXPECTED_ROW_SHAPES if expected_row_shapes is None else expected_row_shapes
    section_lines = _canonical_section_lines(markdown_text)
    table_start: int | None = None
    for line_number, line in section_lines:
        if line.strip().startswith("|"):
            table_start = line_number
            break
    if table_start is None:
        raise OwnershipRegistryError("Canonical matrix section is missing its table")

    offset = table_start - section_lines[0][0]
    table_lines = section_lines[offset:]
    header = _split_table_line(table_lines[0][1], line_number=table_lines[0][0])
    if _normalize_header(header) != _normalize_header(_EXPECTED_HEADER):
        raise OwnershipRegistryError(
            "Ownership matrix table header does not match the canonical eight-column schema"
        )
    if len(table_lines) < 2:
        raise OwnershipRegistryError("Ownership matrix table is missing its separator row")
    separator = _split_table_line(table_lines[1][1], line_number=table_lines[1][0])
    if not all(_SEPARATOR_CELL.fullmatch(cell) for cell in separator):
        raise OwnershipRegistryError("Ownership matrix table has an invalid separator row")

    rows: list[OwnershipMatrixRow] = []
    seen_paths: dict[str, int] = {}
    for line_number, line in table_lines[2:]:
        if not line.strip():
            continue
        if not line.strip().startswith("|"):
            continue
        cells = _split_table_line(line, line_number=line_number)
        path_pattern = _parse_path_pattern(cells[0], line_number=line_number)
        if path_pattern in seen_paths:
            previous = seen_paths[path_pattern]
            raise OwnershipRegistryError(
                f"Duplicate or conflicting ownership row for {path_pattern} at line "
                f"{line_number} (first declared at line {previous})"
            )
        seen_paths[path_pattern] = line_number
        stages = _parse_stages(cells[1], line_number=line_number)
        owner = _parse_ownership_class(cells[2], line_number=line_number)
        permissions = cells[3:]
        if any(not permission for permission in permissions):
            raise OwnershipRegistryError(
                f"Missing ownership permission at line {line_number} for {path_pattern}"
            )
        expected_shape = expected.get(path_pattern)
        if expected_shape is None:
            raise OwnershipRegistryError(
                f"Unknown document path pattern at line {line_number}: {path_pattern}"
            )
        expected_stages, expected_owner = expected_shape
        if stages != expected_stages or owner is not expected_owner:
            raise OwnershipRegistryError(
                f"Conflicting ownership declaration for {path_pattern} at line {line_number}: "
                f"expected stage scope/owner {expected_stages!r}/{expected_owner.value!r}"
            )
        rows.append(
            OwnershipMatrixRow(
                path_pattern=path_pattern,
                stages=stages,
                ownership_class=owner,
                create=permissions[0],
                mutate=permissions[1],
                validate=permissions[2],
                publish=permissions[3],
                ui_authoring=permissions[4],
            )
        )

    missing = sorted(set(expected) - set(seen_paths))
    if missing:
        joined = ", ".join(missing)
        raise OwnershipRegistryError(f"Missing ownership matrix rows: {joined}")
    if not rows:
        raise OwnershipRegistryError("Ownership matrix table must contain data rows")
    return DocumentOwnershipRegistry(rows=tuple(rows))


def load_ownership_registry(
    matrix_path: Path = DEFAULT_OWNERSHIP_MATRIX_PATH,
) -> DocumentOwnershipRegistry:
    try:
        markdown_text = matrix_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OwnershipRegistryError(f"Could not read ownership matrix: {matrix_path}") from exc
    return parse_ownership_matrix(markdown_text)


load_document_ownership_registry = load_ownership_registry


__all__ = [
    "DEFAULT_OWNERSHIP_MATRIX_PATH",
    "DocumentOwnershipRegistry",
    "OwnershipClass",
    "OwnershipMatrixRow",
    "OwnershipRegistryError",
    "load_document_ownership_registry",
    "load_ownership_registry",
    "parse_ownership_matrix",
]

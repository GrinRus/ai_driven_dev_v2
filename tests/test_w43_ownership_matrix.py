from __future__ import annotations

import re
from pathlib import Path

from aidd.core.stages import STAGES

_MATRIX_PATH_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|")
_DOCUMENT_RE = re.compile(r"`([^`]+\.md)`")
_OWNERSHIP_CLASSES = {
    "Runtime content",
    "AIDD workflow record",
    "AIDD control document",
    "Interview ledger",
    "Raw candidate evidence",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _section_bullets(text: str, heading: str) -> tuple[tuple[str, ...], ...]:
    section = text.split(f"## {heading}", maxsplit=1)[1]
    section = section.split("\n## ", maxsplit=1)[0]
    return tuple(
        _DOCUMENT_RE.findall(line)
        for line in section.splitlines()
        if line.lstrip().startswith("-")
    )


def _declared_stage_documents(repo_root: Path) -> set[str]:
    documents: set[str] = set()
    for stage in STAGES:
        text = (repo_root / "contracts" / "stages" / f"{stage}.md").read_text(
            encoding="utf-8"
        )
        for matches in (*_section_bullets(text, "Primary output"),
                        *_section_bullets(text, "System-owned control artifacts")):
            documents.update(Path(document).name for document in matches)
        # Conditional interview documents are declared together in one bullet.
        documents.update({"questions.md", "answers.md"})
    return documents


def _matrix_rows(repo_root: Path) -> list[tuple[str, ...]]:
    text = (repo_root / "contracts" / "documents" / "ownership-matrix.md").read_text(
        encoding="utf-8"
    )
    rows: list[tuple[str, ...]] = []
    for line in text.splitlines():
        if not _MATRIX_PATH_RE.match(line):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        rows.append(cells)
    return rows


def test_ownership_matrix_covers_each_declared_stage_document_once() -> None:
    repo_root = _repo_root()
    rows = _matrix_rows(repo_root)
    assert rows
    path_rows = {Path(row[0].strip("`")).name: row for row in rows}
    declared = _declared_stage_documents(repo_root)

    assert declared <= set(path_rows), sorted(declared - set(path_rows))
    assert len(path_rows) == len(rows), "a document path appears in conflicting matrix rows"


def test_ownership_matrix_rows_have_one_owner_and_complete_permissions() -> None:
    rows = _matrix_rows(_repo_root())
    for row in rows:
        assert len(row) == 8, row
        assert row[2] in _OWNERSHIP_CLASSES, row
        assert all(row[index] for index in (1, 3, 4, 5, 6, 7)), row


def test_ownership_matrix_names_every_stage_and_forbids_runtime_terminal_records() -> None:
    repo_root = _repo_root()
    text = (repo_root / "contracts" / "documents" / "ownership-matrix.md").read_text(
        encoding="utf-8"
    )
    for stage in STAGES:
        assert f"`{stage}`" in text
    assert "runtime completion target" in text
    assert "validator-report.md` | Any stage | AIDD workflow record" in text
    assert "stage-result.md` | Any stage | AIDD workflow record" in text

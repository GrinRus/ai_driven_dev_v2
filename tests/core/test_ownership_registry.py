from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.ownership_registry import (
    OwnershipClass,
    OwnershipRegistryError,
    load_ownership_registry,
)
from aidd.core.stages import STAGES


def _matrix_text() -> str:
    path = Path(__file__).parents[2] / "contracts" / "documents" / "ownership-matrix.md"
    return path.read_text(encoding="utf-8")


def _write_matrix(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "ownership-matrix.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_ownership_registry_parses_canonical_rows() -> None:
    registry = load_ownership_registry()

    assert len(registry.rows) == 20
    assert registry.row_for("workitems/<id>/stages/<stage>/idea-brief.md").stages == ("idea",)
    assert registry.row_for("workitems/<id>/stages/<stage>/stage-result.md").ownership_class == (
        OwnershipClass.AIDD_WORKFLOW_RECORD
    )
    assert len(registry.for_stage("qa")) == 13
    assert {
        row
        for row in registry.rows
        if row.ownership_class is OwnershipClass.RUNTIME_CONTENT
    } == {
        registry.row_for(f"workitems/<id>/stages/<stage>/{filename}")
        for filename in (
            "idea-brief.md",
            "research-notes.md",
            "plan.md",
            "review-spec-report.md",
            "tasklist.md",
            "implementation-report.md",
            "review-report.md",
            "qa-report.md",
        )
    }


@pytest.mark.parametrize("stage", STAGES)
def test_stage_specific_rows_have_one_runtime_owner(stage: str) -> None:
    registry = load_ownership_registry()
    rows = tuple(row for row in registry.for_stage(stage) if row.stages == (stage,))

    assert len(rows) == 1
    assert rows[0].ownership_class is OwnershipClass.RUNTIME_CONTENT


def test_missing_matrix_row_fails_closed(tmp_path: Path) -> None:
    text = _matrix_text()
    row = (
        "| `workitems/<id>/stages/<stage>/qa-report.md` | `qa` | Runtime content | "
        "Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | "
        "No; read-only |\n"
    )
    text = text.replace(row, "")

    with pytest.raises(OwnershipRegistryError, match="Missing ownership matrix rows"):
        load_ownership_registry(_write_matrix(tmp_path, text))


def test_duplicate_matrix_row_fails_closed(tmp_path: Path) -> None:
    text = _matrix_text()
    row = (
        "| `workitems/<id>/stages/<stage>/qa-report.md` | `qa` | Runtime content | "
        "Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | "
        "No; read-only |\n"
    )

    with pytest.raises(OwnershipRegistryError, match="Duplicate or conflicting"):
        load_ownership_registry(_write_matrix(tmp_path, text.replace(row, row + row)))


def test_unknown_stage_and_path_fail_closed(tmp_path: Path) -> None:
    unknown_stage = _matrix_text().replace("| `qa` | Runtime content", "| `ship` | Runtime content")
    with pytest.raises(OwnershipRegistryError, match="Unknown stage"):
        load_ownership_registry(_write_matrix(tmp_path, unknown_stage))

    unknown_path = _matrix_text().replace(
        "`workitems/<id>/stages/<stage>/qa-report.md`",
        "`workitems/<id>/stages/<stage>/unknown.md`",
    )
    with pytest.raises(OwnershipRegistryError, match="Unknown document path pattern"):
        load_ownership_registry(_write_matrix(tmp_path, unknown_path))

    extra_row = (
        "| `workitems/<id>/stages/<stage>/unknown.md` | Any stage | Runtime content | "
        "Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | "
        "No; read-only |\n"
    )
    extra_path = _matrix_text().replace(
        "\n`context/*.md`, upstream stage inputs,",
        f"\n{extra_row}\n`context/*.md`, upstream stage inputs,",
    )
    with pytest.raises(OwnershipRegistryError, match="Unknown document path pattern"):
        load_ownership_registry(_write_matrix(tmp_path, extra_path))


def test_conflicting_owner_fails_closed(tmp_path: Path) -> None:
    text = _matrix_text().replace(
        "| `workitems/<id>/stages/<stage>/qa-report.md` | `qa` | Runtime content",
        "| `workitems/<id>/stages/<stage>/qa-report.md` | `qa` | AIDD control document",
    )

    with pytest.raises(OwnershipRegistryError, match="Conflicting ownership declaration"):
        load_ownership_registry(_write_matrix(tmp_path, text))


def test_unknown_stage_query_fails_closed() -> None:
    with pytest.raises(OwnershipRegistryError, match="Unknown stage"):
        load_ownership_registry().for_stage("ship")

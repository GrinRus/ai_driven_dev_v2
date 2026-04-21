from __future__ import annotations

from pathlib import Path

import pytest

from aidd.validators.document_loader import (
    DocumentLoadError,
    DocumentPathError,
    load_markdown_document,
    resolve_common_document_path,
    resolve_stage_document_path,
    resolve_stage_root,
)


def test_resolve_stage_root_uses_workspace_layout(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    resolved = resolve_stage_root(workspace_root=workspace_root, work_item="WI-001", stage="plan")

    assert resolved == workspace_root / "workitems" / "WI-001" / "stages" / "plan"


def test_resolve_common_document_path_targets_stage_root(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    resolved = resolve_common_document_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        document_name="stage-result.md",
    )

    expected = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "stage-result.md"
    assert resolved == expected


def test_resolve_stage_document_path_targets_io_directory(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    resolved = resolve_stage_document_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        io_direction="output",
        document_name="plan.md",
    )

    expected = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    assert resolved == expected


def test_resolve_common_document_path_rejects_unknown_document(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    with pytest.raises(DocumentPathError, match="Unknown common document"):
        resolve_common_document_path(
            workspace_root=workspace_root,
            work_item="WI-001",
            stage="plan",
            document_name="plan.md",
        )


def test_resolve_stage_document_path_rejects_parent_traversal(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    with pytest.raises(DocumentPathError, match="simple filename"):
        resolve_stage_document_path(
            workspace_root=workspace_root,
            work_item="WI-001",
            stage="plan",
            io_direction="input",
            document_name="../escape.md",
        )


def test_resolve_stage_root_rejects_workspace_escape(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    with pytest.raises(DocumentPathError, match="escapes workspace root"):
        resolve_stage_root(workspace_root=workspace_root, work_item="../../outside", stage="plan")


def test_load_markdown_document_returns_raw_body_and_metadata(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    doc_path.parent.mkdir(parents=True)

    body = "# Plan\n\n- item\n"
    doc_path.write_text(body, encoding="utf-8")

    loaded = load_markdown_document(path=doc_path, workspace_root=workspace_root)

    assert loaded.body == body
    assert loaded.metadata.path == doc_path.resolve()
    assert loaded.metadata.workspace_relative_path == Path(
        "workitems/WI-001/stages/plan/output/plan.md"
    )
    assert loaded.metadata.size_bytes == len(body.encode("utf-8"))
    assert loaded.metadata.modified_time_epoch_s > 0


def test_load_markdown_document_rejects_non_markdown_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.txt"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_text("not markdown", encoding="utf-8")

    with pytest.raises(DocumentPathError, match="Expected a Markdown file"):
        load_markdown_document(path=doc_path, workspace_root=workspace_root)


def test_load_markdown_document_rejects_missing_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"

    with pytest.raises(DocumentLoadError, match="does not exist"):
        load_markdown_document(path=doc_path, workspace_root=workspace_root)

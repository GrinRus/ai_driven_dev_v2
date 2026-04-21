from __future__ import annotations

from pathlib import Path

import pytest

from aidd.validators.document_loader import (
    DocumentPathError,
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

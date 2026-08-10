from __future__ import annotations

from pathlib import Path

from aidd.validators.evidence_context import load_implementation_evidence_context


def test_acceptance_ids_ignore_cross_task_references_in_criterion_prose(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    selection = workspace_root / "workitems" / "WI-1" / "context" / "task-selection.md"
    selection.parent.mkdir(parents=True)
    selection.write_text(
        "# Task Selection\n\n"
        "## Selected task\n\n"
        "- Task id: `T3`\n"
        "- Execution mode: `repository-change`\n\n"
        "## Acceptance criteria\n\n"
        "- `T3-AC1`: The test covers the header-only path.\n"
        "- `T3-AC2`: Preserve the prerequisite evidence from `T2-AC2` when useful.\n"
        "- `T3-AC3`: Keep the bounded CLI scope.\n\n"
        "## Dependencies\n\n"
        "- `T2`\n",
        encoding="utf-8",
    )

    context = load_implementation_evidence_context(
        workspace_root=workspace_root,
        work_item="WI-1",
    )

    assert context.selected_task_id == "T3"
    assert context.acceptance_ids == ("T3-AC1", "T3-AC2", "T3-AC3")

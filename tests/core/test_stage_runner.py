from __future__ import annotations

from pathlib import Path

from aidd.core.stage_runner import prepare_stage_bundle


def test_prepare_stage_bundle_resolves_expected_inputs_and_outputs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="implement",
    )

    assert bundle.stage == "implement"
    assert bundle.work_item == "WI-001"
    assert bundle.expected_input_bundle == (
        workspace_root / "workitems" / "WI-001" / "stages" / "tasklist" / "output" / "tasklist.md",
        workspace_root / "workitems" / "WI-001" / "context" / "repository-state.md",
    )
    assert bundle.expected_output_documents == (
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "implement"
        / "implementation-report.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "stage-result.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "validator-report.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "repair-brief.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "questions.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "answers.md",
    )


def test_prepare_stage_bundle_renders_stage_brief_with_relative_paths(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    content = bundle.stage_brief_markdown

    assert "# Stage" in content
    assert "\nplan\n" in content
    assert "# Expected input bundle" in content
    assert "`workitems/WI-001/stages/research/output/research-notes.md`" in content
    assert "# Expected output documents" in content
    assert "`workitems/WI-001/stages/plan/plan.md`" in content

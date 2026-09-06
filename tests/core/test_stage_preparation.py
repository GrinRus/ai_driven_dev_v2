from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.project_set import ResolvedProject, ResolvedProjectSet
from aidd.core.stage_preparation import prepare_stage_bundle, render_stage_brief
from aidd.core.stages import STAGES


def test_stage_brief_never_exposes_workflow_records_as_runtime_skeletons() -> None:
    stage_brief = render_stage_brief(
        stage="idea",
        purpose="Capture the idea.",
        expected_input_bundle=(),
        expected_output_documents=("idea-brief.md", "stage-result.md", "validator-report.md"),
    )
    write_targets = stage_brief.split("# Runtime write targets", 1)[1].split("# AIDD-generated", 1)[
        0
    ]
    assert "idea-brief.md" in write_targets
    assert "stage-result.md" not in write_targets
    assert "validator-report.md" not in write_targets
    assert "## `idea-brief.md`" in stage_brief
    assert "## `stage-result.md`" not in stage_brief
    assert "## `validator-report.md`" not in stage_brief


def test_stage_brief_keeps_explicitly_empty_runtime_target_list() -> None:
    brief = render_stage_brief(
        stage="idea",
        purpose="Capture the idea.",
        expected_input_bundle=(),
        expected_output_documents=("idea-brief.md",),
        runtime_output_documents=(),
    )
    targets = brief.split("# Runtime write targets", 1)[1].split("# AIDD-generated", 1)[0]
    assert "idea-brief.md" not in targets
    assert "Required output skeletons" not in brief


def test_project_set_stage_brief_assigns_lifecycle_evidence_to_aidd(tmp_path: Path) -> None:
    brief = render_stage_brief(
        stage="plan",
        purpose="Plan declared project work.",
        expected_input_bundle=(),
        expected_output_documents=("plan.md",),
        project_set=ResolvedProjectSet(
            repository_root=tmp_path,
            projects=(
                ResolvedProject(id="api", root=tmp_path / "api", relative_root="api", role=None),
            ),
        ),
        project_set_context_path="workitems/WI-001/context/project-set.md",
    )
    assert "AIDD generates `Project-set evidence` in `stage-result.md`" in brief
    assert "Only these substantive documents are runtime completion targets" in brief
    assert "- Project ids: `api`" in brief
    assert "- Project roots: `api`" in brief


@pytest.mark.parametrize("stage", STAGES)
def test_prepared_stage_brief_separates_runtime_and_aidd_owned_documents(
    tmp_path: Path, stage: str
) -> None:
    bundle = prepare_stage_bundle(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-001",
        stage=stage,
    )
    content = bundle.stage_brief_markdown

    assert "# Runtime write targets" in content
    assert "# AIDD-generated records" in content
    assert "# Interview/control documents" in content
    assert "# Published documents" in content
    assert "published compatibility view" not in content
    assert "## `stage-result.md`" not in content
    assert "## `validator-report.md`" not in content
    assert "`workitems/WI-001/stages/" in content
    assert "stage-result.md" in content
    assert "validator-report.md" in content


def test_tasklist_stage_brief_embeds_rich_scaffold_without_contract_lookup(
    tmp_path: Path,
) -> None:
    stage_brief = render_stage_brief(
        stage="tasklist",
        purpose="Break the approved plan into reviewable tasks.",
        expected_input_bundle=(),
        expected_output_documents=("tasklist.md",),
        contracts_root=tmp_path / "missing-contracts",
    )

    assert "## `tasklist.md`" in stage_brief
    assert "### TL-1 — <imperative task title>" in stage_brief
    assert "- Outcome: <observable outcome tied to an approved plan milestone>" in stage_brief
    assert "- Dominant deliverable: `src/example.py` contains the bounded change." in stage_brief
    assert "- In scope: `src/example.py` and `tests/test_example.py`." in stage_brief
    assert "  - TL-1-AC1: <task-local executable acceptance criterion>" in stage_brief
    assert "- TL-1: none" in stage_brief
    assert "- TL-1: <focused check that proves TL-1>" in stage_brief
    assert "This is prompt input, not a validated output document." in stage_brief
    assert "<replace with stage-specific content>" not in stage_brief

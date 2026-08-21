from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.stage_preparation import prepare_stage_bundle, render_stage_brief
from aidd.core.stages import STAGES
from aidd.validators.protocol import VALIDATOR_REPORT_FIELDS


def test_stage_brief_uses_registry_owned_validator_report_skeleton() -> None:
    stage_brief = render_stage_brief(
        stage="idea",
        purpose="Capture the idea.",
        expected_input_bundle=(),
        expected_output_documents=("validator-report.md",),
    )

    for field in VALIDATOR_REPORT_FIELDS:
        assert f"- {field.label}:" in stage_brief
        for alias in field.aliases:
            assert f"- {alias}:" not in stage_brief
    assert "## Structural checks\n\n- none" in stage_brief
    assert "## Semantic checks\n\n- none" in stage_brief
    assert "## Cross-document checks\n\n- none" in stage_brief


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
    assert "# Expected output documents (published compatibility view)" in content
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

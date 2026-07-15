from __future__ import annotations

from aidd.core.stage_preparation import render_stage_brief
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

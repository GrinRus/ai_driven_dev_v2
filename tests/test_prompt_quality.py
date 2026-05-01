from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.stages import STAGES


@pytest.mark.parametrize("stage", STAGES)
def test_stage_repair_prompt_contains_budget_and_status_consistency_rules(stage: str) -> None:
    prompt_path = Path("prompt-packs") / "stages" / stage / "repair.md"
    prompt_text = prompt_path.read_text(encoding="utf-8")

    assert "repair-budget-exhausted" in prompt_text
    assert "Rerun allowed after this attempt: no" in prompt_text
    assert "stage-result.md" in prompt_text
    assert "`failed`" in prompt_text
    assert "`succeeded`" in prompt_text
    assert "exact required headings" in prompt_text
    assert "do not rename" in prompt_text
    assert "validator" in prompt_text.lower()
    assert "consistent" in prompt_text.lower()
    assert "AIDD-owned read-only repair control evidence" in prompt_text
    assert "Do not rewrite it" in prompt_text


@pytest.mark.parametrize("stage", STAGES)
def test_stage_run_and_system_prompts_forbid_model_authored_repair_brief(
    stage: str,
) -> None:
    run_prompt = (Path("prompt-packs") / "stages" / stage / "run.md").read_text(
        encoding="utf-8"
    )
    system_prompt = (Path("prompt-packs") / "stages" / stage / "system.md").read_text(
        encoding="utf-8"
    )

    assert "Do not create or edit `repair-brief.md`" in run_prompt
    assert "AIDD generates it after validation fails" in run_prompt
    assert "do not create or edit `repair-brief.md`" in system_prompt
    assert "AIDD-owned repair control evidence" in system_prompt

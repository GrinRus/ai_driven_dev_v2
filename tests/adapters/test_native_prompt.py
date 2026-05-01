from __future__ import annotations

from pathlib import Path

from aidd.adapters.native_prompt import build_native_prompt_text


def test_native_prompt_compiler_includes_attempt_bundle_and_contract(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    workspace_root = repository_root / ".aidd"
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True)
    stage_brief_path = stage_root / "stage-brief.md"
    input_bundle_path = stage_root / "attempts" / "attempt-0002" / "input-bundle.md"
    repair_brief_path = stage_root / "repair-brief.md"
    prompt_pack_path = repository_root / "prompt-packs" / "stages" / "plan" / "repair.md"
    input_bundle_path.parent.mkdir(parents=True)
    prompt_pack_path.parent.mkdir(parents=True)
    stage_brief_path.write_text("# Stage\n\nplan\n", encoding="utf-8")
    input_bundle_path.write_text("# Input bundle\n\n- upstream evidence\n", encoding="utf-8")
    repair_brief_path.write_text("# Failed checks\n\n- fix plan\n", encoding="utf-8")
    prompt_pack_path.write_text("# Repair prompt\n\nUse budget rules.\n", encoding="utf-8")

    prompt = build_native_prompt_text(
        runtime_id="codex",
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        workspace_root=workspace_root,
        stage_brief_path=stage_brief_path,
        prompt_pack_paths=(prompt_pack_path.relative_to(repository_root),),
        repository_root=repository_root,
        attempt_number=2,
        repair_mode=True,
        input_bundle_path=input_bundle_path,
        repair_brief_path=repair_brief_path,
        repair_context_markdown="Mode: `repair`\n\nAttempt number: `2`",
    )

    assert "- Runtime: codex" in prompt
    assert "- Stage: plan" in prompt
    assert "- Work item: WI-001" in prompt
    assert "- Run id: run-001" in prompt
    assert "- Attempt: 2" in prompt
    assert "- Attempt mode: repair" in prompt
    assert "## Input bundle" in prompt
    assert "upstream evidence" in prompt
    assert "## Repair context" in prompt
    assert "Mode: `repair`" in prompt
    assert "## Active prompt pack:" in prompt
    assert "# Repair prompt" in prompt
    assert "`repair-brief.md` is AIDD-owned read-only repair control evidence" in prompt
    assert "AIDD post-runtime validation is the final truth source" in prompt

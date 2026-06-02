from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.stages import STAGES


@pytest.mark.parametrize("stage", STAGES)
def test_stage_repair_prompt_contains_budget_and_status_consistency_rules(stage: str) -> None:
    prompt_path = Path("prompt-packs") / "stages" / stage / "repair.md"
    prompt_text = prompt_path.read_text(encoding="utf-8")

    assert "repair-budget-final-attempt" in prompt_text
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
    assert "Do not inspect AIDD validator implementation files" in prompt_text
    assert "After updating the required documents and checking consistency, stop" in prompt_text
    assert "contracts/documents/questions.md" in prompt_text
    assert "contracts/documents/answers.md" in prompt_text
    assert "Do not invent `A1`/`A2` answer ids" in prompt_text
    assert "`- Q1 [resolved] ...`" in prompt_text
    assert "Do not put a colon after the marker" in prompt_text
    assert "`- Q1 [resolved]: ...` is invalid" in prompt_text


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


def test_idea_prompts_make_open_questions_list_format_explicit() -> None:
    run_prompt = Path("prompt-packs/stages/idea/run.md").read_text(encoding="utf-8")
    repair_prompt = Path("prompt-packs/stages/idea/repair.md").read_text(encoding="utf-8")

    assert "`Open questions` as Markdown bullet items, or exactly `- none`" in run_prompt
    assert "prose-only text is invalid" in run_prompt
    assert "do not put indented or nested bullets under a question" in run_prompt
    assert "Prose such as `No open questions.` is still invalid" in repair_prompt
    assert (
        "`SEM-INCOMPLETE-SECTION` for `Constraints` or `Open questions`" in repair_prompt
    )


def test_review_prompts_make_finding_evidence_reference_explicit() -> None:
    run_prompt = Path("prompt-packs/stages/review/run.md").read_text(encoding="utf-8")
    repair_prompt = Path("prompt-packs/stages/review/repair.md").read_text(encoding="utf-8")

    assert "Every finding must include an explicit `Evidence:`" in run_prompt
    assert "A plausible rationale without this evidence reference is invalid" in run_prompt
    assert "`Evidence: implementation-report.md ...`" in run_prompt
    assert "add an explicit `Evidence:` line" in repair_prompt
    assert "if no such evidence exists, mark the finding `invalid` or remove it" in repair_prompt


def test_review_prompt_requires_machine_readable_status_line() -> None:
    run_prompt = Path("prompt-packs/stages/review/run.md").read_text(encoding="utf-8")

    assert "write the approval decision as a machine-readable line" in run_prompt
    assert "- Review status: approved" in run_prompt


def test_qa_prompt_requires_machine_readable_verdict_line() -> None:
    run_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")

    assert "quality decision on its own machine-readable line" in run_prompt
    assert "`Quality verdict`" in run_prompt
    assert "- QA verdict: ready" in run_prompt


def test_review_prompt_respects_authored_verification_boundary() -> None:
    run_prompt = Path("prompt-packs/stages/review/run.md").read_text(encoding="utf-8")
    system_prompt = Path("prompt-packs/stages/review/system.md").read_text(
        encoding="utf-8"
    )

    assert "`context/verification-output.md` define the" in run_prompt
    assert "Do not convert optional broader checks outside that boundary" in run_prompt
    assert "Keep out-of-boundary exploratory check limitations as non-blocking notes" in (
        run_prompt
    )
    assert "do not make approval conditional only because an optional broader check" in (
        system_prompt
    )
    assert "intentional design constraint selected by the authored task" in system_prompt
    assert "not findings by themselves" in run_prompt
    assert "do not write an `accepted-risk`" in run_prompt


def test_qa_prompt_respects_selected_design_constraints() -> None:
    run_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    repair_prompt = Path("prompt-packs/stages/qa/repair.md").read_text(encoding="utf-8")
    system_prompt = Path("prompt-packs/stages/qa/system.md").read_text(
        encoding="utf-8"
    )

    assert "Intentional design constraints selected by the authored task" in run_prompt
    assert "not residual release risks by themselves" in run_prompt
    assert "trusted local code execution is `ready`" in run_prompt
    assert "Do not preserve `ready-with-risks` only because" in repair_prompt
    assert "do not downgrade solely for an intentional design constraint" in system_prompt


def test_review_and_implement_prompts_treat_untracked_files_as_workspace_changes() -> None:
    implement_prompt = Path("prompt-packs/stages/implement/run.md").read_text(
        encoding="utf-8"
    )
    review_prompt = Path("prompt-packs/stages/review/run.md").read_text(
        encoding="utf-8"
    )
    review_system_prompt = Path("prompt-packs/stages/review/system.md").read_text(
        encoding="utf-8"
    )

    assert "newly created untracked source files" in implement_prompt
    assert "the deliverable is the" in implement_prompt
    assert "local workspace state, not a tracked-only patch" in implement_prompt
    assert "Newly created untracked source files under the" in review_prompt
    assert "allowed write scope are part of the AIDD deliverable" in review_prompt
    assert "Do not reject solely because such a file is absent from `git diff --stat`" in (
        review_prompt
    )
    assert "do not reject a change solely because a newly created file is untracked" in (
        review_system_prompt
    )


def test_review_spec_prompts_require_exact_decision_heading() -> None:
    run_prompt = Path("prompt-packs/stages/review-spec/run.md").read_text(
        encoding="utf-8"
    )
    repair_prompt = Path("prompt-packs/stages/review-spec/repair.md").read_text(
        encoding="utf-8"
    )

    assert "- `## Decision`" in run_prompt
    assert "sign-off status under `## Decision`" in run_prompt
    assert "`## Decision/sign-off`" in run_prompt
    assert "structurally invalid" in run_prompt
    assert "exact top-level heading `## Decision`" in repair_prompt
    assert "`## Decision/sign-off`" in repair_prompt
    assert "aliases do not" in repair_prompt
    assert "satisfy the document contract" in repair_prompt


def test_review_spec_prompts_require_exact_readiness_vocabulary() -> None:
    run_prompt = Path("prompt-packs/stages/review-spec/run.md").read_text(
        encoding="utf-8"
    )
    repair_prompt = Path("prompt-packs/stages/review-spec/repair.md").read_text(
        encoding="utf-8"
    )

    assert "exactly one top-level bullet" in run_prompt
    assert "`ready`, `ready-with-conditions`, or `not-ready`" in run_prompt
    assert "`conditionally ready`" in run_prompt
    assert "containing only `ready-with-conditions`" in run_prompt
    assert "`ready-with-conditions` ->" in run_prompt
    assert "`approved-with-conditions`" in run_prompt
    assert "`approved-with-conditions` is paired with `ready-with-conditions`" in repair_prompt
    assert "do not replace it with prose such as `conditionally ready`" in repair_prompt


def test_implement_prompts_require_executable_verification_evidence() -> None:
    run_prompt = Path("prompt-packs/stages/implement/run.md").read_text(
        encoding="utf-8"
    )
    repair_prompt = Path("prompt-packs/stages/implement/repair.md").read_text(
        encoding="utf-8"
    )

    assert "outcome claim is invalid unless the same bullet" in run_prompt
    assert "executable/check evidence" in run_prompt
    assert "Manual or `CliRunner` checks must cite" in run_prompt
    assert "do not write `manual inspection -> pass` without evidence" in run_prompt
    assert "write `not-run: <reason>`" in run_prompt
    assert "outcome claim without executable/check evidence" in repair_prompt
    assert "captured assertion result" in repair_prompt
    assert "`not-run: <reason>` explicitly" in repair_prompt

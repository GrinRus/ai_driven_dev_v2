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
    system_prompt = Path("prompt-packs/stages/idea/system.md").read_text(
        encoding="utf-8"
    )
    interview_prompt = Path("prompt-packs/stages/idea/interview.md").read_text(
        encoding="utf-8"
    )
    contract = Path("contracts/stages/idea.md").read_text(encoding="utf-8")

    assert "avoid unsupported absolute claims" in run_prompt
    assert "Do not assert source-code root causes" in run_prompt
    assert "leave source" in run_prompt
    assert "diagnosis to `research`" in run_prompt
    assert "tie them to the selected request, constraints, and acceptance context" in run_prompt
    assert "`context/selected-task.md`" in run_prompt
    assert "`context/acceptance-criteria.md`" in run_prompt
    assert "`Open questions` as Markdown bullet items, or exactly `- none`" in run_prompt
    assert "prose-only text is invalid" in run_prompt
    assert "do not put indented or nested bullets under a question" in run_prompt
    assert "Prose such as `No open questions.` is still invalid" in repair_prompt
    assert (
        "`SEM-INCOMPLETE-SECTION` for `Constraints` or `Open questions`" in repair_prompt
    )
    for text in (run_prompt, repair_prompt, system_prompt, interview_prompt, contract):
        assert "blocking answers" in text
        assert "interview answers" in text
        assert "operator policy decisions" in text
        assert "before downstream planning or implementation" in text


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
    assert "`context/diff-summary.md`" in run_prompt
    assert "lockfile, dependency manifest, generated resolver output" in run_prompt
    assert "set `QA verdict: not-ready` and release recommendation" in run_prompt
    assert "one top-level bullet per criterion" in run_prompt
    assert "Each bullet must name exactly one `AC-N` id" in run_prompt
    assert "Do not use range claims such as `AC-1 through AC-4`" in run_prompt
    assert "Do not pair `QA verdict: ready` with residual risk bullets" in run_prompt
    assert "use `ready-with-risks` and `proceed-with-conditions`" in run_prompt
    assert "isolated optional broad-suite failures in unrelated environment-sensitive tests" in (
        run_prompt
    )
    assert "non-blocking optional-check note instead of a residual risk" in run_prompt


def test_qa_prompts_do_not_downgrade_for_isolated_optional_broad_suite_failures() -> None:
    run_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    repair_prompt = Path("prompt-packs/stages/qa/repair.md").read_text(encoding="utf-8")
    system_prompt = Path("prompt-packs/stages/qa/system.md").read_text(
        encoding="utf-8"
    )
    contract = Path("contracts/stages/qa.md").read_text(encoding="utf-8")

    for text in (run_prompt, repair_prompt, system_prompt, contract):
        assert "isolated optional broad-suite failures" in text
        assert "unrelated environment-sensitive tests" in text

    assert "record it as a non-blocking optional-check note" in run_prompt
    assert "rather than a residual risk" in repair_prompt
    assert "must record it as a non-blocking" in contract


def test_review_prompt_respects_authored_verification_boundary() -> None:
    run_prompt = Path("prompt-packs/stages/review/run.md").read_text(encoding="utf-8")
    system_prompt = Path("prompt-packs/stages/review/system.md").read_text(
        encoding="utf-8"
    )

    assert (
        "When present, selected task evidence, acceptance criteria, and "
        "`context/verification-output.md`"
    ) in run_prompt
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


def test_review_and_qa_prompts_cross_check_tasklist_and_plan_obligations() -> None:
    review_prompt = Path("prompt-packs/stages/review/run.md").read_text(
        encoding="utf-8"
    )
    review_repair_prompt = Path("prompt-packs/stages/review/repair.md").read_text(
        encoding="utf-8"
    )
    qa_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    qa_repair_prompt = Path("prompt-packs/stages/qa/repair.md").read_text(
        encoding="utf-8"
    )

    assert "audit the\n   implementation against task-level details" in review_prompt
    assert "planned risk mitigations" in review_prompt
    assert "error-cause or diagnostic-context preservation check" in review_prompt
    assert "named mechanisms as requirements" in review_prompt
    assert "named synchronization primitive" in review_prompt
    assert "missed tasklist/plan requirement" in review_repair_prompt
    assert "named mechanism" in review_repair_prompt
    assert "cross-check nontrivial task details" in qa_prompt
    assert "error-cause or\n   diagnostic-context preservation promise" in qa_prompt
    assert "required named synchronization primitive" in qa_prompt
    assert "Do not name a specific execution surface" in qa_prompt
    assert "`ASGI/TestClient`, state the exact surface" in qa_prompt
    assert "missed tasklist/plan requirement" in qa_repair_prompt
    assert "Named mechanisms include concrete APIs/library calls" in qa_repair_prompt
    assert "overstated execution surface" in qa_repair_prompt
    assert "synchronization primitives such as named" not in qa_repair_prompt


def test_implement_review_and_qa_require_shared_surface_blast_radius_evidence() -> None:
    implement_prompt = Path("prompt-packs/stages/implement/run.md").read_text(
        encoding="utf-8"
    )
    review_prompt = Path("prompt-packs/stages/review/run.md").read_text(
        encoding="utf-8"
    )
    qa_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    implement_contract = Path("contracts/stages/implement.md").read_text(
        encoding="utf-8"
    )
    review_contract = Path("contracts/stages/review.md").read_text(encoding="utf-8")
    qa_contract = Path("contracts/stages/qa.md").read_text(encoding="utf-8")

    for text in (
        implement_prompt,
        review_prompt,
        qa_prompt,
        implement_contract,
        review_contract,
        qa_contract,
    ):
        assert "shared public-surface mechanism" in text
        assert "CLI decorator" in text
        assert "parser/helper" in text
        assert "router/error boundary" in text
        assert "schema transform helper" in text
        assert "sibling commands, routes, generated outputs" in text
        assert "help/usage" in text
        assert "API compatibility" in text
        assert "docs consistency" in text

    assert "explicitly mark the unchecked sibling surface as a residual risk" in (
        implement_prompt
    )
    assert "Record a finding when implementation evidence does not cover" in (
        review_prompt
    )
    assert "Missing help/usage, docs consistency, API compatibility" in qa_prompt
    assert "must force `QA verdict: not-ready`" in qa_contract


def test_plan_prompts_require_milestone_ids_and_verification_mapping() -> None:
    contract = Path("contracts/stages/plan.md").read_text(encoding="utf-8")
    run_prompt = Path("prompt-packs/stages/plan/run.md").read_text(encoding="utf-8")
    repair_prompt = Path("prompt-packs/stages/plan/repair.md").read_text(
        encoding="utf-8"
    )

    assert "use stable ids such as `M1`, `M2`" in contract
    assert "tie checks to milestone ids such as `M1`" in contract
    assert "must start with a stable id such as `M1`, `M2`, or `M3`" in run_prompt
    assert "Verification notes` must reference the milestone ids" in run_prompt
    assert "missing milestone ids" in repair_prompt
    assert "reference those ids" in repair_prompt


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
    assert "do not pair `QA verdict: ready` with residual risk bullets" in repair_prompt
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
    assert "`git status --short --untracked-files=all` and" in implement_prompt
    assert "`git diff --name-only`" in implement_prompt
    assert "Do not leave lockfiles, dependency manifests" in implement_prompt
    assert "`git stash`, `git reset`, `git checkout --`, or `git restore`" in (
        implement_prompt
    )
    assert "Newly created untracked source files under the" in review_prompt
    assert "allowed write scope are part of the AIDD deliverable" in review_prompt
    assert "Do not reject solely because such a file is absent from `git diff --stat`" in (
        review_prompt
    )
    assert "record a `must-fix` finding" in review_prompt
    assert "do not reject a change solely because a newly created file is untracked" in (
        review_system_prompt
    )


def test_live_prompts_and_contracts_protect_prepared_workspace() -> None:
    implement_prompt = Path("prompt-packs/stages/implement/run.md").read_text(
        encoding="utf-8"
    )
    implement_repair = Path("prompt-packs/stages/implement/repair.md").read_text(
        encoding="utf-8"
    )
    review_prompt = Path("prompt-packs/stages/review/run.md").read_text(
        encoding="utf-8"
    )
    qa_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    implement_contract = Path("contracts/stages/implement.md").read_text(
        encoding="utf-8"
    )
    review_contract = Path("contracts/stages/review.md").read_text(encoding="utf-8")
    qa_contract = Path("contracts/stages/qa.md").read_text(encoding="utf-8")

    for text in (implement_prompt, implement_repair, implement_contract):
        normalized_text = " ".join(text.split())
        assert (
            "Do not delete, move, reclone, or recreate the prepared repository checkout"
            in normalized_text
        )
        assert "`install-home/`" in text
        assert "packaged contracts disappear" in text
        assert (
            "do not try to recover by" in text
            or "instead of attempting workspace recovery" in text
            or "instead of running `git clone`" in text
        )
        assert "`git status --ignored --short --untracked-files=all`" in text
        assert "`.venv/`" in text
        assert "`.pdm-build/`" in text
        assert "`coverage/`" in text
        assert "`.coverage*`" in text
        assert "`__pycache__/`" in text
        assert "Do not" in text and "claim cleanup" in text

    for text in (review_prompt, qa_prompt, review_contract, qa_contract):
        assert "prepared checkout disappeared" in text
        assert "was recloned" in text
        assert "`target-workspace-evidence.*`" in text
        assert "`git status --ignored --short --untracked-files=all`" in text
        assert "`.pytest_cache/`" in text
        assert "`.coverage*`" in text
        assert "`__pycache__/`" in text
        assert "workspace pollution" in text
        assert "cleanup claim" in text or "claim cleanup" in text


def test_review_and_qa_use_live_setup_workspace_baseline() -> None:
    review_prompt = Path("prompt-packs/stages/review/run.md").read_text(
        encoding="utf-8"
    )
    qa_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    review_contract = Path("contracts/stages/review.md").read_text(encoding="utf-8")
    qa_contract = Path("contracts/stages/qa.md").read_text(encoding="utf-8")

    for text in (review_prompt, qa_prompt, review_contract, qa_contract):
        assert "Live setup workspace baseline" in text
        lower_text = text.lower()
        assert "known harness config" in lower_text
        assert "setup-baseline untracked non-aidd files" in lower_text
        assert "not" in text and "solely because" in text
        assert "new untracked files" in text and "baseline" in text


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


def test_review_spec_prompt_requires_issue_severity_and_rationale_shape() -> None:
    run_prompt = Path("prompt-packs/stages/review-spec/run.md").read_text(
        encoding="utf-8"
    )
    repair_prompt = Path("prompt-packs/stages/review-spec/repair.md").read_text(
        encoding="utf-8"
    )

    assert "`- I1: Severity: medium. Rationale: because ...`" in run_prompt
    assert "`- Severity: medium`" in run_prompt
    assert "metadata bullets immediately under each heading" in run_prompt
    assert "every subsection issue has immediate `Severity:`" in repair_prompt
    assert "`Severity: none`" in run_prompt
    assert "`Rationale: because ...`" in run_prompt
    assert "do not write bare prose such as `No material issues identified.`" in run_prompt


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
    assert "Use one bullet per command/check" in run_prompt
    assert "``- `command goes here` -> pass (observed summary)``" in run_prompt
    assert "one bullet per command/check" in repair_prompt
    assert "short intent on the same line" in run_prompt
    assert "copy this exact shape for every file" in run_prompt
    assert "``- `path/to/file.ext` - changed <short intent>``" in run_prompt
    assert "Do not write a top-level bullet that only names" in run_prompt
    assert "self-check the `Touched files` section" in run_prompt
    assert "same-line\n  path + intent" in repair_prompt
    assert "Keep debugging bounded" in run_prompt
    assert "at most one focused fix attempt" in run_prompt
    assert "truthful failed verification report" in run_prompt
    assert "timing out without stage artifacts" in run_prompt
    assert "continuing ad hoc debugging until timeout" in repair_prompt

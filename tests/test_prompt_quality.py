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
    assert "`- Q1: [resolved] ...`" in prompt_text
    assert "do not create `[resolved]`" in prompt_text


@pytest.mark.parametrize("stage", STAGES)
def test_stage_run_prompts_make_interview_syntax_strict(stage: str) -> None:
    run_prompt = (Path("prompt-packs") / "stages" / stage / "run.md").read_text(
        encoding="utf-8"
    )

    assert "## Interview document syntax" in run_prompt
    assert "`- Q1 [blocking] text`" in run_prompt
    assert "`- Q1 [non-blocking] text`" in run_prompt
    assert "`- Q1 [resolved] text`" in run_prompt
    assert "`- Q1 [partial] text`" in run_prompt
    assert "`- Q1 [deferred] text`" in run_prompt
    assert "`- Q1 [resolved]: text`" in run_prompt
    assert "`- Q1: [resolved] text`" in run_prompt
    assert "Do not invent `A1`/`A2` answer ids" in run_prompt
    assert "do not create\n  `[resolved]` answers yourself" in run_prompt or (
        "must not invent\n  `[resolved]` answers" in run_prompt
    )


def test_interview_document_contracts_and_native_prompt_forbid_marker_colon() -> None:
    questions_contract = Path("contracts/documents/questions.md").read_text(
        encoding="utf-8"
    )
    answers_contract = Path("contracts/documents/answers.md").read_text(
        encoding="utf-8"
    )
    native_prompt = Path("src/aidd/adapters/native_prompt.py").read_text(
        encoding="utf-8"
    )

    for text in (questions_contract, answers_contract):
        assert "Canonical" in text
        assert "must be followed by a space" in text
        assert "`- Q1: [blocking] question text`" in text or (
            "`- Q1: [resolved] answer text`" in text
        )
        assert "invalid" in text
        assert "A1" in text

    assert "`- Q1 [resolved]: ...` is invalid" in native_prompt
    assert "`- Q1: [resolved] ...`" in native_prompt
    assert "do not create `[resolved]` answers" in native_prompt


def test_plan_run_prompt_forbids_self_answered_downstream_policy() -> None:
    run_prompt = Path("prompt-packs/stages/plan/run.md").read_text(encoding="utf-8")

    assert "Planning may ask downstream clarification questions" in run_prompt
    assert "must not invent\n  `[resolved]` answers for missing operator decisions" in (
        run_prompt
    )
    assert "If no operator answer is present" in run_prompt


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


def test_implement_stage_result_next_action_stays_flow_aware() -> None:
    stage_result_contract = Path("contracts/documents/stage-result.md").read_text(
        encoding="utf-8"
    )
    implement_contract = Path("contracts/stages/implement.md").read_text(
        encoding="utf-8"
    )
    implement_prompt = Path("prompt-packs/stages/implement/run.md").read_text(
        encoding="utf-8"
    )
    implement_repair_prompt = Path("prompt-packs/stages/implement/repair.md").read_text(
        encoding="utf-8"
    )

    for text in (
        stage_result_contract,
        implement_contract,
        implement_prompt,
        implement_repair_prompt,
    ):
        assert "directly to `qa`" in text
        assert "`review`" in text

    assert "implement -> review -> qa" in stage_result_contract
    assert "implement -> review -> qa" in implement_contract
    assert "`implement` hands off to `review`, never\n  directly to `qa`" in (
        implement_prompt
    )
    assert "downstream-order drift" in implement_repair_prompt


def test_middle_stage_result_next_actions_stay_flow_aware() -> None:
    stage_result_contract = Path("contracts/documents/stage-result.md").read_text(
        encoding="utf-8"
    )
    plan_contract = Path("contracts/stages/plan.md").read_text(encoding="utf-8")
    plan_prompt = Path("prompt-packs/stages/plan/run.md").read_text(encoding="utf-8")
    plan_repair_prompt = Path("prompt-packs/stages/plan/repair.md").read_text(
        encoding="utf-8"
    )
    review_spec_contract = Path("contracts/stages/review-spec.md").read_text(
        encoding="utf-8"
    )
    review_spec_prompt = Path("prompt-packs/stages/review-spec/run.md").read_text(
        encoding="utf-8"
    )
    review_spec_repair_prompt = Path(
        "prompt-packs/stages/review-spec/repair.md"
    ).read_text(encoding="utf-8")
    live_scenario = Path(
        "harness/scenarios/live/hono-non-error-throw-handling.yaml"
    ).read_text(encoding="utf-8")

    assert "`plan` -> `review-spec`" in stage_result_contract
    assert "`review-spec` -> `tasklist`" in stage_result_contract

    for text in (plan_contract, plan_prompt, plan_repair_prompt, live_scenario):
        assert "`review-spec`" in text
        assert "immediate" in text
        assert "implementation" in text

    for text in (
        review_spec_contract,
        review_spec_prompt,
        review_spec_repair_prompt,
        live_scenario,
    ):
        assert "`tasklist`" in text
        assert "immediate" in text
        assert "implementation" in text


def test_js_ts_helper_internal_claims_require_export_map_evidence() -> None:
    tasklist_prompt = Path("prompt-packs/stages/tasklist/run.md").read_text(
        encoding="utf-8"
    )
    tasklist_contract = Path("contracts/stages/tasklist.md").read_text(
        encoding="utf-8"
    )
    implement_prompt = Path("prompt-packs/stages/implement/run.md").read_text(
        encoding="utf-8"
    )
    implement_contract = Path("contracts/stages/implement.md").read_text(
        encoding="utf-8"
    )
    review_prompt = Path("prompt-packs/stages/review/run.md").read_text(
        encoding="utf-8"
    )
    review_contract = Path("contracts/stages/review.md").read_text(encoding="utf-8")
    qa_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    qa_contract = Path("contracts/stages/qa.md").read_text(encoding="utf-8")

    for text in (
        tasklist_prompt,
        tasklist_contract,
        implement_prompt,
        implement_contract,
        review_prompt,
        review_contract,
        qa_prompt,
        qa_contract,
    ):
        normalized = " ".join(text.split())
        assert "JavaScript or TypeScript packages" in text
        assert "`package.json`" in text
        assert "`exports`" in text
        assert "wildcard subpath exports" in normalized
        assert "`./utils/*`" in text
        assert "generated declaration" in normalized
        assert "public import conventions" in normalized
        assert "internal-only" in text or "internal solely" in text

    assert "do not plan a concrete helper/module path as private" in tasklist_prompt
    assert "before describing that helper as private or internal-only" in (
        tasklist_contract
    )


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


def test_plan_and_tasklist_preserve_authored_verification_commands() -> None:
    plan_contract = Path("contracts/stages/plan.md").read_text(encoding="utf-8")
    tasklist_contract = Path("contracts/stages/tasklist.md").read_text(
        encoding="utf-8"
    )
    plan_prompt = Path("prompt-packs/stages/plan/run.md").read_text(encoding="utf-8")
    tasklist_prompt = Path("prompt-packs/stages/tasklist/run.md").read_text(
        encoding="utf-8"
    )

    for text in (plan_contract, tasklist_contract, plan_prompt, tasklist_prompt):
        normalized = " ".join(text.split())
        assert "`context/verification-output.md`" in text
        assert "preserve those commands exactly" in text
        assert "flags, path lists, environment variables" in normalized
        assert "coverage/cache-disabling options" in text
        assert "`--coverage.enabled=false`" in text
        assert "do not replace them with" in normalized or "do not rewrite them as" in (
            normalized
        )
        assert "Optional broad checks outside the authored verification boundary" in text
        assert (
            "not become required pass criteria" in normalized
            or "Do not turn them into required pass criteria" in normalized
            or "not promoted to required pass criteria" in normalized
        )


def test_tasklist_prompts_are_live_installed_workspace_safe() -> None:
    run_prompt = Path("prompt-packs/stages/tasklist/run.md").read_text(
        encoding="utf-8"
    )
    repair_prompt = Path("prompt-packs/stages/tasklist/repair.md").read_text(
        encoding="utf-8"
    )

    for text in (run_prompt, repair_prompt):
        assert "stage-brief.md" in text
        assert "Repository-local `contracts/...` files may be absent" in text
        assert "Do not end the turn after analysis-only reads" in text

    assert "Avoid broad commands such as `rg --files .aidd`" in run_prompt
    assert "make the first file-changing action create or replace all" in run_prompt
    assert "the first file-changing action must" in repair_prompt


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
    qa_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    review_contract = Path("contracts/stages/review.md").read_text(encoding="utf-8")
    qa_contract = Path("contracts/stages/qa.md").read_text(encoding="utf-8")

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

    for text in (review_prompt, qa_prompt, review_contract, qa_contract):
        normalized = " ".join(text.split())
        assert "`git diff -- <untracked-file>`" in text
        assert "`git status --short --untracked-files=all` plus direct file inspection" in (
            normalized
        )
        assert "`git diff --no-index /dev/null <untracked-file>`" in text


def test_setup_workspace_prompts_and_contracts_protect_prepared_workspace() -> None:
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
        assert "setup-owned" in text.lower()
        assert "`context/workspace-baseline.md`" in text
        assert "packaged contracts disappear" in text
        assert (
            "do not try to recover by" in text
            or "instead of attempting workspace recovery" in text
            or "instead of running `git clone`" in text
        )
        assert "git status --ignored --short --untracked-files=all" in normalized_text
        assert "`.venv/`" in text
        assert "`.ruff_cache/`" in text
        assert "`.pdm-build/`" in text
        assert "`coverage/`" in text
        assert "`.coverage*`" in text
        assert "`__pycache__/`" in text
        assert "Do not" in text and "claim cleanup" in text

    for text in (implement_prompt, implement_repair):
        normalized_text = " ".join(text.split())
        assert (
            "If this setup-owned workspace runs any test, type, lint, docs, or build command"
            in normalized_text
            or "If the setup-owned workspace ran any test, type, lint, docs, or build command"
            in normalized_text
        )
        assert "exact command" in normalized_text
        assert "`git status --short --untracked-files=all` is insufficient" in normalized_text

    for text in (review_prompt, qa_prompt, review_contract, qa_contract):
        normalized_text = " ".join(text.split())
        assert "prepared checkout disappeared" in normalized_text
        assert "was recloned" in normalized_text
        assert "`context/workspace-baseline.md`" in text
        assert "git status --ignored --short --untracked-files=all" in normalized_text
        assert "`.pytest_cache/`" in text
        assert "`.ruff_cache/`" in text
        assert "`.coverage*`" in text
        assert "`__pycache__/`" in text
        assert "workspace pollution" in text
        assert "cleanup claim" in text or "claim cleanup" in text


def test_review_and_qa_prompts_require_post_command_residue_truthfulness() -> None:
    review_prompt = Path("prompt-packs/stages/review/run.md").read_text(
        encoding="utf-8"
    )
    review_repair = Path("prompt-packs/stages/review/repair.md").read_text(
        encoding="utf-8"
    )
    qa_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    qa_repair = Path("prompt-packs/stages/qa/repair.md").read_text(encoding="utf-8")
    review_contract = Path("contracts/stages/review.md").read_text(encoding="utf-8")
    qa_contract = Path("contracts/stages/qa.md").read_text(encoding="utf-8")

    review_texts = (review_prompt, review_repair, review_contract)
    for text in review_texts:
        normalized = " ".join(text.split())
        assert "after all review commands" in normalized
        assert "`Findings: none`" in text
        assert "residue" in text
        assert "`coverage/`" in text
        assert "post-cleanup evidence" in normalized

    qa_texts = (qa_prompt, qa_repair, qa_contract)
    for text in qa_texts:
        normalized = " ".join(text.split())
        assert "after all QA commands" in normalized
        assert "clean review report" in normalized
        assert "`QA verdict: ready`" in text or "`not-ready`" in text
        assert "`coverage/`" in text
        assert "residue" in text


def test_research_prompts_and_contracts_clean_ignored_verification_residue() -> None:
    run_prompt = Path("prompt-packs/stages/research/run.md").read_text(
        encoding="utf-8"
    )
    repair_prompt = Path("prompt-packs/stages/research/repair.md").read_text(
        encoding="utf-8"
    )
    contract = Path("contracts/stages/research.md").read_text(encoding="utf-8")

    for text in (run_prompt, repair_prompt, contract):
        assert "`git status --ignored --short --untracked-files=all`" in text
        assert "`.pytest_cache/`" in text
        assert "`.ruff_cache/`" in text
        assert "`coverage/`" in text
        assert "`.coverage*`" in text
        assert "`__pycache__/`" in text
        assert "workspace pollution" in text
        assert "ignored verification residue" in text


def test_research_prompts_and_contracts_require_bounded_local_probes() -> None:
    run_prompt = Path("prompt-packs/stages/research/run.md").read_text(
        encoding="utf-8"
    )
    repair_prompt = Path("prompt-packs/stages/research/repair.md").read_text(
        encoding="utf-8"
    )
    contract = Path("contracts/stages/research.md").read_text(encoding="utf-8")

    for text in (run_prompt, repair_prompt, contract):
        assert "bounded by construction" in text
        assert "external per-stage timeout" in text
        assert "infinite" in text
        assert "stream" in text
        assert "`anyio.fail_after(...)`" in text
        assert "`subprocess.run(..., timeout=...)`" in text
        assert "`not-run: <reason>`" in text


def test_live_docs_distinguish_provider_no_progress_from_quality_failure() -> None:
    catalog = Path("docs/e2e/live-e2e-catalog.md").read_text(encoding="utf-8")
    rubric = Path("docs/e2e/live-quality-rubric.md").read_text(encoding="utf-8")
    skill = Path(".agents/skills/live-e2e/SKILL.md").read_text(encoding="utf-8")

    for text in (catalog, rubric, skill):
        lower_text = text.lower()
        normalized_text = " ".join(text.split())
        assert "provider-no-progress before completed stage artifact" in normalized_text
        assert "no_progress_timeout_minutes" in text
        assert (
            "infra/provider" in lower_text
            or "blocked-provider" in lower_text
            or "blocked-infra" in lower_text
            or "terminal `infra-fail`" in lower_text
        )
        assert (
            "not product-quality" in lower_text
            or "not a product-quality" in lower_text
            or "not product quality" in lower_text
        )
        assert "manual-quality-stop" in lower_text


def test_review_and_qa_use_setup_workspace_baseline_context() -> None:
    review_prompt = Path("prompt-packs/stages/review/run.md").read_text(
        encoding="utf-8"
    )
    qa_prompt = Path("prompt-packs/stages/qa/run.md").read_text(encoding="utf-8")
    review_contract = Path("contracts/stages/review.md").read_text(encoding="utf-8")
    qa_contract = Path("contracts/stages/qa.md").read_text(encoding="utf-8")

    for text in (review_prompt, qa_prompt, review_contract, qa_contract):
        assert "`context/workspace-baseline.md`" in text
        lower_text = text.lower()
        assert "setup-owned" in lower_text
        assert "baseline" in lower_text
        assert "not" in text and "solely because" in text
        assert "new untracked files" in text and "baseline" in text


def test_reusable_runtime_surface_has_no_live_target_or_eval_vocabulary() -> None:
    reusable_roots = (
        Path("src/aidd/core"),
        Path("src/aidd/adapters"),
        Path("src/aidd/validators"),
        Path("contracts"),
        Path("prompt-packs"),
        Path("src/aidd/runtime_catalog.py"),
    )
    reusable_forbidden = (
        "LinearRouter",
        "PatternRouter",
        "sqlite-utils",
        "sqlite_utils",
        "AIDD_EVAL_CLAUDE_CODE_COMMAND",
        "AIDD_EVAL_CODEX_COMMAND",
        "AIDD_EVAL_OPENCODE_COMMAND",
        "AIDD_EVAL_QWEN_COMMAND",
        "Live setup workspace baseline",
        "Installed live",
        "installed live",
        "live setup-baseline",
        "live setup baseline",
        "live target checkouts",
        "target-workspace-evidence.*",
        "target-workspace-evidence",
        "live harness",
        "live E2E",
        "Live E2E",
    )
    scanned_groups = (
        (reusable_roots, reusable_forbidden),
        (
            (
                Path("AGENTS.md"),
                Path("CONTRIBUTING.md"),
                Path("README.md"),
                Path("docs/product"),
                Path("docs/operator-handbook.md"),
                Path("docs/operator-support-policy.md"),
                Path("docs/operator-troubleshooting.md"),
                Path("docs/architecture"),
                Path("docs/release-checklist.md"),
                Path("docs/compatibility-policy.md"),
            ),
            (
                "Live E2E",
                "live E2E",
                "manual live",
                "installed live",
                "black-box live",
                "live harness",
                "target-workspace-evidence",
                "aidd-live-e2e",
                "sqlite-utils",
                "Hono",
                "honojs",
                "hono-",
                "AIDD_EVAL",
                "install-home",
                "uv-cache",
                "source/aidd",
                "live_e2e_black_box",
                "AIDD-LIVE",
                "live catalog",
                "live matrix",
                "live evidence",
                "live eval",
                "live scenario",
                "live audit",
                "local-wheel live",
            ),
        ),
        (
            (Path("src/aidd/cli/static"),),
            (
                "Live E2E",
                "live E2E",
                "manual live E2E",
                "target-workspace-evidence",
                "AIDD_EVAL_CODEX_COMMAND",
                "sqlite-utils",
            ),
        ),
        (
            (Path("tests/validators/test_semantic.py"),),
            (
                "TASK-LIVE",
                "WI-LIVE",
                "Hono",
                "hono",
                "sqlite-utils",
                "sqlite_utils",
                "typer/",
                "UV_CACHE_DIR=/tmp/uv-cache",
                "install-home",
                "target-workspace-evidence",
            ),
        ),
        (
            (Path("README.md"),),
            (
                "target-workspace-evidence",
                "install-home",
                "uv-cache",
                "source/aidd",
                "sqlite-utils",
                "aidd-live-e2e",
                "manual live E2E",
                "Live E2E",
            ),
        ),
    )

    violations: list[str] = []
    for scanned_paths, forbidden in scanned_groups:
        candidate_files: list[Path] = []
        for scanned_path in scanned_paths:
            if scanned_path.is_file():
                candidate_files.append(scanned_path)
            else:
                candidate_files.extend(path for path in scanned_path.rglob("*"))
        for path in candidate_files:
            if not path.is_file():
                continue
            if path.suffix in {".pyc", ".png", ".jpg", ".jpeg", ".gif"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for needle in forbidden:
                if needle in text:
                    violations.append(f"{path}: {needle}")

    assert violations == []


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

    assert "explicit `Severity`, `Evidence`, and `Rationale` text" in run_prompt
    assert "Severity: medium" in run_prompt
    assert "Evidence:" in run_prompt
    assert "Rationale: because ..." in run_prompt
    assert "`- Severity: medium`" in run_prompt
    assert "`- Evidence: plan.md M2`" in run_prompt
    assert "metadata bullets immediately under each heading" in run_prompt
    normalized_repair_prompt = " ".join(repair_prompt.split())
    assert (
        "every subsection issue has immediate `Severity:`, `Evidence:`, and "
        "`Rationale:`" in normalized_repair_prompt
    )
    assert "`Severity: none`" in run_prompt
    assert "`Evidence: plan.md / research-notes.md`" in run_prompt
    assert "do not write bare prose such as `No material issues identified.`" in run_prompt


def test_review_spec_prompts_require_direct_evidence_and_reconciliation() -> None:
    run_prompt = Path("prompt-packs/stages/review-spec/run.md").read_text(
        encoding="utf-8"
    )
    repair_prompt = Path("prompt-packs/stages/review-spec/repair.md").read_text(
        encoding="utf-8"
    )
    contract = Path("contracts/documents/review-spec-report.md").read_text(
        encoding="utf-8"
    )

    assert "`critical` and `high` issues must cite direct evidence" in run_prompt
    assert "Do not write unsupported claims such as `source inspection shows`" in run_prompt
    assert "Do not expand implementation scope" in run_prompt
    assert "convert speculative risk into a high-severity defect" in run_prompt
    assert "include `Reconciliation:`" in run_prompt
    assert "missing evidence reference" in repair_prompt
    assert "unsupported high-severity claim" in repair_prompt
    assert "contradiction with upstream research or plan" in repair_prompt
    assert "Unsupported phrases such as `source inspection shows`" in contract


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
    assert "Do not list mutation-only cleanup commands such as `rm -rf ...`" in run_prompt
    assert "proving residue is absent" in run_prompt
    assert "`not-run: future-stage artifact`" in run_prompt
    assert "write `not-run: <reason>`" in run_prompt
    assert "outcome claim without executable/check evidence" in repair_prompt
    assert "captured assertion result" in repair_prompt
    assert (
        "Do not preserve mutation-only cleanup bullets such as `rm -rf ... -> pass`"
        in repair_prompt
    )
    assert "`not-run: future-stage artifact`" in repair_prompt
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

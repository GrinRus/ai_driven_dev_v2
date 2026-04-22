from __future__ import annotations

from pathlib import Path

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic import (
    INCOMPLETE_EXECUTION_SUMMARY_CODE,
    INCOMPLETE_SECTION_CODE,
    MISSING_DIFF_EVIDENCE_CODE,
    MISSING_EVIDENCE_LINK_CODE,
    MISSING_EVIDENCE_REF_CODE,
    PLACEHOLDER_CONTENT_CODE,
    UNSUPPORTED_CLAIM_CODE,
    UNSUPPORTED_VERDICT_CODE,
    UNVERIFIABLE_CHECK_CLAIM_CODE,
    has_non_placeholder_text,
    validate_semantic_outputs,
)

_SEMANTIC_FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "semantic"


def _write_stage_contract(
    *,
    contracts_root: Path,
    required_inputs: tuple[str, ...],
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
) -> None:
    (contracts_root / "idea.md").write_text(
        "\n".join(
            [
                "# Stage Contract: `idea`",
                "",
                "## Purpose",
                "",
                "Turn intake into an idea brief.",
                "",
                "## Primary output",
                "",
                *[f"- `{item}`" for item in required_outputs],
                "",
                "## Required inputs",
                "",
                *[f"- `{item}`" for item in required_inputs],
                "",
                "## Prompt pack",
                "",
                *[f"- `{item}`" for item in prompt_pack_paths],
                "",
                "## Validation focus",
                "",
                "- required heading coverage in `idea-brief.md` "
                "(`Problem statement`, `Desired outcome`, `Constraints`, `Open questions`),",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _touch_contract_references(
    *,
    repo_root: Path,
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
) -> None:
    documents_root = repo_root / "contracts" / "documents"
    documents_root.mkdir(parents=True, exist_ok=True)
    for output in required_outputs:
        (documents_root / output).write_text("# Contract\n", encoding="utf-8")

    idea_brief_contract = documents_root / "idea-brief.md"
    idea_brief_contract.write_text(
        "\n".join(
            [
                "# Document Contract: `idea-brief.md`",
                "",
                "## Required sections",
                "",
                "- `Problem statement`",
                "- `Desired outcome`",
                "- `Constraints`",
                "- `Open questions`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    for prompt_path in prompt_pack_paths:
        prompt_file = repo_root / prompt_path
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text("# Prompt\n", encoding="utf-8")


def _write_idea_brief(workspace_root: Path, body: str) -> Path:
    path = workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "idea-brief.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_research_notes(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "research" / "research-notes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_plan_document(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "plan" / "plan.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_has_non_placeholder_text_detects_placeholders() -> None:
    assert has_non_placeholder_text("Final answer with concrete detail.")
    assert not has_non_placeholder_text("TBD: fill this section later.")


def test_validate_semantic_outputs_reports_placeholder_content(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("idea-brief.md",)
    prompt_paths = ("prompt-packs/stages/idea/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    workspace_root = tmp_path / ".aidd"
    _write_idea_brief(
        workspace_root,
        (
            "# Idea Brief\n\n"
            "## Problem statement\n\n"
            "Operators need deterministic stage outputs to reduce review churn.\n\n"
            "## Desired outcome\n\n"
            "TBD define explicit acceptance signal for the first rollout milestone.\n\n"
            "## Constraints\n\n"
            "- none\n\n"
            "## Open questions\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=PLACEHOLDER_CONTENT_CODE,
            message="Placeholder content remains in required section `Desired outcome`.",
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/idea/idea-brief.md",
                line_number=7,
            ),
        ),
    )


def test_validate_semantic_outputs_reports_incomplete_section(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("idea-brief.md",)
    prompt_paths = ("prompt-packs/stages/idea/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    workspace_root = tmp_path / ".aidd"
    _write_idea_brief(
        workspace_root,
        (
            "# Idea Brief\n\n"
            "## Problem statement\n\n"
            "Short note.\n\n"
            "## Desired outcome\n\n"
            "Deliver a stable baseline with measurable rollout gates for operators.\n\n"
            "## Constraints\n\n"
            "- none\n\n"
            "## Open questions\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Required section `Problem statement` is too brief to establish "
                "a reviewable semantic baseline."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/idea/idea-brief.md",
                line_number=3,
            ),
        ),
    )


def test_validate_semantic_outputs_reports_unsupported_claims(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("idea-brief.md",)
    prompt_paths = ("prompt-packs/stages/idea/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    workspace_root = tmp_path / ".aidd"
    _write_idea_brief(
        workspace_root,
        (
            "# Idea Brief\n\n"
            "## Problem statement\n\n"
            "Release preparation currently depends on manual cross-checking "
            "and tribal knowledge.\n\n"
            "## Desired outcome\n\n"
            "This change will always guarantee zero defects in production release.\n\n"
            "## Constraints\n\n"
            "- none\n\n"
            "## Open questions\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=UNSUPPORTED_CLAIM_CODE,
            message=(
                "Section `Desired outcome` includes unsupported absolute claims "
                "without evidence grounding."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/idea/idea-brief.md",
                line_number=7,
            ),
        ),
    )


def test_validate_semantic_outputs_requires_list_format_for_constraints(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("idea-brief.md",)
    prompt_paths = ("prompt-packs/stages/idea/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    workspace_root = tmp_path / ".aidd"
    _write_idea_brief(
        workspace_root,
        (
            "# Idea Brief\n\n"
            "## Problem statement\n\n"
            "Operators spend too much time reconstructing missing task context after handoffs.\n\n"
            "## Desired outcome\n\n"
            "Capture problem framing and boundaries in a reusable artifact for "
            "downstream stages.\n\n"
            "## Constraints\n\n"
            "Keep rollout in one delivery wave and avoid introducing a new auth provider.\n\n"
            "## Open questions\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Required section `Constraints` must use bullet items "
                "(or `- none`) so downstream stages can parse constraints "
                "and open questions deterministically."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-001/stages/idea/idea-brief.md",
                line_number=11,
            ),
        ),
    )


def test_validate_semantic_outputs_passes_for_grounded_complete_content(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("idea-brief.md",)
    prompt_paths = ("prompt-packs/stages/idea/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        required_inputs=("context/intake.md",),
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    workspace_root = tmp_path / ".aidd"
    _write_idea_brief(
        workspace_root,
        (
            "# Idea Brief\n\n"
            "## Problem statement\n\n"
            "Operators spend significant time reconciling inconsistent stage outcomes "
            "before approving downstream work.\n\n"
            "## Desired outcome\n\n"
            "Provide a reviewable baseline that links each stage decision to explicit "
            "acceptance signals and documented constraints.\n\n"
            "## Constraints\n\n"
            "- keep stage outputs Markdown-first and repository-local\n\n"
            "## Open questions\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_valid_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-SEM-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-SEM-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=PLACEHOLDER_CONTENT_CODE,
            message="Placeholder content remains in required section `Desired outcome`.",
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-SEM-INVALID/stages/idea/idea-brief.md",
                line_number=7,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_valid_list_format_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "valid-list-format" / "workspace"

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-SEM-LIST-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_list_format_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "invalid-list-format" / "workspace"

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-SEM-LIST-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Required section `Constraints` must use bullet items "
                "(or `- none`) so downstream stages can parse constraints "
                "and open questions deterministically."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-LIST-INVALID/stages/idea/idea-brief.md"
                ),
                line_number=11,
            ),
        ),
    )


def test_validate_semantic_outputs_requires_citations_in_research_findings(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_research_notes(
        workspace_root,
        "WI-RESEARCH-001",
        (
            "# Research Notes\n\n"
            "## Scope\n\n"
            "- Evaluate rollout constraints for adapter integration.\n\n"
            "## Sources\n\n"
            "- [S1] docs/architecture/target-architecture.md (accessed 2026-04-22)\n\n"
            "## Findings\n\n"
            "- The adapter interface already supports runtime capability probing.\n\n"
            "## Trade-offs\n\n"
            "- none\n\n"
            "## Evidence trace\n\n"
            "- Runtime capability probing baseline -> [S1]\n\n"
            "## Open questions\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="research",
        work_item="WI-RESEARCH-001",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=MISSING_EVIDENCE_LINK_CODE,
            message=(
                "Section `Findings` must reference citation ids from "
                "`Sources` for material research claims."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-RESEARCH-001/stages/research/research-notes.md"
                ),
                line_number=11,
            ),
        ),
    )


def test_validate_semantic_outputs_rejects_unknown_research_citation_ids(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_research_notes(
        workspace_root,
        "WI-RESEARCH-002",
        (
            "# Research Notes\n\n"
            "## Scope\n\n"
            "- Evaluate rollout constraints for adapter integration.\n\n"
            "## Sources\n\n"
            "- [S1] docs/architecture/target-architecture.md (accessed 2026-04-22)\n\n"
            "## Findings\n\n"
            "- Runtime capability probing is present in the current architecture [S1].\n\n"
            "## Trade-offs\n\n"
            "- none\n\n"
            "## Evidence trace\n\n"
            "- Runtime capability probing baseline -> [S1], [S2]\n\n"
            "## Open questions\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="research",
        work_item="WI-RESEARCH-002",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=MISSING_EVIDENCE_LINK_CODE,
            message="Section `Evidence trace` references unknown citation ids: [S2].",
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-RESEARCH-002/stages/research/research-notes.md"
                ),
                line_number=19,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_valid_research_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "research-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="research",
        work_item="WI-SEM-RESEARCH-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_research_missing_source_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "research-invalid-missing-source" / "workspace"

    findings = validate_semantic_outputs(
        stage="research",
        work_item="WI-SEM-RESEARCH-MISSING-SOURCE",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=MISSING_EVIDENCE_LINK_CODE,
            message="Section `Findings` references unknown citation ids: [S2].",
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-RESEARCH-MISSING-SOURCE/stages/research/research-notes.md"
                ),
                line_number=11,
            ),
        ),
        ValidationFinding(
            code=MISSING_EVIDENCE_LINK_CODE,
            message="Section `Evidence trace` references unknown citation ids: [S2].",
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-RESEARCH-MISSING-SOURCE/stages/research/research-notes.md"
                ),
                line_number=19,
            ),
        ),
    )


def test_validate_semantic_outputs_flags_research_unresolved_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "research-invalid-unresolved-question" / "workspace"

    findings = validate_semantic_outputs(
        stage="research",
        work_item="WI-SEM-RESEARCH-UNRESOLVED",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=MISSING_EVIDENCE_LINK_CODE,
            message=(
                "Section `Findings` must reference citation ids from "
                "`Sources` for material research claims."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-RESEARCH-UNRESOLVED/stages/research/research-notes.md"
                ),
                line_number=11,
            ),
        ),
    )


def test_validate_semantic_outputs_requires_plan_verification_note_milestone_links(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_document(
        workspace_root,
        "WI-PLAN-001",
        (
            "# Plan\n\n"
            "## Goals\n\n"
            "- Deliver incident follow-up tracking.\n\n"
            "## Out of scope\n\n"
            "- none\n\n"
            "## Milestones\n\n"
            "- M1: Add persistence layer for follow-up actions.\n"
            "- M2: Expose operator workflow for action lifecycle.\n\n"
            "## Implementation strategy\n\n"
            "- Deliver M1 before M2 and keep rollout incremental.\n\n"
            "## Risks\n\n"
            "- R1: Email dispatch errors can hide alerts; mitigation: add retry checks.\n\n"
            "## Dependencies\n\n"
            "- Existing email integration utility module.\n\n"
            "## Verification approach\n\n"
            "- Run targeted checks per milestone before broad test gates.\n\n"
            "## Verification notes\n\n"
            "- Verify dispatch and retry behavior before release.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item="WI-PLAN-001",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Verification notes` must reference milestone ids "
                "(for example `M1`) to keep checks tied to planned increments."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-PLAN-001/stages/plan/plan.md",
                line_number=32,
            ),
        ),
    )


def test_validate_semantic_outputs_requires_plan_dependency_lists_and_risk_mitigation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_document(
        workspace_root,
        "WI-PLAN-002",
        (
            "# Plan\n\n"
            "## Goals\n\n"
            "- Deliver incident follow-up tracking.\n\n"
            "## Out of scope\n\n"
            "- none\n\n"
            "## Milestones\n\n"
            "- M1: Add notifications first.\n"
            "- M2: Decide data model later.\n\n"
            "## Implementation strategy\n\n"
            "- Start with whichever task seems fastest.\n\n"
            "## Risks\n\n"
            "- R1: Might be risky.\n\n"
            "## Dependencies\n\n"
            "Some internal services.\n\n"
            "## Verification approach\n\n"
            "- Run tests.\n\n"
            "## Verification notes\n\n"
            "- M1: verify notification dispatch and rollback behavior.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item="WI-PLAN-002",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each `Risks` item must include mitigation direction "
                "(for example `mitigation:`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-PLAN-002/stages/plan/plan.md",
                line_number=20,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Required section `Dependencies` must use bullet items "
                "so ordering constraints are explicit."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-PLAN-002/stages/plan/plan.md",
                line_number=24,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_valid_plan_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "plan-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="plan",
        work_item="WI-SEM-PLAN-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_plan_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "plan-invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="plan",
        work_item="WI-SEM-PLAN-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each `Risks` item must include mitigation direction "
                "(for example `mitigation:`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-SEM-PLAN-INVALID/stages/plan/plan.md",
                line_number=20,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Required section `Dependencies` must use bullet items "
                "so ordering constraints are explicit."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-SEM-PLAN-INVALID/stages/plan/plan.md",
                line_number=24,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Verification notes` must reference milestone ids "
                "(for example `M1`) to keep checks tied to planned increments."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path="workitems/WI-SEM-PLAN-INVALID/stages/plan/plan.md",
                line_number=32,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_valid_review_spec_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "review-spec-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-SEM-REVIEW-SPEC-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_review_spec_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "review-spec-invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-SEM-REVIEW-SPEC-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each `Issue list` item must include explicit severity "
                "(critical/high/medium/low)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-SPEC-INVALID/stages/review-spec/review-spec-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each `Issue list` item must include rationale "
                "(for example `because ...`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-SPEC-INVALID/stages/review-spec/review-spec-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Recommendation summary` cannot be `none`; "
                "include actionable remediation steps."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-SPEC-INVALID/stages/review-spec/review-spec-report.md"
                ),
                line_number=15,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Sections `Readiness state` and `Decision` are inconsistent: "
                "`not-ready` expects `rejected`."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-SPEC-INVALID/stages/review-spec/review-spec-report.md"
                ),
                line_number=23,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_valid_tasklist_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "tasklist-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_tasklist_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "tasklist-invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Task summary` is too brief to explain decomposition "
                "scope and sequencing intent."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-TASKLIST-INVALID/stages/tasklist/tasklist.md"
                ),
                line_number=3,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message="Section `Dependencies` references unknown task ids: TL-9.",
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-TASKLIST-INVALID/stages/tasklist/tasklist.md"
                ),
                line_number=12,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Dependencies` must include explicit entries "
                "for each task id. Missing: TL-1."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-TASKLIST-INVALID/stages/tasklist/tasklist.md"
                ),
                line_number=12,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Section `Verification notes` must include at least one "
                "check per task id. Missing: TL-2."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-TASKLIST-INVALID/stages/tasklist/tasklist.md"
                ),
                line_number=16,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_valid_implement_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "implement-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_implement_noop_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "implement-invalid-noop" / "workspace"

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-NOOP",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
            message=(
                "No-op output requires explicit evidence-backed justification "
                "in summary or follow-up notes."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-NOOP/stages/implement/implementation-report.md"
                ),
                line_number=8,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
            message=(
                "No-op output must include an actionable next step in "
                "`Follow-up notes`."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-NOOP/stages/implement/implementation-report.md"
                ),
                line_number=20,
            ),
        ),
        ValidationFinding(
            code=MISSING_DIFF_EVIDENCE_CODE,
            message=(
                "Change summary claims completed implementation but touched-files "
                "list is empty."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-NOOP/stages/implement/implementation-report.md"
                ),
                line_number=8,
            ),
        ),
        ValidationFinding(
            code=UNVERIFIABLE_CHECK_CLAIM_CODE,
            message=(
                "Verification note includes outcome claim without executable "
                "command evidence."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-NOOP/stages/implement/implementation-report.md"
                ),
                line_number=16,
            ),
        ),
    )


def test_validate_semantic_outputs_flags_invalid_implement_verification_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "implement-invalid-verification" / "workspace"

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-VERIFY",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=UNVERIFIABLE_CHECK_CLAIM_CODE,
            message=(
                "Verification note must include observed command outcome "
                "(for example `-> pass` or exit code)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-VERIFY/stages/implement/implementation-report.md"
                ),
                line_number=16,
            ),
        ),
        ValidationFinding(
            code=UNVERIFIABLE_CHECK_CLAIM_CODE,
            message=(
                "Verification note includes outcome claim without executable "
                "command evidence."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-VERIFY/stages/implement/implementation-report.md"
                ),
                line_number=16,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_valid_review_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "review-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_review_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "review-invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each finding must include explicit severity "
                "(critical/high/medium/low)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each finding must include rationale "
                "(for example `Rationale:` or `because ...`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=UNSUPPORTED_CLAIM_CODE,
            message=(
                "Finding is missing evidence reference to implementation output "
                "or acceptance criteria."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each finding must include explicit disposition "
                "(`must-fix`, `follow-up`, `accepted-risk`, or `invalid`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Each finding must include rationale "
                "(for example `Rationale:` or `because ...`)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=UNSUPPORTED_CLAIM_CODE,
            message=(
                "Finding is missing evidence reference to implementation output "
                "or acceptance criteria."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Approval status cannot be `approved` while unresolved "
                "`must-fix` findings remain."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-INVALID/stages/review/review-report.md"
                ),
                line_number=12,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_valid_qa_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "qa-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="qa",
        work_item="WI-SEM-QA-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_qa_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "qa-invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="qa",
        work_item="WI-SEM-QA-INVALID",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=MISSING_EVIDENCE_REF_CODE,
            message=(
                "Material QA claims and release recommendation must reference "
                "verification artifacts or execution outputs."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-INVALID/stages/qa/qa-report.md"
                ),
                line_number=15,
            ),
        ),
        ValidationFinding(
            code=UNSUPPORTED_VERDICT_CODE,
            message=(
                "Verdicts `ready` or `ready-with-risks` cannot pair with "
                "release recommendation `hold`."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-INVALID/stages/qa/qa-report.md"
                ),
                line_number=11,
            ),
        ),
        ValidationFinding(
            code=UNSUPPORTED_VERDICT_CODE,
            message=(
                "Ready/proceed-style outcomes are unsupported without concrete "
                "verification evidence references."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-INVALID/stages/qa/qa-report.md"
                ),
                line_number=3,
            ),
        ),
    )

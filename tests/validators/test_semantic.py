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
    RISK_UNDERREPORT_CODE,
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


def _write_tasklist_document(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "tasklist" / "tasklist.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_qa_report(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "qa" / "qa-report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_acceptance_criteria(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "context" / "acceptance-criteria.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_repository_state(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "context" / "repository-state.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_review_spec_report(workspace_root: Path, work_item: str, body: str) -> Path:
    path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "review-spec"
        / "review-spec-report.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_implementation_report(workspace_root: Path, work_item: str, body: str) -> Path:
    path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "implement"
        / "implementation-report.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_review_report(workspace_root: Path, work_item: str, body: str) -> Path:
    path = workspace_root / "workitems" / work_item / "stages" / "review" / "review-report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_has_non_placeholder_text_detects_placeholders() -> None:
    assert has_non_placeholder_text("Final answer with concrete detail.")
    assert not has_non_placeholder_text("TBD: fill this section later.")
    assert not has_non_placeholder_text("`TBD`")
    assert not has_non_placeholder_text("- `N/A`")
    assert not has_non_placeholder_text("- `...`")
    assert has_non_placeholder_text(
        "No placeholder content (`TBD`, `TODO`, `N/A`, `...`) remains."
    )
    assert has_non_placeholder_text(
        "No placeholder content (TBD, TODO, N/A, ...) detected."
    )
    assert has_non_placeholder_text(
        '- No\n  ambiguous "TBD" entries remain in the report.'
    )
    assert has_non_placeholder_text(
        "- No\n  `N/A` values are used for required evidence."
    )
    assert has_non_placeholder_text(
        "TSV header-only input is exercised with `sqlite-utils insert ... --tsv`."
    )
    assert has_non_placeholder_text(
        "```\nAssertionError: Cannot transform a table\n```\n"
        "Then call `transform(...)` only when the table exists."
    )
    assert has_non_placeholder_text(
        "The final frame is `db.py:1888 ... AssertionError: Cannot transform "
        "a table that\ndoesn't exist yet` invoked from `cli.py:1180`."
    )
    assert has_non_placeholder_text(
        'The prose says "edit `cli.py:1179` ... so the transform call is skipped".'
    )
    assert not has_non_placeholder_text("Placeholder: TBD")
    assert not has_non_placeholder_text("- Evidence state:\n  TBD define signal.")


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


def test_validate_semantic_outputs_allows_inline_placeholder_examples(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("validator-report.md",)
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
    (tmp_path / "contracts" / "documents" / "validator-report.md").write_text(
        "\n".join(
            [
                "# Document Contract: `validator-report.md`",
                "",
                "## Required sections",
                "",
                "- `Semantic checks`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    workspace_root = tmp_path / ".aidd"
    output_path = (
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "idea"
        / "validator-report.md"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        (
            "# Validator Report\n\n"
            "## Semantic checks\n\n"
            "No placeholder content (`TBD`, `TODO`, `N/A`, `...`) remains "
            "in required sections.\n"
        ),
        encoding="utf-8",
    )

    findings = validate_semantic_outputs(
        stage="idea",
        work_item="WI-001",
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )

    assert findings == ()


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


def test_validate_semantic_outputs_allows_negated_security_guarantee_caveat(
    tmp_path: Path,
) -> None:
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
            "The CLI needs an explicit trust boundary for user-provided Python code.\n\n"
            "## Desired outcome\n\n"
            "Document the feature and its caveats without implying a broader security "
            "guarantee for untrusted code.\n\n"
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

    assert findings == ()


def test_validate_semantic_outputs_allows_disclaimed_security_guarantee_caveat(
    tmp_path: Path,
) -> None:
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
            "The CLI needs clear documentation that includes an explicit disclaimer "
            "of sandboxing or any security guarantee for local Python execution.\n\n"
            "## Desired outcome\n\n"
            "Document the feature with a warning callout that explicitly disclaims "
            "sandboxing or any security guarantee.\n\n"
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

    assert findings == ()


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
                "Required section `Open questions` must use bullet items "
                "(or `- none`) so downstream stages can parse constraints "
                "and open questions deterministically."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-LIST-INVALID/stages/idea/idea-brief.md"
                ),
                line_number=15,
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


def test_validate_semantic_outputs_accepts_nested_plan_risk_mitigation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_document(
        workspace_root,
        "WI-PLAN-003",
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
            "- **R1 - Dispatch errors hide alerts.**\n"
            "  - risk: Operators may miss failed delivery.\n"
            "  - mitigation: Add retry checks and error logging.\n"
            "  - verification: M1 validates delivery failures.\n\n"
            "- **R2 - Lifecycle events drift.**\n"
            "  - risk: Follow-up state can become inconsistent.\n"
            "  - mitigation: Verify state transitions before release.\n"
            "  - verification: M2 validates operator workflow transitions.\n\n"
            "## Dependencies\n\n"
            "- Existing email integration utility module.\n\n"
            "## Verification approach\n\n"
            "- Run targeted checks per milestone before broad test gates.\n\n"
            "## Verification notes\n\n"
            "- M1: verify dispatch and retry behavior before release.\n"
            "- M2: verify lifecycle transitions before hand-off.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item="WI-PLAN-003",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_plan_risk_table_mitigation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_document(
        workspace_root,
        "WI-PLAN-TABLE-RISKS",
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
            "| Risk | Likelihood | Impact | Mitigation | Verification |\n"
            "|------|------------|--------|------------|--------------|\n"
            "| R1 - Dispatch errors hide alerts | Low | Medium | "
            "Add retry checks and error logging. | "
            "M1 validates delivery failures. |\n"
            "| R2 - Lifecycle events drift | Low | Medium | "
            "Verify state transitions before release. | "
            "M2 validates operator workflow transitions. |\n\n"
            "## Dependencies\n\n"
            "- Existing email integration utility module.\n\n"
            "## Verification approach\n\n"
            "- Run targeted checks per milestone before broad test gates.\n\n"
            "## Verification notes\n\n"
            "- M1: verify dispatch and retry behavior before release.\n"
            "- M2: verify lifecycle transitions before hand-off.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item="WI-PLAN-TABLE-RISKS",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_requires_each_nested_plan_risk_to_include_mitigation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_document(
        workspace_root,
        "WI-PLAN-004",
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
            "- **R1 - Dispatch errors hide alerts.**\n"
            "  - risk: Operators may miss failed delivery.\n"
            "  - mitigation: Add retry checks and error logging.\n"
            "  - verification: M1 validates delivery failures.\n\n"
            "- **R2 - Lifecycle events drift.**\n"
            "  - risk: Follow-up state can become inconsistent.\n"
            "  - verification: M2 validates operator workflow transitions.\n\n"
            "## Dependencies\n\n"
            "- Existing email integration utility module.\n\n"
            "## Verification approach\n\n"
            "- Run targeted checks per milestone before broad test gates.\n\n"
            "## Verification notes\n\n"
            "- M1: verify dispatch and retry behavior before release.\n"
            "- M2: verify lifecycle transitions before hand-off.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item="WI-PLAN-004",
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
                workspace_relative_path="workitems/WI-PLAN-004/stages/plan/plan.md",
                line_number=20,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_subheaded_plan_risks(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_document(
        workspace_root,
        "WI-PLAN-005",
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
            "### R1 - Dispatch errors hide alerts\n\n"
            "- Impact: Operators may miss failed delivery.\n"
            "- Mitigation intent: Add retry checks and error logging.\n"
            "- Verification linkage: M1 validates delivery failures.\n\n"
            "### R2 - Lifecycle events drift\n\n"
            "- Impact: Follow-up state can become inconsistent.\n"
            "- Mitigation intent: Verify state transitions before release.\n"
            "- Verification linkage: M2 validates operator workflow transitions.\n\n"
            "## Dependencies\n\n"
            "- Existing email integration utility module.\n\n"
            "## Verification approach\n\n"
            "- Run targeted checks per milestone before broad test gates.\n\n"
            "## Verification notes\n\n"
            "- M1: verify dispatch and retry behavior before release.\n"
            "- M2: verify lifecycle transitions before hand-off.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item="WI-PLAN-005",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_requires_each_subheaded_plan_risk_to_include_mitigation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_plan_document(
        workspace_root,
        "WI-PLAN-006",
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
            "### R1 - Dispatch errors hide alerts\n\n"
            "- Impact: Operators may miss failed delivery.\n"
            "- Mitigation intent: Add retry checks and error logging.\n"
            "- Verification linkage: M1 validates delivery failures.\n\n"
            "### R2 - Lifecycle events drift\n\n"
            "- Impact: Follow-up state can become inconsistent.\n"
            "- Verification linkage: M2 validates operator workflow transitions.\n\n"
            "## Dependencies\n\n"
            "- Existing email integration utility module.\n\n"
            "## Verification approach\n\n"
            "- Run targeted checks per milestone before broad test gates.\n\n"
            "## Verification notes\n\n"
            "- M1: verify dispatch and retry behavior before release.\n"
            "- M2: verify lifecycle transitions before hand-off.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item="WI-PLAN-006",
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
                workspace_relative_path="workitems/WI-PLAN-006/stages/plan/plan.md",
                line_number=20,
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


def test_validate_semantic_outputs_accepts_review_spec_nested_issue_metadata(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-NESTED",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- **State:** `ready`\n\n"
            "## Issue list\n\n"
            "- **OBS-1** - `info` - Plan line numbers are one-off from "
            "`transform` call in prose, but the actual edit target is correct.\n"
            "  - **Severity:** `info`\n"
            "  - **Rationale:** The prose says \"edit `cli.py:1179` ... so the "
            "transform call is skipped\" because the edit is scoped to the guard "
            "line and not to unrelated behavior.\n\n"
            "## Strengths\n\n"
            "- The plan is scoped to a minimal regression fix with targeted tests.\n\n"
            "## Recommendation summary\n\n"
            "- Adopt the plan as-is; no remediation is required for OBS-1.\n\n"
            "## Required changes\n\n"
            "None.\n\n"
            "## Decision\n\n"
            "- **Status:** `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-NESTED",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_spec_issue_subsections(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-SUBSECTIONS",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- Readiness: `ready`\n\n"
            "## Issue list\n\n"
            "Each issue is severity-tagged and rationale-backed.\n\n"
            "### I1 - Conditional implementation shape\n\n"
            "- **Severity:** low\n"
            "- **Section:** `Milestones > M3`.\n"
            "- **Observation:** The plan keeps two implementation shapes open.\n"
            "- **Rationale:** because the downstream implement stage must record "
            "which shape it chose and why; this is advisory, not blocking.\n\n"
            "### I2 - Test file location remains flexible\n\n"
            "- **Severity:** info\n"
            "- **Section:** `Milestones > M1`.\n"
            "- **Observation:** The exact test file is left to implementation.\n"
            "- **Rationale:** because the repo layout is observable at task time "
            "and the recommendation only improves traceability.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "- **(Highest impact, maps to I1)** Record the chosen implementation "
            "shape in `stage-result.md`.\n"
            "- **(Lower impact, maps to I2)** Pin test filenames during task "
            "decomposition.\n\n"
            "## Required changes\n\n"
            "- none\n\n"
            "## Decision\n\n"
            "- Decision: `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-SUBSECTIONS",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_spec_no_issue_markers(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-NO-ISSUES",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- Readiness: `ready`\n\n"
            "## Issue list\n\n"
            "- **I1 - Upstream issue-id discrepancy is advisory.**\n"
            "  - Severity: `low`\n"
            "  - Rationale: because the plan records the discrepancy and maps "
            "it to a commit-message recommendation.\n"
            "- **I2 - No material defect found that blocks decomposition.**\n"
            "  - Severity: `none`\n"
            "  - Rationale: Plan goals, scope, milestones, dependencies, risks, "
            "and verification approach are mutually consistent.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "- **(High priority, maps to I1)** Preserve the documented issue-id "
            "wording in downstream commit text.\n\n"
            "## Required changes\n\n"
            "- none\n\n"
            "## Decision\n\n"
            "- Decision: `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-NO-ISSUES",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_spec_inline_severity_label(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-INLINE-SEVERITY",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- `ready-with-conditions`\n\n"
            "## Issue list\n\n"
            "- I1: Severity: low. Rationale: because the plan should add one "
            "delegated constructor smoke check during downstream tasking.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "1. Add the delegated constructor smoke check before implementation sign-off.\n"
            "2. Proceed with task decomposition after carrying I1 into the tasklist.\n\n"
            "## Required changes\n\n"
            "- Add or assign the I1 smoke check during task decomposition.\n\n"
            "## Decision\n\n"
            "- `approved-with-conditions`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-INLINE-SEVERITY",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_review_spec_no_issue_prose_without_metadata(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-NO-ISSUE-PROSE",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- Readiness: `ready`\n\n"
            "## Issue list\n\n"
            "No material issues identified.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "- Proceed with implementation using the planned verification order.\n\n"
            "## Required changes\n\n"
            "- none\n\n"
            "## Decision\n\n"
            "- Decision: `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-NO-ISSUE-PROSE",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Required section `Issue list` must use bullet items with "
                "severity and rationale."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-REVIEW-SPEC-NO-ISSUE-PROSE/stages/review-spec/"
                    "review-spec-report.md"
                ),
                line_number=7,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_review_spec_ordered_recommendations(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_spec_report(
        workspace_root,
        "WI-REVIEW-SPEC-ORDERED-RECS",
        (
            "# Review Spec Report\n\n"
            "## Readiness state\n\n"
            "- Readiness: `ready`\n\n"
            "## Issue list\n\n"
            "- **I1 - Memory command assertion can be stronger.**\n"
            "  - Severity: `low`\n"
            "  - Rationale: because adding an output assertion would tighten "
            "the regression without changing scope.\n\n"
            "## Strengths\n\n"
            "- The plan is bounded and test-first.\n\n"
            "## Recommendation summary\n\n"
            "1. **Approve and proceed.** The plan is coherent and bounded.\n"
            "2. **Optionally tighten memory assertions.** Confirm no "
            "`AssertionError` appears in command output.\n\n"
            "## Required changes\n\n"
            "- none\n\n"
            "## Decision\n\n"
            "- Decision: `approved`\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review-spec",
        work_item="WI-REVIEW-SPEC-ORDERED-RECS",
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
                "(critical/high/medium/low/info/none)."
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


def test_validate_semantic_outputs_accepts_compact_tasklist_ids(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist_document(
        workspace_root,
        "WI-SEM-TASKLIST-COMPACT",
        (
            "# Tasklist\n\n"
            "## Task summary\n\n"
            "Decompose the live sqlite-utils fix into ordered, reviewable tasks "
            "with explicit verification coverage.\n\n"
            "## Ordered tasks\n\n"
            "### T1 - Confirm upstream issue shape\n\n"
            "- Dominant output artifact: issue cross-check notes.\n"
            "- Dependencies: none.\n"
            "- Verification note: issue text matches the reproduced assertion.\n\n"
            "### T2 - Add insert regression test\n\n"
            "- Dominant output artifact: `tests/test_cli_insert.py` regression.\n"
            "- Dependencies: `T1`.\n"
            "- Verification note: run `pytest tests/test_cli_insert.py -q`; "
            "this covers the default post-4.0a1 path without treating that "
            "version phrase as a task id.\n\n"
            "### T3 - Guard insert transform call\n\n"
            "- Dominant output artifact: one guard in `sqlite_utils/cli.py`.\n"
            "- Dependencies: `T2`.\n"
            "- Verification note: run the insert regression plus happy-path CSV tests.\n\n"
            "## Dependencies\n\n"
            "- `T1`: none.\n"
            "- `T1 -> T2`: T2 locks the regression contract after issue confirmation.\n"
            "- `T2 -> T3`: T3 applies the guard only after the failing test exists.\n\n"
            "## Verification notes\n\n"
            "- `T1`: recorded issue cross-check evidence.\n"
            "- `T2`: `pytest tests/test_cli_insert.py -q` fails before the guard and "
            "passes after it.\n"
            "- `T3`: `pytest tests/test_cli_insert.py -q` and existing CSV happy-path "
            "tests pass.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-COMPACT",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_ignores_tradeoff_ids_when_tasklist_uses_tl_ids(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist_document(
        workspace_root,
        "WI-SEM-TASKLIST-TL",
        (
            "# Tasklist\n\n"
            "## Task summary\n\n"
            "Decompose the live sqlite-utils fix into ordered, reviewable tasks "
            "while retaining references to plan trade-offs T1 and T2 as context.\n\n"
            "## Ordered tasks\n\n"
            "### TL-1 - Add regression tests\n\n"
            "- Dominant output artifact: `tests/test_cli.py` regression.\n"
            "- Dependencies: none.\n"
            "- Verification note: fails before the guard.\n\n"
            "### TL-2 - Apply guard\n\n"
            "- Dominant output artifact: one guard in `sqlite_utils/cli.py`.\n"
            "- Dependencies: `TL-1`.\n"
            "- Verification note: covers trade-off T1 and rejected option T2.\n\n"
            "### TL-3 - Run full suite\n\n"
            "- Dominant output artifact: pytest output.\n"
            "- Dependencies: `TL-2`.\n"
            "- Verification note: records trade-off T3 as non-blocking context.\n\n"
            "## Dependencies\n\n"
            "- `TL-1`: none.\n"
            "- `TL-2`: depends on `TL-1`.\n"
            "- `TL-3`: depends on `TL-2`.\n\n"
            "## Verification notes\n\n"
            "- `TL-1`: targeted regression fails before the patch.\n"
            "- `TL-2`: targeted regression passes after the patch; plan trade-off T1 "
            "is still cited as rationale.\n"
            "- `TL-3`: full suite passes and documents trade-off T3 scope handling.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-TL",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_ignores_review_and_acceptance_ids_when_tasklist_uses_t_ids(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist_document(
        workspace_root,
        "WI-SEM-TASKLIST-T",
        (
            "# Tasklist\n\n"
            "## Task summary\n\n"
            "Decompose the sqlite-utils fix into compact T-prefixed tasks while "
            "preserving review condition ids RC-1 and RC-2 plus AC-3 as context.\n\n"
            "## Ordered tasks\n\n"
            "### T1 - Pre-write reproduction\n\n"
            "- Dominant output artifact: RC-1 scratch reproduction notes.\n"
            "- Dependencies: none.\n"
            "- Verification note: confirms whether AC-3 can be exercised safely.\n\n"
            "### T2 - Add regression test\n\n"
            "- Dominant output artifact: one pytest function covering RC-2.\n"
            "- Dependencies: `T1`.\n"
            "- Verification note: fails before the guard and includes stderr coverage.\n\n"
            "### T3 - Apply guard\n\n"
            "- Dominant output artifact: one guard in `sqlite_utils/cli.py`.\n"
            "- Dependencies: `T2`.\n"
            "- Verification note: passes the regression and keeps RC-1 satisfied.\n\n"
            "## Dependencies\n\n"
            "- `T1`: none; implements review condition `RC-1`.\n"
            "- `T2`: depends on `T1`; covers `AC-3` and `RC-2`.\n"
            "- `T3`: depends on `T2`; keeps `RC-1` from widening scope.\n\n"
            "## Verification notes\n\n"
            "- `T1`: scratch reproduction records the `RC-1` branch outcome.\n"
            "- `T2`: targeted pytest fails before the guard and satisfies `AC-3`.\n"
            "- `T3`: targeted pytest passes after the guard; `RC-2` stderr assertion remains.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-T",
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


def test_validate_semantic_outputs_accepts_live_style_implementation_report(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-LIVE",
        (
            "# Implementation Report\n\n"
            "## Selected task id\n\n"
            "- `ISSUE-705`, traced to tasklist tasks `TL-1` through `TL-5`.\n\n"
            "## Summary\n\n"
            "Implemented the bounded header-only CSV fix and mapped the source "
            "edits, regression tests, and verification evidence back to the "
            "selected tasklist tasks.\n\n"
            "## Touched files\n\n"
            "- `sqlite_utils/cli.py` -> guard the two existing transform follow-up paths.\n"
            "  - line 1179: `if tracker is not None:` -> "
            "`if tracker is not None and tracker.types:`.\n"
            "  - line 2036: `if tracker is not None:` -> "
            "`if tracker is not None and tracker.types:`.\n"
            "- `tests/test_cli.py` -> add focused header-only CSV/TSV regression tests.\n\n"
            "```diff\n"
            "-        if tracker is not None:\n"
            "+        if tracker is not None and tracker.types:\n"
            "```\n\n"
            "## Verification\n\n"
            "### TL-4 regression and gate evidence\n\n"
            "- `.venv/bin/python -c \"import sqlite_utils.cli\"` -> printed `OK`.\n"
            "- `.venv/bin/pytest tests/` -> `1045 passed, 16 skipped`, exit `0`.\n"
            "- `.venv/bin/sqlite-utils schema test.db` -> "
            "`CREATE TABLE \"people\" (\"name\" TEXT, \"age\" TEXT);` "
            "-> matches expected post-fix schema.\n"
            "- `.venv/bin/mypy sqlite_utils tests` ->\n"
            "  `Success: no issues found in 55 source files`, exit `0`.\n"
            "- `.venv/bin/ty check sqlite_utils` -> `Found 21 diagnostics`, exit `1`.\n"
            "  The output matched the pre-patch baseline exactly.\n\n"
            "### TL-6 audit evidence\n\n"
            "- Command: `Grep` pattern "
            "`transform\\(types=tracker\\.types\\)|if tracker is not None` on "
            "`sqlite_utils/`\n"
            "  -> outcome: 2 production matches in `sqlite_utils/cli.py` and 2 "
            "docstring matches in `sqlite_utils/utils.py`.\n"
            "- Command: `git diff --stat`\n"
            "  -> outcome: 3 files changed, 57 insertions(+), 2 deletions(-); "
            "changed files limited to `sqlite_utils/cli.py`, `tests/test_cli.py`, "
            "and `tests/test_cli_memory.py`.\n\n"
            "### TL-5 evidence bundle\n\n"
            "- `validator-report.md` records the draft self-validator pass.\n"
            "- QA reproduction recipe:\n"
            "  - `printf 'a,b,c\\n' > /tmp/header_only.csv && "
            ".venv/bin/sqlite-utils insert /tmp/test.db tbl /tmp/header_only.csv --csv`\n"
            "    -> exit `0`, no traceback.\n"
            "  - `git stash -- sqlite_utils/cli.py` then "
            "`.venv/bin/pytest tests/test_cli.py -k header_only -v` "
            "-> 5 failures with the original assertion signature.\n\n"
            "## Risks\n\n"
            "- Existing `ty` and `black` findings are pre-existing baseline noise.\n\n"
            "## Follow-up\n\n"
            "- No deferred items before QA.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-LIVE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_requires_live_ignored_residue_evidence_for_implement(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-IMPLEMENT-LIVE-RESIDUE"
    _write_repository_state(
        workspace_root,
        work_item,
        (
            "# Repository State\n\n"
            "## Live setup workspace baseline\n\n"
            "- Known harness config present: `aidd.example.toml`.\n"
        ),
    )
    _write_implementation_report(
        workspace_root,
        work_item,
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Task id: `TASK-LIVE-HONO-NON-ERROR-THROW`.\n\n"
            "## Change summary\n\n"
            "Implemented the selected live task and added focused regression coverage.\n\n"
            "## Touched files\n\n"
            "- `src/hono-base.ts` - normalize thrown non-Error values.\n"
            "- `src/hono.test.ts` - add non-Error throw regression coverage.\n\n"
            "## Verification notes\n\n"
            "- `./node_modules/.bin/vitest --run --coverage.enabled=false "
            "src/hono.test.ts` -> pass (new regression passed).\n"
            "- `./node_modules/.bin/tsc --noEmit` -> pass.\n\n"
            "## Follow-up notes\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert any(
        finding.code == UNVERIFIABLE_CHECK_CLAIM_CODE
        and "git status --ignored --short --untracked-files=all" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_accepts_live_ignored_residue_evidence_for_implement(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-IMPLEMENT-LIVE-RESIDUE-CLEAN"
    _write_repository_state(
        workspace_root,
        work_item,
        (
            "# Repository State\n\n"
            "## Live setup workspace baseline\n\n"
            "- Known harness config present: `aidd.example.toml`.\n"
        ),
    )
    _write_implementation_report(
        workspace_root,
        work_item,
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Task id: `TASK-LIVE-HONO-NON-ERROR-THROW`.\n\n"
            "## Change summary\n\n"
            "Implemented the selected live task and added focused regression coverage.\n\n"
            "## Touched files\n\n"
            "- `src/hono-base.ts` - normalize thrown non-Error values.\n"
            "- `src/hono.test.ts` - add non-Error throw regression coverage.\n\n"
            "## Verification notes\n\n"
            "- `./node_modules/.bin/vitest --run --coverage.enabled=false "
            "src/hono.test.ts` -> pass (new regression passed).\n"
            "- `./node_modules/.bin/tsc --noEmit` -> pass.\n"
            "- `git status --ignored --short --untracked-files=all` -> pass "
            "(no new `coverage/`, `.coverage*`, `__pycache__/`, build, dist, "
            "or dependency-cache residue beyond setup baseline).\n\n"
            "## Follow-up notes\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_aidd_command_evidence_for_implement(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-IMPLEMENT-AIDD-COMMAND"
    _write_implementation_report(
        workspace_root,
        work_item,
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Task id: `TASK-LIVE-SQLITE-YIELDED-ROWS`.\n\n"
            "## Change summary\n\n"
            "Implemented the selected live task and preserved operator answer alignment.\n\n"
            "## Touched files\n\n"
            "- `sqlite_utils/cli.py` - add yielded rows option handling.\n"
            "- `tests/test_cli_insert.py` - cover yielded rows behavior.\n\n"
            "## Verification notes\n\n"
            "- `aidd stage questions idea --work-item WI-LIVE-SQLITE-INTERVIEW` "
            "-> pass (exit code 0; no unresolved blocking questions).\n\n"
            "## Follow-up notes\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_sed_command_evidence_for_implement(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-IMPLEMENT-LIVE-SED"
    _write_repository_state(
        workspace_root,
        work_item,
        (
            "# Repository State\n\n"
            "## Live setup workspace baseline\n\n"
            "- Known harness config present: `aidd.example.toml`.\n"
        ),
    )
    _write_implementation_report(
        workspace_root,
        work_item,
        (
            "# Implementation Report\n\n"
            "## Summary\n\n"
            "- Selected task id: `TASK-LIVE-HONO-NON-ERROR-THROW`.\n"
            "- Implemented bounded non-Error throw normalization with focused "
            "regression coverage and public type compatibility checks.\n\n"
            "## Touched files\n\n"
            "- `src/compose.ts` - normalize composed middleware thrown values.\n"
            "- `src/hono-base.ts` - normalize direct route thrown values.\n"
            "- `src/hono.test.ts` - add primitive and object throw regressions.\n"
            "- `src/compose.test.ts` - add composed middleware regression coverage.\n\n"
            "## Verification\n\n"
            "- `./node_modules/.bin/vitest --run --coverage.enabled=false "
            "src/hono.test.ts src/compose.test.ts` -> pass (235 passed).\n"
            "- `./node_modules/.bin/tsc --noEmit` -> pass (exit code 0).\n"
            "- `sed -n '113,119p' src/types.ts` -> pass (observed `ErrorHandler` "
            "still accepts `err: Error | HTTPResponseError`).\n"
            "- `sed -n '319,334p' src/context.ts` -> pass (observed `Context.error` "
            "remains `Error | undefined`).\n"
            "- `git status --ignored --short --untracked-files=all` -> pass "
            "(no new `coverage/`, `.coverage*`, `__pycache__/`, build, dist, "
            "or dependency-cache residue beyond setup baseline).\n\n"
            "## Risks\n\n"
            "- Public type compatibility remains source-compatible.\n\n"
            "## Follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_contract_summary_task_id_and_cli_subcommands(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-SUMMARY-ID",
        (
            "# Implementation Report\n\n"
            "## Summary\n\n"
            "- Task id: `ISSUE-705`\n"
            "- Traced to tasklist: `TL-1` and `TL-2`.\n\n"
            "This change fixes the header-only CSV crash by guarding the "
            "`transform(types=tracker.types)` follow-up path and adding a "
            "focused regression test.\n\n"
            "## Touched files\n\n"
            "- `sqlite_utils/cli.py` - add table-existence guard before transform.\n"
            "- `tests/test_cli.py` - add header-only CSV regression coverage.\n\n"
            "## Verification\n\n"
            "### TL-1 verification\n\n"
            "- `pytest tests/test_cli.py::test_insert_detect_types -v`\n"
            "  - Observed: 3 passed in 0.50s\n"
            "  - Verdict: pass\n\n"
            "- Manual parity check (insert path, header-only CSV):\n"
            "  - `insert ... --csv` with `input=\"name,age\\n\"`: "
            "exit_code 0, no `creatures` table created\n"
            "  - `insert ... --csv --no-detect-types` with same input: "
            "exit_code 0, no `creatures` table created\n"
            "  - Verdict: parity confirmed\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-SUMMARY-ID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_block_scoped_verification_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-BLOCK-EVIDENCE",
        (
            "# Implementation Report\n\n"
            "## Summary\n\n"
            "- Task id: `ISSUE-705`\n"
            "- Traced to tasklist: `TL-1` and `TL-2`.\n\n"
            "Implemented the bounded header-only CSV fix and recorded command "
            "evidence by verification subsection.\n\n"
            "## Touched files\n\n"
            "- `sqlite_utils/cli.py` - add table-existence guard before transform.\n"
            "- `tests/test_cli.py` - add header-only CSV regression coverage.\n\n"
            "## Verification\n\n"
            "### T1 - reproduction evidence\n\n"
            "- Command: `python -m sqlite_utils insert /tmp/t.db t "
            "/tmp/header.csv --csv --detect-types` -> exit code `1`.\n"
            "- Observed stderr from the T1 reproduction command -> "
            "`AssertionError: Cannot transform a table that doesn't exist yet` -> pass.\n"
            "- Baseline shape command: `python -m sqlite_utils insert /tmp/base.db t "
            "/tmp/header.csv --csv --no-detect-types` -> exit code `0`.\n\n"
            "### T4 - scenario verification\n\n"
            "- Command: `.venv/bin/python -m pytest -q` from the repository root.\n"
            "- Outcome: `1041 passed, 16 skipped in 5.97s`, exit code `0` -> pass.\n"
            "- Targeted baseline re-run command: `.venv/bin/python -m pytest "
            "tests/test_cli_insert.py -q` -> `43 passed in 0.55s`, "
            "exit code `0` -> pass.\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-BLOCK-EVIDENCE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_flat_live_verification_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-FLAT-LIVE",
        (
            "# Implementation Report\n\n"
            "## Selected task id\n\n"
            "- `ISSUE-705` -- header-only CSV bugfix.\n\n"
            "## Summary\n\n"
            "Implemented the bounded header-only CSV fix and mapped the source "
            "edits, regression tests, and verification evidence back to the "
            "selected tasklist tasks.\n\n"
            "## Touched files\n\n"
            "- `sqlite_utils/cli.py` - add table-existence guard before transform.\n"
            "- `tests/test_cli.py` - add header-only CSV regression coverage.\n\n"
            "## Verification\n\n"
            "- `T1` -- diff inspection: `git diff sqlite_utils/cli.py` shows "
            "two hunks only, each adding the issue-naming comment plus the "
            "`if db.table(...).exists():` gate.\n"
            "- `T1` -- live reproduction: `uv run python -c \"...\"` invoking "
            "`CliRunner().invoke(...)` -> `exit_code == 0`, `output == \"\"`, "
            "`exception is None`. Observed.\n"
            "- `T2` -- revert sanity check: `git stash push -- sqlite_utils/cli.py "
            "&& uv run pytest tests/test_cli.py::test_insert_detect_types_header_only_csv` "
            "-> `3 failed` with `AssertionError`; `git stash pop` restored the "
            "fix; subsequent re-run -> `3 passed`.\n"
            "- `T3` -- revert sanity check: same stash/pop procedure as `T2` "
            "-> `3 failed` with the same `AssertionError`; restored the fix; "
            "re-run -> `3 passed`.\n"
            "- `T4` -- revert sanity check: stash/pop procedure -> the `None` "
            "parametrization fails with the pre-fix assertion; restored the "
            "fix; re-run -> `3 passed`.\n"
            "- `T5` -- boundary check: `git diff --name-only` -> "
            "`sqlite_utils/cli.py`, `tests/test_cli.py` only. "
            "`git diff sqlite_utils/db.py sqlite_utils/utils.py` -> empty.\n"
            "- `T7` -- not run in this stage; deferred to the `qa` stage.\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-FLAT-LIVE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_rg_verification_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-RG-EVIDENCE",
        (
            "# Implementation Report\n\n"
            "## Selected task id\n\n"
            "- `TASK-123`, decomposed into tasklist item `TL-2`.\n\n"
            "## Summary\n\n"
            "Implemented the scoped task and used command readback to confirm "
            "the repaired document shape and stage status.\n\n"
            "## Touched files\n\n"
            "- `src/example.py` - apply the selected scoped change.\n\n"
            "## Verification\n\n"
            "- Repair readback: `rg -n '^## (Summary|Verification)$|Status:' "
            ".aidd/workitems/WI-123/stages/implement` -> exit code 0; "
            "confirmed expected headings and status markers.\n"
            "- Downstream artifact check: `test -f "
            ".aidd/workitems/WI-123/stages/qa/output/stage-result.md` -> "
            "exit code 1; expected because QA output is downstream of implement.\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-RG-EVIDENCE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_find_cleanup_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-FIND-CLEANUP",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-LIVE-TYPER-BOOLEAN-HELP`\n\n"
            "## Summary\n\n"
            "Implemented the selected task and recorded cleanup checks for "
            "workspace hygiene.\n\n"
            "## Touched files\n\n"
            "- `typer/core.py` - update boolean option help rendering.\n"
            "- `tests/test_tutorial/test_parameter_types/test_bool/test_help_rendering.py` "
            "- add focused help output coverage.\n\n"
            "## Verification\n\n"
            "- `find typer tests docs_src -type d -name __pycache__ -print` "
            "-> pass (zero output after cleanup).\n"
            "- `find . -maxdepth 1 -type d -name workitems -print` "
            "-> pass (no top-level `workitems/` directory was created).\n"
            "- `test ! -e .pytest_cache` -> pass (pytest cache removed after verification).\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-FIND-CLEANUP",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_python_c_output_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-PYTHON-C-OUTPUT",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-LIVE-SQLITE-YIELDED-ROWS`\n\n"
            "## Summary\n\n"
            "Implemented the selected yielded-rows CLI behavior and recorded "
            "target-local command evidence for focused tests, help output, "
            "runtime success paths, and invalid-input behavior.\n\n"
            "## Touched files\n\n"
            "- `sqlite_utils/cli.py` - add trusted Python file input handling.\n"
            "- `tests/test_cli_insert.py` - cover rows, yields, and invalid input.\n"
            "- `docs/cli.rst` - document the trusted-code boundary.\n\n"
            "## Verification\n\n"
            "- `python -m pytest tests/test_cli_insert.py -q` "
            "-> output: `52 passed in 1.01s`.\n"
            "- `python -c \"from click.testing import CliRunner; "
            "from sqlite_utils import cli; result = CliRunner().invoke("
            "cli.cli, ['insert', '--help']); print(result.output)\"` "
            "-> output contains: `--python-file FILE`.\n"
            "- `python -c \"from click.testing import CliRunner; "
            "from sqlite_utils import cli; result = CliRunner().invoke("
            "cli.cli, ['insert', '/tmp/test.db', 'people', '--python-file', "
            "'/tmp/rows_test.py']); print(result.exit_code)\"` "
            "-> output: `0`.\n"
            "- `python -c \"from click.testing import CliRunner; "
            "from sqlite_utils import cli; result = CliRunner().invoke("
            "cli.cli, ['insert', '/tmp/test.db', 'items', '--python-file', "
            "'/tmp/rows_test.py', '--csv']); print(result.output); "
            "print(result.exit_code)\"` "
            "-> output: `Error: Cannot use --python-file with --csv\\n1`.\n\n"
            "## Risks\n\n"
            "- No residual product risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-PYTHON-C-OUTPUT",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_sphinx_build_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-SPHINX-BUILD",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-LIVE-SQLITE-YIELDED-ROWS`\n\n"
            "## Summary\n\n"
            "Implemented the selected documentation-bearing CLI behavior and "
            "recorded a concrete documentation build command with observed output.\n\n"
            "## Touched files\n\n"
            "- `docs/cli.rst` - document the new CLI option and trust boundary.\n\n"
            "## Verification\n\n"
            "- `sphinx-build docs docs/_build` -> build succeeded, 16 warnings "
            "(exit code 0).\n\n"
            "## Risks\n\n"
            "- No residual product risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-SPHINX-BUILD",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_live_selected_task_and_not_run_checks(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-LIVE-TASK-ID",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Work item: `WI-LIVE-TYPER-BOOLEAN`\n"
            "- Stable selected task id: `TASK-LIVE-TYPER-BOOLEAN-HELP`\n"
            "- Selected task title: boolean option help rendering\n\n"
            "## Summary\n\n"
            "Implemented the selected live task by changing the Rich help label "
            "rendering and adding focused regression coverage for grouped "
            "boolean option labels while preserving default details.\n\n"
            "## Touched files\n\n"
            "- `typer/rich_utils.py` - group boolean option labels when secondary flags exist.\n"
            "- `tests/test_tutorial/test_parameter_types/test_bool/test_tutorial003.py` - add "
            "Rich label and default preservation assertions.\n\n"
            "## Verification\n\n"
            "- Authored Rich-mode command `uv run pytest -q "
            "tests/test_tutorial/test_parameter_types/test_bool` -> blocked before pytest: "
            "`error: failed to open file /Users/example/.cache/uv/sdists-v9/.git: "
            "Operation not permitted (os error 1)`.\n"
            "- Sandbox-compatible Rich command `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q "
            "tests/test_tutorial/test_parameter_types/test_bool` -> pass, `43 passed in 1.95s`.\n"
            "- QA output existence check `test -f "
            ".aidd/workitems/WI-LIVE-TYPER-BOOLEAN/stages/qa/output/stage-result.md` "
            "-> not-run, targets a downstream QA-stage artifact that is not produced by "
            "the implement stage.\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-LIVE-TASK-ID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_bun_verification_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-BUN",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-LIVE-HONO-NON-ERROR-THROW`\n"
            "- Selected task title: non-Error throw handling\n\n"
            "## Summary\n\n"
            "Implemented the selected Hono runtime error-handling task and "
            "recorded focused regression coverage plus broad-suite evidence.\n\n"
            "## Touched files\n\n"
            "- `src/compose.ts` - normalize non-Error thrown values before onError.\n"
            "- `src/hono-base.ts` - normalize dispatch errors before the Hono error handler.\n"
            "- `src/hono.test.ts` - cover primitive and object non-Error throws.\n\n"
            "## Verification\n\n"
            "- `bunx vitest --run src/compose.test.ts src/hono.test.ts` "
            "-> exit code 0; captured summary `Test Files 2 passed (2)` and "
            "`Tests 241 passed (241)`.\n"
            "- `bunx tsc --noEmit` -> exit code 0; captured output contained no diagnostics.\n"
            "- `./node_modules/.bin/prettier --check src/utils/error.ts src/hono-base.ts` "
            "-> pass, exit code 0; all matched files use Prettier style.\n"
            "- `bun run test` -> exit code 1; captured summary "
            "`Test Files 3 failed | 141 passed (144)`, `Tests 11 failed | "
            "4314 passed | 33 skipped (4358)`, and `Errors 4 errors`.\n"
            "- `bun test` -> not-run: earlier implement evidence recorded this "
            "plain Bun runner as a sandbox-hanging command.\n\n"
            "## Risks\n\n"
            "- Broad-suite verification remains locally blocked by unrelated target "
            "runner failures; focused regression and TypeScript checks passed.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-BUN",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_rejects_plain_tool_prose_as_command_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-PLAIN-TOOLS",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-LIVE-HONO-NON-ERROR-THROW`\n\n"
            "## Summary\n\n"
            "Implemented the selected Hono task with a scoped source update and "
            "recorded verification notes.\n\n"
            "## Touched files\n\n"
            "- `src/hono-base.ts` - normalize dispatch errors before the Hono error handler.\n\n"
            "## Verification\n\n"
            "- Bun runner passed.\n"
            "- Prettier passed.\n"
            "- TypeScript tsc passed.\n\n"
            "## Risks\n\n"
            "- No residual risk remains.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-PLAIN-TOOLS",
        workspace_root=workspace_root,
    )

    assert [finding.code for finding in findings] == [
        UNVERIFIABLE_CHECK_CLAIM_CODE,
        UNVERIFIABLE_CHECK_CLAIM_CODE,
        UNVERIFIABLE_CHECK_CLAIM_CODE,
    ]
    assert all(finding.severity == "high" for finding in findings)


def test_validate_semantic_outputs_accepts_live_noop_blocker_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-BLOCKER",
        (
            "# Implementation Report\n\n"
            "## Selected task id\n\n"
            "`ISSUE-705`, decomposed into ordered tasks `T1` -> `T2` -> `T3`.\n\n"
            "## Summary\n\n"
            "This attempt executed `T1` only. The pre-write scratch reproduction "
            "observed the documented fail path, so later source-edit tasks were "
            "not started and a blocking plan question was raised.\n\n"
            "## Touched files\n\n"
            "- `sqlite_utils/cli.py` (`scratch-and-revert`, no net change): applied "
            "the guard for the T1 observation, then reverted it. Net diff is empty.\n\n"
            "## Verification\n\n"
            "- VN-1 (scratch guard observation):\n"
            "  - Command: `.venv/bin/python -c \"...\"` invoking `cli.cli` with "
            "`[\"insert\", \"--csv\", \"--detect-types\", <db>, \"data\", <csv>]`.\n"
            "  - Observed: exit code `0`, `result.stderr == \"\"`, "
            "`db[\"data\"].exists() is False`, `db.table_names() == []`.\n"
            "  - Outcome: T1 fail path confirmed; halts the task graph.\n\n"
            "- VN-3 (`insert_all` empty-iterator behaviour):\n"
            "  - Command: `.venv/bin/python -c \"...\"` calling "
            "`Database(db_path)[\"t\"].insert_all([])`.\n"
            "  - Observed: the target table does not exist after the call; "
            "`db.table_names() == []`.\n"
            "  - Outcome: the planned guard cannot satisfy the table-creation clause.\n\n"
            "- VN-4 (post-attempt source diff):\n"
            "  - Command: `git diff sqlite_utils/cli.py tests/test_cli_insert.py`.\n"
            "  - Observed: empty output.\n"
            "  - Outcome: no production-code change leaked from this attempt.\n\n"
            "- T5 full-suite run (`uv run pytest -q || pytest -q`) was not\n"
            "  executed because the bugfix was not applied and the preconditions failed.\n\n"
            "## Risks\n\n"
            "- The plan-stage table-creation expectation is now a confirmed blocker.\n\n"
            "## Follow-up\n\n"
            "- Route the blocking question to a new plan attempt before implementation.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-BLOCKER",
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


def test_validate_semantic_outputs_accepts_bounded_diff_verification_summary(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-DIFF",
        "# Implementation Report\n\n"
        "## Selected task\n\n"
        "- Task id: `TASK-LIVE-SQLITE-YIELDED-ROWS`\n"
        "- Local task ids: T1, T2\n\n"
        "## Change summary\n\n"
        "Implemented the selected yielded-rows feature with scoped code, tests, and docs.\n\n"
        "## Touched files\n\n"
        "- `sqlite_utils/cli.py` - add yielded-row ingestion handling.\n"
        "- `tests/test_cli_insert.py` - cover yielded rows and invalid input.\n"
        "- `docs/cli.rst` - document trusted local Python caveats.\n\n"
        "## Verification\n\n"
        "- `uv run pytest -q` -> 1044 passed, 16 skipped.\n"
        "- `git diff --name-only` -> changes bounded to `sqlite_utils/cli.py`, "
        "`tests/test_cli_insert.py`, `docs/cli.rst`.\n\n"
        "## Risks\n\n"
        "- None observed.\n\n"
        "## Follow-up\n\n"
        "- None.\n",
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-DIFF",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_live_cleanup_residue_note(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-LIVE-CLEANUP",
        "# Implementation Report\n\n"
        "## Selected task\n\n"
        "- Task id: `TASK-LIVE-SQLITE-YIELDED-ROWS`\n\n"
        "## Change summary\n\n"
        "Implemented the selected yielded-rows feature with code, tests, and docs.\n\n"
        "## Touched files\n\n"
        "- `sqlite_utils/cli.py` - add yielded-row ingestion handling.\n"
        "- `tests/test_cli_insert.py` - cover yielded rows and invalid input.\n"
        "- `docs/cli.rst` - document trusted local Python caveats.\n\n"
        "## Verification\n\n"
        "- `uv run pytest -q` -> pass (1055 passed, 16 skipped).\n"
        "- `uv run sphinx-build -W -b html docs docs/_build` -> pass.\n"
        "- Verification residue cleanup: removed `.pytest_cache/`, "
        "`.hypothesis/`, `docs/_build/`, and `__pycache__/` directories "
        "created by the pytest/sphinx checks.\n"
        "- `git status --ignored --short --untracked-files=all` -> pass "
        "(no `.pytest_cache/`, `.hypothesis/`, `docs/_build/`, "
        "`__pycache__/`, `.ruff_cache/`, or `.mypy_cache/` residue remains).\n\n"
        "## Risks\n\n"
        "- None observed.\n\n"
        "## Follow-up\n\n"
        "- None.\n",
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-LIVE-CLEANUP",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_backticked_python_heredoc_verification(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-HEREDOC",
        "# Implementation Report\n\n"
        "## Summary\n\n"
        "- Implemented selected task `TASK-LIVE-TYPER-BOOLEAN-HELP` with focused "
        "code, docs, and test coverage.\n\n"
        "## Touched files\n\n"
        "- `typer/core.py` - adjust plain boolean option help formatting.\n"
        "- `typer/rich_utils.py` - adjust Rich boolean option help layout.\n"
        "- `tests/test_rich_utils.py` - cover paired and false-only boolean rows.\n\n"
        "## Verification\n\n"
        "- `python - <<'PY' ... current CliRunner boolean help probe ... PY` -> "
        "pass (exit code 0; observed Rich paired and false-only rows plus plain "
        "false-only `-d, --demo`).\n"
        "- `python -m pytest tests/test_rich_utils.py -q` -> pass (10 passed).\n\n"
        "## Risks\n\n"
        "- Rich help layout is column-width dependent.\n\n"
        "## Follow-up\n\n"
        "- none\n",
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-HEREDOC",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_valid_review_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "review-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_explicit_no_review_findings(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NO-FINDINGS",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "No review findings were identified.\n\n"
            "Evidence: `implementation-report.md` records AC-1 and AC-2 coverage.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NO-FINDINGS",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_none_review_findings_bullet(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NONE-FINDINGS-BULLET",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "- none\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NONE-FINDINGS-BULLET",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_none_review_findings_with_evidence_note(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NONE-FINDINGS-EVIDENCE",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "- none\n\n"
            "Evidence: `implementation-report.md` records AC-1 coverage.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NONE-FINDINGS-EVIDENCE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_review_clean_approval_with_live_residue(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-REVIEW-LIVE-RESIDUE"
    (tmp_path / "coverage" / "raw" / "default").mkdir(parents=True)
    _write_repository_state(
        workspace_root,
        work_item,
        (
            "# Repository State\n\n"
            "## Live setup workspace baseline\n\n"
            "- Known harness config present: `aidd.example.toml`.\n"
        ),
    )
    _write_review_report(
        workspace_root,
        work_item,
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Review status: approved\n\n"
            "## Findings\n\n"
            "- none\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert any(
        finding.code == UNVERIFIABLE_CHECK_CLAIM_CODE
        and "coverage/raw/default" in finding.message
        and "after all review commands" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_accepts_review_condition_with_live_residue_finding(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-REVIEW-LIVE-RESIDUE-FINDING"
    (tmp_path / "coverage" / "raw" / "default").mkdir(parents=True)
    _write_repository_state(
        workspace_root,
        work_item,
        (
            "# Repository State\n\n"
            "## Live setup workspace baseline\n\n"
            "- Known harness config present: `aidd.example.toml`.\n"
        ),
    )
    _write_review_report(
        workspace_root,
        work_item,
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Review status: approved-with-conditions\n\n"
            "## Findings\n\n"
            "### RV-1 - ignored residue remains after review\n\n"
            "- Severity: `high`\n"
            "- Disposition: `must-fix`\n"
            "- Evidence: `coverage/raw/default` remains visible after "
            "`git status --ignored --short --untracked-files=all`.\n"
            "- Rationale: because ignored coverage residue is workspace pollution "
            "unless it is removed or selected as deliverable output.\n\n"
            "## Risks\n\n"
            "- Review is conditional on cleanup.\n\n"
            "## Required follow-up\n\n"
            "- RV-1: remove `coverage/raw/default` or document it as selected deliverable.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_review_cleanup_claim_with_live_residue(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-REVIEW-LIVE-CLEANUP-CLAIM"
    (tmp_path / "coverage" / "raw" / "default").mkdir(parents=True)
    _write_repository_state(
        workspace_root,
        work_item,
        (
            "# Repository State\n\n"
            "## Live setup workspace baseline\n\n"
            "- Known harness config present: `aidd.example.toml`.\n"
        ),
    )
    _write_review_report(
        workspace_root,
        work_item,
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Review status: approved\n\n"
            "## Findings\n\n"
            "### RV-1 - scoped implementation evidence reviewed\n\n"
            "- Severity: `low`\n"
            "- Disposition: `accepted-risk`\n"
            "- Evidence: `implementation-report.md` records focused verification.\n"
            "- Rationale: because the selected behavior is covered by targeted tests.\n\n"
            "## Risks\n\n"
            "- Cleanup passed after verification; workspace hygiene is clean.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert any(
        finding.code == UNVERIFIABLE_CHECK_CLAIM_CODE
        and "cleanup passed" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_ignores_review_residue_without_live_context(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-REVIEW-NON-LIVE-RESIDUE"
    (tmp_path / "coverage" / "raw" / "default").mkdir(parents=True)
    _write_review_report(
        workspace_root,
        work_item,
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Review status: approved\n\n"
            "## Findings\n\n"
            "- none\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_subheading_findings(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-SUBHEADINGS",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "**Status:** `approved`\n\n"
            "## Findings\n\n"
            "### REV-001 - memory residual no such table path\n\n"
            "- **Severity:** low\n"
            "- **Disposition:** accepted-risk\n"
            "- **Rationale:** the implemented guard is acceptable because it prevents the "
            "header-only memory crash without changing populated imports.\n"
            "- **Evidence:** `implementation-report.md` TL-4 and `tests/test_cli_memory.py`.\n\n"
            "### REV-002 - kwarg forwarding drift risk\n\n"
            "- **Severity:** low\n"
            "- **Disposition:** follow-up\n"
            "- **Rationale:** forwarding table creation kwargs remains reviewable because the "
            "current change preserves insert option behavior.\n"
            "- **Evidence:** `sqlite_utils/cli.py:1189-1196` and AC-2.\n\n"
            "## Risks\n\n"
            "- Low residual risk is bounded by targeted regression tests.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-SUBHEADINGS",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_review_none_severity_findings(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NONE-SEVERITY",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "### RV-1 - Patch shape matches requested scope\n\n"
            "- Severity: `none`\n"
            "- Disposition: `accepted-risk`\n"
            "- Evidence: `sqlite_utils/cli.py:1179` and AC-2.\n"
            "- Rationale: because the finding records a verified non-defect "
            "with bounded residual risk.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NONE-SEVERITY",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_does_not_infer_review_severity_from_prose(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-SEVERITY-PROSE",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "### RV-1 - Patch shape is bounded\n\n"
            "- Disposition: `accepted-risk`\n"
            "- Evidence: `sqlite_utils/cli.py:1179` and AC-2.\n"
            "- Rationale: because none of the observed checks indicate scope creep.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-SEVERITY-PROSE",
        workspace_root=workspace_root,
    )

    assert any(
        finding.code == INCOMPLETE_SECTION_CODE
        and "explicit severity" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_requires_review_finding_evidence_reference(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-NO-EVIDENCE",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "### RV-1 - Plausible but uncited claim\n\n"
            "- Severity: `low`\n"
            "- Disposition: `accepted-risk`\n"
            "- Rationale: because the implementation appears small and bounded.\n\n"
            "## Risks\n\n"
            "- No material review risk remains.\n\n"
            "## Required follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-NO-EVIDENCE",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=UNSUPPORTED_CLAIM_CODE,
            message=(
                "Finding is missing evidence reference to implementation output "
                "or acceptance criteria."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-REVIEW-NO-EVIDENCE/stages/review/review-report.md"
                ),
                line_number=7,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_compact_review_finding_severity(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-COMPACT-SEVERITY",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved-with-conditions`\n\n"
            "## Findings\n\n"
            "- `RV-1` `medium` `accepted-risk` Evidence: "
            "`implementation-report.md` records the scoped no-op boundary. "
            "Rationale: The boundary is acceptable because release-proof "
            "execution is intentionally non-destructive.\n"
            "- `RV-2` `low` `follow-up` Evidence: AC-2 and "
            "`implementation-report.md`. Rationale: Follow-up remains "
            "bounded to maintained-runtime task completion.\n\n"
            "## Risks\n\n"
            "- Medium residual release-proof risk is explicitly accepted.\n\n"
            "## Required follow-up\n\n"
            "- Re-run the maintained runtime live scenario separately.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-COMPACT-SEVERITY",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_ignores_non_disposition_must_fix_mentions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_review_report(
        workspace_root,
        "WI-SEM-REVIEW-MUST-FIX-MENTION",
        (
            "# Review Report\n\n"
            "## Verdict\n\n"
            "- Status: `approved`\n\n"
            "## Findings\n\n"
            "### RV-1 [low] [accepted-risk] Bounded flag asymmetry\n\n"
            "- Severity: `low`\n"
            "- Disposition: `accepted-risk`\n"
            "- Evidence: `sqlite_utils/cli.py:1179-1183` and AC-2.\n"
            "- Rationale: because the behaviour is bounded to the agreed "
            "scope and should remain accepted-risk rather than `must-fix`.\n\n"
            "### RV-2 [low] [follow-up] Deferred sibling site\n\n"
            "- Severity: `low`\n"
            "- Disposition: `follow-up`\n"
            "- Evidence: `sqlite_utils/cli.py:2029-2040` and AC-3.\n"
            "- Rationale: because the sibling path is documented out of scope.\n\n"
            "## Risks\n\n"
            "- No unresolved `must-fix` findings remain.\n\n"
            "## Required follow-up\n\n"
            "- Track RV-2 separately.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="review",
        work_item="WI-SEM-REVIEW-MUST-FIX-MENTION",
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
                "(critical/high/medium/low/info/none)."
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


def test_validate_semantic_outputs_accepts_qa_acceptance_coverage_checklist(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-ACCEPTANCE-COVERAGE"
    _write_acceptance_criteria(
        tmp_path,
        work_item,
        """# Acceptance Criteria

- AC-1: Regression exercises the public CLI behavior.
- AC-2: The tracked diff stays within the selected command module and tests.
""",
    )
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Quality verdict

- QA verdict: ready

## Verification summary

- Verification passed with acceptance evidence tracked by `EV-1`.

## Release recommendation

- proceed

## Evidence

- EV-1: `context/verification-output.md` reports the targeted tests passed.

## Known issues

- Known issues: none.

## Readiness

- AC-1: confirmed. Evidence: EV-1, `context/verification-output.md`.
  The public CLI regression test passed.
- AC-2: confirmed. Evidence: EV-1, `context/verification-output.md`.
  Diff review stayed within the selected files.
- Ready because each acceptance criterion has evidence and no known issue remains.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == ()


def test_validate_semantic_outputs_requires_live_ignored_residue_evidence_for_ready_qa(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-LIVE-RESIDUE"
    _write_repository_state(
        tmp_path,
        work_item,
        (
            "# Repository State\n\n"
            "## Live setup workspace baseline\n\n"
            "- Known harness config present: `aidd.example.toml`.\n"
        ),
    )
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Quality verdict

- QA verdict: ready

## Verification summary

- Authored verification passed with evidence tracked by `EV-1` and `EV-2`.

## Release recommendation

- proceed

## Evidence

- EV-1: `./node_modules/.bin/vitest --run --coverage.enabled=false src/hono.test.ts` -> pass.
- EV-2: `./node_modules/.bin/tsc --noEmit` -> pass.

## Known issues

- Known issues: none.

## Readiness

- Ready because authored verification passed and no known issue remains.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert any(
        finding.code == MISSING_EVIDENCE_REF_CODE
        and "git status --ignored --short --untracked-files=all" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_accepts_live_ignored_residue_evidence_for_ready_qa(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-LIVE-RESIDUE-CLEAN"
    _write_repository_state(
        tmp_path,
        work_item,
        (
            "# Repository State\n\n"
            "## Live setup workspace baseline\n\n"
            "- Known harness config present: `aidd.example.toml`.\n"
        ),
    )
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Quality verdict

- QA verdict: ready

## Verification summary

- Authored verification passed with evidence tracked by `EV-1`, `EV-2`, and `EV-3`.

## Release recommendation

- proceed

## Evidence

- EV-1: `./node_modules/.bin/vitest --run --coverage.enabled=false src/hono.test.ts` -> pass.
- EV-2: `./node_modules/.bin/tsc --noEmit` -> pass.
- EV-3: `git status --ignored --short --untracked-files=all` -> pass; no new
  `coverage/`, `.coverage*`, `__pycache__/`, build, dist, or dependency-cache
  residue beyond setup baseline.

## Known issues

- Known issues: none.

## Readiness

- Ready because authored verification and ignored workspace residue evidence are clean.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_qa_bundled_acceptance_coverage(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-BUNDLED-ACCEPTANCE"
    _write_acceptance_criteria(
        tmp_path,
        work_item,
        """# Acceptance Criteria

- AC-1: Regression exercises the public CLI behavior.
- AC-2: The tracked diff stays within the selected command module and tests.
- AC-3: Verification transcript captures the targeted command.
""",
    )
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Quality verdict

- QA verdict: ready

## Verification summary

- Verification passed with acceptance evidence tracked by `EV-1`.

## Release recommendation

- proceed

## Evidence

- EV-1: `context/verification-output.md` reports the targeted tests passed.

## Known issues

- Known issues: none.

## Readiness

- AC-1 through AC-3: confirmed. Evidence: EV-1.
- Ready because the authored verification passed.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Acceptance coverage must use a separate top-level bullet for "
                "`AC-1` instead of bundling multiple `AC-N` ids."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-BUNDLED-ACCEPTANCE/stages/qa/qa-report.md"
                ),
                line_number=1,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "QA report must include an acceptance coverage bullet for "
                "`AC-2` from `context/acceptance-criteria.md`."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-BUNDLED-ACCEPTANCE/stages/qa/qa-report.md"
                ),
                line_number=1,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_SECTION_CODE,
            message=(
                "Acceptance coverage must use a separate top-level bullet for "
                "`AC-3` instead of bundling multiple `AC-N` ids."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-BUNDLED-ACCEPTANCE/stages/qa/qa-report.md"
                ),
                line_number=1,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_known_issue_blocks_with_metadata(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-KNOWN-ISSUES"
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Verification summary

- Quality verdict: `ready-with-risks`.
- Verification passed with residual risks tracked by `EV-1`.

## Release recommendation

- `proceed-with-conditions`

## Evidence

- EV-1: `context/verification-output.md` reports full test pass.

## Known issues

### KI-1: sibling command remains out of scope

- Severity: `medium`.
- Disposition: `follow-up`.
- Description: sibling command remains intentionally deferred.
- Mitigation: track a follow-up before broad release.
- Ownership: platform maintainer.
- Evidence: `EV-1`, `context/verification-output.md`.

### KI-2: acceptance branch remains explicit

- Severity: `low`.
- Disposition: `accepted-risk`.
- Description: accepted branch is documented in the regression test.
- Mitigation: keep the test docstring as the change boundary.
- Ownership: QA owner.
- Evidence: `EV-1`.

## Readiness

- Ready with conditions because `EV-1` is clean and known issues have owners.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_flat_known_issue_metadata(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-FLAT-KNOWN-ISSUES"
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Verification summary

- Quality verdict: `ready-with-risks`.
- Verification passed with residual risks tracked by `EV-1`.

## Release recommendation

- `proceed-with-conditions`

## Evidence

- EV-1: `context/verification-output.md` reports full test pass.

## Known issues

- QR-1 (`medium`): release-proof lane validates operator semantics only.
- Mitigation: keep maintained-runtime live bugfix runs in nightly checks.
- Owner: platform maintainer.

## Readiness

- Ready with conditions because `EV-1` is clean and known issue ownership is explicit.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_ready_with_residual_risk_entry(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-READY-WITH-RESIDUAL-RISK"
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Verification summary

- Quality verdict: `ready`.
- Verification passed with residual risk tracked by `EV-1`.

## Release recommendation

- proceed

## Evidence

- EV-1: `context/verification-output.md` reports full test pass.

## Known issues

- Known issues: none.
- Residual risk RR-1: Severity: low. Verification is focused rather than full-suite.
  Mitigation/ownership: release operator may run the broader suite if policy requires it.

## Readiness

- Ready because `EV-1` is clean and the residual risk has low severity and owner coverage.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == (
        ValidationFinding(
            code=UNSUPPORTED_VERDICT_CODE,
            message=(
                "Verdict `ready` cannot include residual risk entries; use "
                "`ready-with-risks` or `proceed-with-conditions` for true "
                "residual risk, or move satisfied selected-boundary notes out "
                "of `Known issues`."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-READY-WITH-RESIDUAL-RISK/stages/qa/"
                    "qa-report.md"
                ),
                line_number=16,
            ),
        ),
    )


def test_validate_semantic_outputs_flags_known_issue_block_missing_severity(
    tmp_path: Path,
) -> None:
    work_item = "WI-SEM-QA-MISSING-SEVERITY"
    _write_qa_report(
        tmp_path,
        work_item,
        """# QA Report

## Verification summary

- Quality verdict: `ready-with-risks`.
- Verification passed with residual risks tracked by `EV-1`.

## Release recommendation

- `proceed-with-conditions`

## Evidence

- EV-1: `context/verification-output.md` reports full test pass.

## Known issues

### KI-1: sibling command remains out of scope

- Disposition: `follow-up`.
- Description: sibling command remains intentionally deferred.
- Mitigation: track a follow-up before broad release.
- Ownership: platform maintainer.
- Evidence: `EV-1`, `context/verification-output.md`.

## Readiness

- Ready with conditions because `EV-1` is clean and known issues have owners.
""",
    )

    findings = validate_semantic_outputs(
        stage="qa",
        work_item=work_item,
        workspace_root=tmp_path,
    )

    assert findings == (
        ValidationFinding(
            code=RISK_UNDERREPORT_CODE,
            message=(
                "Each residual risk item must include explicit severity "
                "(critical/high/medium/low)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-QA-MISSING-SEVERITY/stages/qa/qa-report.md"
                ),
                line_number=16,
            ),
        ),
    )


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

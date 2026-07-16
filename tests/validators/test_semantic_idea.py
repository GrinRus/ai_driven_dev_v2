from __future__ import annotations

from pathlib import Path

from semantic_test_support import (
    _SEMANTIC_FIXTURES_ROOT,
    _touch_contract_references,
    _write_idea_brief,
    _write_stage_contract,
)

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic import (
    INCOMPLETE_SECTION_CODE,
    PLACEHOLDER_CONTENT_CODE,
    UNSUPPORTED_CLAIM_CODE,
    validate_semantic_outputs,
)


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


from __future__ import annotations

from pathlib import Path

import pytest
from semantic_test_support import (
    _SEMANTIC_FIXTURES_ROOT,
    _write_plan_document,
)

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic import (
    INCOMPLETE_SECTION_CODE,
    validate_semantic_outputs,
)
from aidd.validators.semantic_rules.plan import PLAN_SCOPE_MISMATCH_CODE


def _scoped_plan(*, milestone: str, strategy: str) -> str:
    return (
        "# Plan\n\n"
        "## Goals\n\n"
        "- Deliver bounded composition error handling.\n\n"
        "## Out of scope\n\n"
        "- Broad framework changes.\n\n"
        "## Milestones\n\n"
        f"- M1: {milestone}\n\n"
        "## Implementation strategy\n\n"
        f"- {strategy}\n\n"
        "## Risks\n\n"
        "- R1: Behavior can drift; mitigation: run focused regression checks.\n\n"
        "## Dependencies\n\n"
        "- M1 depends on the existing composition boundary.\n\n"
        "## Verification approach\n\n"
        "- Run the authored focused checks.\n\n"
        "## Verification notes\n\n"
        "- M1: verify composition error behavior.\n"
    )


def _write_allowed_scope(workspace_root: Path, work_item: str, markdown: str) -> None:
    path = workspace_root / "workitems" / work_item / "context" / "allowed-write-scope.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


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


def test_plan_scope_rejects_live_shaped_out_of_scope_helper(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-PLAN-SCOPE-LIVE"
    _write_allowed_scope(
        workspace_root,
        work_item,
        (
            "# Allowed write scope\n\n"
            "- `src/compose.ts`\n"
            "- `src/hono-base.ts`\n"
            "- `src/compose.test.ts`\n"
            "- `src/hono.test.ts`\n"
        ),
    )
    _write_plan_document(
        workspace_root,
        work_item,
        _scoped_plan(
            milestone=(
                "Update `src/compose.ts` and create a shared helper in "
                "`src/utils/error.ts`."
            ),
            strategy="Modify `src/hono-base.ts` to consume the new helper.",
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    scope_findings = tuple(
        finding for finding in findings if finding.code == PLAN_SCOPE_MISMATCH_CODE
    )
    assert len(scope_findings) == 1
    assert scope_findings[0].severity == "high"
    assert "`src/utils/error.ts`" in scope_findings[0].message
    assert "Milestones" in scope_findings[0].message


@pytest.mark.parametrize(
    ("path", "expected_section"),
    (
        ("src2/helper.ts", "Implementation strategy"),
        ("../escape.ts", "Implementation strategy"),
        ("/tmp/absolute.ts", "Implementation strategy"),
        (r"src\\windows.ts", "Implementation strategy"),
        ("src/*.ts", "Implementation strategy"),
    ),
)
def test_plan_scope_rejects_outside_or_unsafe_strategy_paths(
    tmp_path: Path,
    path: str,
    expected_section: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-PLAN-SCOPE-BOUNDARY"
    _write_allowed_scope(
        workspace_root,
        work_item,
        "# Allowed write scope\n\n- `src`\n",
    )
    _write_plan_document(
        workspace_root,
        work_item,
        _scoped_plan(
            milestone="Update `src/compose.ts` with bounded behavior.",
            strategy=f"Create `{path}` for shared error handling.",
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    scope_findings = tuple(
        finding for finding in findings if finding.code == PLAN_SCOPE_MISMATCH_CODE
    )
    assert len(scope_findings) == 1
    assert f"`{path}`" in scope_findings[0].message
    assert expected_section in scope_findings[0].message


def test_plan_scope_accepts_allowed_writes_and_ignores_read_only_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-PLAN-SCOPE-ALLOWED"
    _write_allowed_scope(
        workspace_root,
        work_item,
        "# Allowed write scope\n\n- `src/compose.ts`\n",
    )
    _write_plan_document(
        workspace_root,
        work_item,
        _scoped_plan(
            milestone="Update `src/compose.ts` without adding another module.",
            strategy=(
                "Implement the change in `src/compose.ts`.\n"
                "  - Inspect `tests/external-fixture.ts` as read-only evidence.\n"
                "  - Command: `uv run pytest tests/external_test.py`."
            ),
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert not any(finding.code == PLAN_SCOPE_MISMATCH_CODE for finding in findings)


def test_plan_scope_is_unrestricted_when_canonical_document_is_absent(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-PLAN-SCOPE-LEGACY"
    _write_plan_document(
        workspace_root,
        work_item,
        _scoped_plan(
            milestone="Create `src/new/helper.ts` for the implementation.",
            strategy="Update `tests/new/helper.test.ts` with focused coverage.",
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert not any(finding.code == PLAN_SCOPE_MISMATCH_CODE for finding in findings)


def test_plan_scope_fails_closed_when_canonical_document_is_malformed(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-PLAN-SCOPE-MALFORMED"
    _write_allowed_scope(
        workspace_root,
        work_item,
        "# Allowed write scope\n\n- no canonical path\n",
    )
    _write_plan_document(
        workspace_root,
        work_item,
        _scoped_plan(
            milestone="Update `src/compose.ts`.",
            strategy="Implement the bounded behavior in `src/compose.ts`.",
        ),
    )

    findings = validate_semantic_outputs(
        stage="plan",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    scope_findings = tuple(
        finding for finding in findings if finding.code == PLAN_SCOPE_MISMATCH_CODE
    )
    assert len(scope_findings) == 1
    assert scope_findings[0].severity == "high"
    assert "malformed" in scope_findings[0].message

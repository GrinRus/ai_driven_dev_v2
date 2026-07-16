from __future__ import annotations

from pathlib import Path

from semantic_test_support import (
    _SEMANTIC_FIXTURES_ROOT,
    _write_plan_document,
)

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic import (
    INCOMPLETE_SECTION_CODE,
    validate_semantic_outputs,
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


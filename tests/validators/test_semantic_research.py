from __future__ import annotations

from pathlib import Path

from semantic_test_support import (
    _SEMANTIC_FIXTURES_ROOT,
    _write_research_notes,
)

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic import (
    MISSING_EVIDENCE_LINK_CODE,
    validate_semantic_outputs,
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


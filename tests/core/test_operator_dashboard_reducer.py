from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aidd.core.operator_frontend_dashboard_reducer import (
    OperatorDashboardEvidence,
    reduce_operator_dashboard_evidence,
)
from aidd.core.operator_frontend_models import (
    OperatorNextAction,
    OperatorRunArchive,
    OperatorRunLineage,
    OperatorRunSummary,
)


def _evidence(tmp_path: Path) -> OperatorDashboardEvidence:
    return OperatorDashboardEvidence(
        work_item="WI-UI",
        workspace_root=tmp_path / ".aidd",
        project_root=tmp_path,
        active_stage="idea",
        run=OperatorRunSummary(
            run_id="run-ui",
            work_item="WI-UI",
            runtime_id="generic-cli",
            adapter_id="generic-cli",
            stage_target="idea",
            workflow_stage_start="idea",
            workflow_stage_end="qa",
            created_at_utc="2026-07-16T00:00:00Z",
            updated_at_utc="2026-07-16T00:00:01Z",
            lineage=OperatorRunLineage(
                source_run_id=None,
                source_work_item_id=None,
                baseline_id=None,
                baseline_label=None,
                child_work_item_candidates=(),
            ),
            archive=OperatorRunArchive(
                archived=False,
                archived_at_utc=None,
                reason=None,
                source=None,
            ),
        ),
        stages=(),
        active_stage_view=None,
        primary_artifact=None,
        next_action=OperatorNextAction(
            action="run-stage",
            label="Run Idea",
            detail="Start the first stage.",
            stage="idea",
            enabled=True,
        ),
        blockers=(),
        first_failure=None,
        validation_findings=(),
        primary_validation_finding=None,
        recovery_actions=(),
        evidence_refs=(),
        activity=(),
        recent_artifacts=(),
        terminal_handoff=None,
    )


@pytest.mark.parametrize(
    ("action", "enabled"),
    (
        ("run-stage", True),
        ("wait-for-stage", False),
        ("inspect-validation", True),
        ("open-terminal-handoff", True),
    ),
)
def test_dashboard_reducer_is_a_pure_field_projection(
    tmp_path: Path,
    action: str,
    enabled: bool,
) -> None:
    evidence = _evidence(tmp_path)
    evidence = replace(
        evidence,
        next_action=replace(
            evidence.next_action,
            action=action,
            enabled=enabled,
        ),
    )

    view = reduce_operator_dashboard_evidence(evidence)

    assert view.work_item == evidence.work_item
    assert view.run is evidence.run
    assert view.next_action is evidence.next_action
    assert view.blockers is evidence.blockers
    assert view.terminal_handoff is evidence.terminal_handoff


def test_dashboard_reducer_has_no_io_dependencies() -> None:
    import aidd.core.operator_frontend_dashboard_reducer as reducer

    source = Path(reducer.__file__).read_text(encoding="utf-8")

    for forbidden in (
        "subprocess",
        "urllib",
        "requests",
        ".read_text(",
        ".write_text(",
        ".exists(",
        "datetime.now",
        "time.time",
    ):
        assert forbidden not in source

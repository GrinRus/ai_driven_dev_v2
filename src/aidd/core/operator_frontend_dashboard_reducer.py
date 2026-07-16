from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.core.operator_frontend_models import (
    OperatorActivityEvent,
    OperatorArtifactRef,
    OperatorBlocker,
    OperatorDashboardView,
    OperatorEvidenceRef,
    OperatorFirstFailure,
    OperatorNextAction,
    OperatorPrimaryArtifact,
    OperatorRecoveryAction,
    OperatorRunSummary,
    OperatorStageRailItem,
    OperatorStageView,
    OperatorTerminalRunHandoff,
    OperatorValidationFindingView,
)


@dataclass(frozen=True, slots=True)
class OperatorDashboardEvidence:
    work_item: str
    workspace_root: Path
    project_root: Path
    active_stage: str
    run: OperatorRunSummary
    stages: tuple[OperatorStageRailItem, ...]
    active_stage_view: OperatorStageView | None
    primary_artifact: OperatorPrimaryArtifact | None
    next_action: OperatorNextAction
    blockers: tuple[OperatorBlocker, ...]
    first_failure: OperatorFirstFailure | None
    validation_findings: tuple[OperatorValidationFindingView, ...]
    primary_validation_finding: OperatorValidationFindingView | None
    recovery_actions: tuple[OperatorRecoveryAction, ...]
    evidence_refs: tuple[OperatorEvidenceRef, ...]
    activity: tuple[OperatorActivityEvent, ...]
    recent_artifacts: tuple[OperatorArtifactRef, ...]
    terminal_handoff: OperatorTerminalRunHandoff | None


def reduce_operator_dashboard_evidence(
    evidence: OperatorDashboardEvidence,
) -> OperatorDashboardView:
    return OperatorDashboardView(
        work_item=evidence.work_item,
        workspace_root=evidence.workspace_root,
        project_root=evidence.project_root,
        active_stage=evidence.active_stage,
        run=evidence.run,
        stages=evidence.stages,
        active_stage_view=evidence.active_stage_view,
        primary_artifact=evidence.primary_artifact,
        next_action=evidence.next_action,
        blockers=evidence.blockers,
        first_failure=evidence.first_failure,
        validation_findings=evidence.validation_findings,
        primary_validation_finding=evidence.primary_validation_finding,
        recovery_actions=evidence.recovery_actions,
        evidence_refs=evidence.evidence_refs,
        activity=evidence.activity,
        recent_artifacts=evidence.recent_artifacts,
        terminal_handoff=evidence.terminal_handoff,
    )


__all__ = [
    "OperatorDashboardEvidence",
    "reduce_operator_dashboard_evidence",
]

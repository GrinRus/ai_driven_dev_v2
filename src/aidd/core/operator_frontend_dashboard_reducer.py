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
    OperatorIntentPhaseSummary,
    OperatorNextAction,
    OperatorPrimaryArtifact,
    OperatorRecoveryAction,
    OperatorRunSummary,
    OperatorStageRailItem,
    OperatorStageView,
    OperatorTerminalRunHandoff,
    OperatorValidationFindingView,
)

_INTENT_PHASES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("understand", "Understand", ("idea", "research")),
    ("decide", "Decide", ("plan", "review-spec")),
    ("deliver", "Deliver", ("tasklist", "implement")),
    ("prove", "Prove", ("review", "qa")),
)


def _intent_phase_status(
    stages: tuple[OperatorStageRailItem, ...],
    phase_stages: tuple[str, ...],
) -> str:
    stage_by_id = {getattr(item, "stage", ""): item for item in stages}
    items = [stage_by_id[stage] for stage in phase_stages if stage in stage_by_id]
    statuses = {str(getattr(item, "status", "pending")) for item in items}
    if not items:
        return "pending"
    if statuses & {"blocked", "failed", "cancelled"}:
        return "blocked"
    if statuses & {"preparing", "executing", "validating"}:
        return "active"
    if statuses and statuses <= {"succeeded"}:
        return "complete"
    if statuses - {"pending"}:
        return "ready"
    return "pending"


def _intent_phases(
    stages: tuple[OperatorStageRailItem, ...],
) -> tuple[OperatorIntentPhaseSummary, ...]:
    return tuple(
        OperatorIntentPhaseSummary(
            phase_id=phase_id,
            label=label,
            stages=phase_stages,
            status=_intent_phase_status(stages, phase_stages),
        )
        for phase_id, label, phase_stages in _INTENT_PHASES
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
        phases=_intent_phases(evidence.stages),
    )


__all__ = [
    "OperatorDashboardEvidence",
    "reduce_operator_dashboard_evidence",
]

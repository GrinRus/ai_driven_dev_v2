from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from aidd.core.operator_frontend_models import (
    OperatorBlocker,
    OperatorNextAction,
    OperatorStageRailItem,
    OperatorStageView,
)
from aidd.core.run_inspection import RunMetadataSummary
from aidd.core.state_machine import StageState


@dataclass(frozen=True, slots=True)
class OperatorNextActionContext:
    """Typed snapshot consumed by the ordered dashboard next-action rules."""

    metadata: RunMetadataSummary | None
    active_stage: str
    active_stage_view: OperatorStageView | None
    rail_by_stage: Mapping[str, OperatorStageRailItem]
    report_blockers: tuple[OperatorBlocker, ...] = ()
    stages_with_operator_requests: frozenset[str] = frozenset()


NextActionRule = Callable[[OperatorNextActionContext], OperatorNextAction | None]

_RUNNING_STAGE_STATES = frozenset(
    {
        StageState.PREPARING.value,
        StageState.EXECUTING.value,
        StageState.VALIDATING.value,
    }
)


def _choose_runtime(context: OperatorNextActionContext) -> OperatorNextAction | None:
    if context.metadata is not None:
        return None
    return OperatorNextAction(
        action="choose-runtime",
        label="Select runtime",
        detail="Choose a runtime before starting the workflow.",
        stage=None,
        enabled=False,
    )


def _stale_downstream(context: OperatorNextActionContext) -> OperatorNextAction | None:
    stale_stage = next((item for item in context.rail_by_stage.values() if item.stale), None)
    if stale_stage is None:
        return None
    return OperatorNextAction(
        action="rerun-stale-downstream",
        label="Rerun stale downstream",
        detail=stale_stage.stale_reason
        or "A remediation attempt invalidated downstream stage evidence.",
        stage=stale_stage.stage,
        enabled=True,
    )


def _rail_blocking_questions(
    context: OperatorNextActionContext,
) -> OperatorNextAction | None:
    blocked_stage = next(
        (item for item in context.rail_by_stage.values() if item.unresolved_blocking_count),
        None,
    )
    if blocked_stage is None:
        return None
    return OperatorNextAction(
        action="answer-questions",
        label=f"Answer {blocked_stage.title} questions",
        detail="Resolve blocking questions before resuming execution.",
        stage=blocked_stage.stage,
        enabled=True,
    )


def _active_stage_blocking_questions(
    context: OperatorNextActionContext,
) -> OperatorNextAction | None:
    active_stage_view = context.active_stage_view
    if active_stage_view is None or not (
        active_stage_view.questions.unresolved_blocking_question_ids
    ):
        return None
    return OperatorNextAction(
        action="answer-questions",
        label="Answer blocking questions",
        detail="Resolve stage questions before resuming execution.",
        stage=active_stage_view.result.stage,
        enabled=True,
    )


def _running_stage(context: OperatorNextActionContext) -> OperatorNextAction | None:
    running_stage = running_stage_item(context.rail_by_stage)
    if running_stage is None:
        return None
    return running_stage_next_action(running_stage)


def _failed_validation(context: OperatorNextActionContext) -> OperatorNextAction | None:
    failed_stage = next(
        (
            item
            for item in context.rail_by_stage.values()
            if item.validator_fail_count and item.status != StageState.SUCCEEDED.value
        ),
        None,
    )
    if failed_stage is None:
        return None
    if failed_stage.stage in context.stages_with_operator_requests:
        return OperatorNextAction(
            action="review-intervention",
            label="Review requested change result",
            detail=(
                "Open validation recovery for the requested change result. "
                "Request another change if repair is exhausted."
            ),
            stage=failed_stage.stage,
            enabled=True,
        )
    return OperatorNextAction(
        action="inspect-validation",
        label=f"Inspect {failed_stage.title} validation",
        detail=(
            "Open validation recovery. Run Repair if available, or Request Change "
            "if the repair budget is exhausted."
        ),
        stage=failed_stage.stage,
        enabled=True,
    )


def _active_stage_blocked(context: OperatorNextActionContext) -> OperatorNextAction | None:
    active_stage_view = context.active_stage_view
    if active_stage_view is None:
        return None
    result = active_stage_view.result
    if result.final_state != StageState.BLOCKED.value:
        return None
    return OperatorNextAction(
        action="resume-stage",
        label="Resume stage",
        detail="Answers are present; rerun the selected stage in the same run.",
        stage=result.stage,
        enabled=True,
    )


def _blocked_stage(context: OperatorNextActionContext) -> OperatorNextAction | None:
    blocked_stage = next(
        (
            item
            for item in context.rail_by_stage.values()
            if item.status == StageState.BLOCKED.value
        ),
        None,
    )
    if blocked_stage is None:
        return None
    return OperatorNextAction(
        action="resume-stage",
        label=f"Resume {blocked_stage.title}",
        detail="Answers are present; rerun the blocked stage in the same run.",
        stage=blocked_stage.stage,
        enabled=True,
    )


def _review_blocker(context: OperatorNextActionContext) -> OperatorNextAction | None:
    blocker = next(
        (
            item
            for item in context.report_blockers
            if item.kind in {"review-rejected", "review-conditions"}
        ),
        None,
    )
    if blocker is None:
        return None
    return OperatorNextAction(
        action="review-findings",
        label="Resolve review findings",
        detail=blocker.detail,
        stage="review",
        enabled=True,
    )


def _qa_blocker(context: OperatorNextActionContext) -> OperatorNextAction | None:
    blocker = next(
        (
            item
            for item in context.report_blockers
            if item.kind in {"qa-not-ready", "qa-ready-with-risks"}
        ),
        None,
    )
    if blocker is None:
        return None
    return OperatorNextAction(
        action="qa-verdict",
        label="Resolve QA verdict",
        detail=blocker.detail,
        stage="qa",
        enabled=True,
    )


def _terminal_evidence_blocker(
    context: OperatorNextActionContext,
) -> OperatorNextAction | None:
    blocker = next(
        (item for item in context.report_blockers if item.kind == "terminal-missing-evidence"),
        None,
    )
    if blocker is None:
        return None
    return OperatorNextAction(
        action="review-complete",
        label="Restore terminal evidence",
        detail=blocker.detail,
        stage="qa",
        enabled=True,
    )


def _all_stages_succeeded(context: OperatorNextActionContext) -> OperatorNextAction | None:
    if any(item.status != StageState.SUCCEEDED.value for item in context.rail_by_stage.values()):
        return None
    return OperatorNextAction(
        action="review-complete",
        label="Review final artifacts",
        detail=(
            "All canonical stages have succeeded. Inspect the QA handoff and final "
            "evidence before starting the next flow."
        ),
        stage=None,
        enabled=True,
    )


def _runnable_stage(context: OperatorNextActionContext) -> OperatorNextAction:
    runnable = next((item for item in context.rail_by_stage.values() if item.can_run), None)
    if runnable is None:
        return OperatorNextAction(
            action="run-stage",
            label="No runnable stage",
            detail="Inspect blockers before continuing.",
            stage=context.active_stage,
            enabled=False,
        )
    return OperatorNextAction(
        action="run-stage",
        label=f"Run {runnable.stage}",
        detail=runnable.reason,
        stage=runnable.stage,
        enabled=True,
    )


_RULES: tuple[NextActionRule, ...] = (
    _choose_runtime,
    _stale_downstream,
    _rail_blocking_questions,
    _active_stage_blocking_questions,
    _running_stage,
    _failed_validation,
    _active_stage_blocked,
    _blocked_stage,
    _review_blocker,
    _qa_blocker,
    _terminal_evidence_blocker,
    _all_stages_succeeded,
)


def resolve_next_action(context: OperatorNextActionContext) -> OperatorNextAction:
    """Evaluate dashboard next-action rules in their documented priority order."""

    for rule in _RULES:
        if action := rule(context):
            return action
    return _runnable_stage(context)


def running_stage_item(
    rail_by_stage: Mapping[str, OperatorStageRailItem],
) -> OperatorStageRailItem | None:
    return next(
        (item for item in rail_by_stage.values() if item.status in _RUNNING_STAGE_STATES),
        None,
    )


def running_stage_next_action(running_stage: OperatorStageRailItem) -> OperatorNextAction:
    return OperatorNextAction(
        action="wait-for-stage",
        label=f"{running_stage.title} running",
        detail="Refresh after the active stage leaves preparing, executing, or validating.",
        stage=running_stage.stage,
        enabled=False,
    )


__all__ = [
    "NextActionRule",
    "OperatorNextActionContext",
    "resolve_next_action",
    "running_stage_item",
    "running_stage_next_action",
]

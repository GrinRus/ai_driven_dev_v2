from __future__ import annotations

import json
import re
from pathlib import Path

from aidd.core.operator_frontend_artifacts import (
    _artifact_size,
    resolve_operator_artifact_document_content,
)
from aidd.core.operator_frontend_common import validate_operator_stage
from aidd.core.operator_frontend_models import (
    OperatorActivityEvent,
    OperatorApprovalCounts,
    OperatorArtifactRef,
    OperatorBlocker,
    OperatorChildWorkItemCandidate,
    OperatorDashboardView,
    OperatorEvidenceRef,
    OperatorNextAction,
    OperatorNextFlowRecommendation,
    OperatorPrimaryArtifact,
    OperatorRepairCounts,
    OperatorRunLineage,
    OperatorRunSummary,
    OperatorStageRailItem,
    OperatorStageView,
    OperatorTerminalRunHandoff,
)
from aidd.core.operator_frontend_questions import (
    resolve_operator_questions_view,
    resolve_operator_stage_view,
)
from aidd.core.operator_intervention import (
    latest_operator_intervention_request,
    list_operator_intervention_requests,
)
from aidd.core.run_inspection import (
    RunMetadataSummary,
    StageResultSummary,
    resolve_run_artifacts_summary,
    resolve_run_metadata_summary,
    resolve_stage_result_summary,
)
from aidd.core.run_lookup import latest_attempt_number
from aidd.core.run_store import (
    RUN_ATTEMPT_INPUT_BUNDLE_FILENAME,
    RUN_EVENTS_JSONL_FILENAME,
    load_stage_metadata,
    run_attempt_root,
)
from aidd.core.runtime_operator import (
    OPERATOR_DECISIONS_FILENAME,
    OPERATOR_REQUESTS_FILENAME,
    load_operator_decisions,
    load_operator_requests,
)
from aidd.core.stage_graph import StageAdvancementSummary, summarize_workflow_advancement
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState

_STAGE_UI_COPY: dict[str, tuple[str, str]] = {
    "idea": ("Idea", "Clarify the request"),
    "research": ("Research", "Gather context"),
    "plan": ("Plan", "Design the approach"),
    "review-spec": ("Review Spec", "Check the plan"),
    "tasklist": ("Tasklist", "Break down work"),
    "implement": ("Implement", "Make changes"),
    "review": ("Review", "Inspect quality"),
    "qa": ("QA", "Verify outcomes"),
}

_PRIMARY_ARTIFACT_KEYS: tuple[str, ...] = (
    "idea_brief",
    "research_notes",
    "plan",
    "review_spec_report",
    "tasklist",
    "implementation_report",
    "review_report",
    "qa_report",
    "stage_result",
    "validator_report",
    "questions",
    "input_bundle",
    "stage_brief",
    "repair_brief",
    "answers",
)
_MAX_ACTIVITY_EVENTS = 24
_MAX_RECENT_ARTIFACTS = 12
_MAX_ARTIFACT_EXCERPT_CHARS = 6000
_QA_VERDICT_PATTERN = re.compile(
    r"\b(ready-with-risks|not-ready|ready)\b",
    flags=re.IGNORECASE,
)


def _empty_run_lineage() -> OperatorRunLineage:
    return OperatorRunLineage(
        source_run_id=None,
        source_work_item_id=None,
        baseline_id=None,
        baseline_label=None,
        child_work_item_candidates=(),
    )


def _empty_run_summary(*, work_item: str) -> OperatorRunSummary:
    return OperatorRunSummary(
        run_id=None,
        work_item=work_item,
        runtime_id=None,
        adapter_id=None,
        stage_target=None,
        workflow_stage_start=None,
        workflow_stage_end=None,
        created_at_utc=None,
        updated_at_utc=None,
        lineage=_empty_run_lineage(),
    )


def _optional_manifest_stage(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if not normalized or normalized.lower() == "none":
        return None
    return normalized


def _run_summary(metadata: RunMetadataSummary) -> OperatorRunSummary:
    lineage = metadata.lineage
    return OperatorRunSummary(
        run_id=metadata.run_id,
        work_item=metadata.work_item,
        runtime_id=metadata.runtime_id,
        adapter_id=metadata.adapter_id,
        stage_target=metadata.stage_target,
        workflow_stage_start=_optional_manifest_stage(metadata.workflow_stage_start),
        workflow_stage_end=_optional_manifest_stage(metadata.workflow_stage_end),
        created_at_utc=metadata.created_at_utc,
        updated_at_utc=metadata.updated_at_utc,
        lineage=OperatorRunLineage(
            source_run_id=lineage.source_run_id,
            source_work_item_id=lineage.source_work_item_id,
            baseline_id=lineage.baseline_id,
            baseline_label=lineage.baseline_label,
            child_work_item_candidates=tuple(
                OperatorChildWorkItemCandidate(
                    work_item_id=candidate.work_item_id,
                    label=candidate.label,
                    relationship=candidate.relationship,
                    source_run_id=candidate.source_run_id,
                )
                for candidate in lineage.child_work_item_candidates
            ),
        ),
    )


def _stage_result_or_none(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None,
) -> StageResultSummary | None:
    if run_id is None:
        return None
    try:
        return resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        )
    except ValueError:
        return None


def _advancement_by_stage(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary | None,
) -> dict[str, StageAdvancementSummary]:
    if metadata is None:
        return {}
    try:
        advancement = summarize_workflow_advancement(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=metadata.run_id,
            stage_start=_optional_manifest_stage(metadata.workflow_stage_start) or STAGES[0],
            stage_end=(
                _optional_manifest_stage(metadata.workflow_stage_end)
                or metadata.stage_target
                or STAGES[-1]
            ),
        )
    except ValueError:
        return {}
    return {summary.stage: summary for summary in advancement}


def _stage_rail_items(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary | None,
) -> tuple[OperatorStageRailItem, ...]:
    metadata_by_stage = (
        {stage.stage: stage for stage in metadata.stages} if metadata is not None else {}
    )
    advancement_by_stage = _advancement_by_stage(
        workspace_root=workspace_root,
        work_item=work_item,
        metadata=metadata,
    )
    items: list[OperatorStageRailItem] = []
    for stage in STAGES:
        title, subtitle = _STAGE_UI_COPY[stage]
        metadata_summary = metadata_by_stage.get(stage)
        advancement_summary = advancement_by_stage.get(stage)
        result = _stage_result_or_none(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=metadata.run_id if metadata is not None else None,
        )
        questions = resolve_operator_questions_view(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        items.append(
            OperatorStageRailItem(
                stage=stage,
                title=title,
                subtitle=subtitle,
                status=(
                    metadata_summary.status
                    if metadata_summary is not None
                    else StageState.PENDING.value
                ),
                attempt_count=metadata_summary.attempt_count if metadata_summary else 0,
                can_run=advancement_summary.can_run if advancement_summary else stage == STAGES[0],
                reason=advancement_summary.reason if advancement_summary else "not started",
                question_count=len(questions.questions),
                unresolved_blocking_count=len(questions.unresolved_blocking_question_ids),
                validator_pass_count=result.validator_pass_count if result else 0,
                validator_fail_count=result.validator_fail_count if result else 0,
            )
        )
    return tuple(items)


def _primary_artifact(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None,
) -> OperatorPrimaryArtifact | None:
    if run_id is None:
        return None
    try:
        artifacts = resolve_run_artifacts_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        )
    except ValueError:
        return None

    key = next(
        (candidate for candidate in _PRIMARY_ARTIFACT_KEYS if candidate in artifacts.documents),
        None,
    )
    if key is None:
        return None
    try:
        content = resolve_operator_artifact_document_content(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            key=key,
            run_id=run_id,
            mode="preview",
            limit_bytes=_MAX_ARTIFACT_EXCERPT_CHARS,
        )
    except ValueError:
        return None
    excerpt = content.text[:_MAX_ARTIFACT_EXCERPT_CHARS]
    return OperatorPrimaryArtifact(
        key=content.key,
        path=content.path,
        content_type=content.content_type,
        byte_size=content.byte_size,
        excerpt=excerpt,
        truncated=content.truncated or len(content.text) > len(excerpt),
    )


def _evidence_refs(
    *,
    workspace_root: Path,
    work_item: str,
    active_stage_view: OperatorStageView | None,
    primary_artifact: OperatorPrimaryArtifact | None,
) -> tuple[OperatorEvidenceRef, ...]:
    if active_stage_view is None:
        return ()
    result = active_stage_view.result
    refs: list[OperatorEvidenceRef] = []
    if primary_artifact is not None:
        refs.append(
            OperatorEvidenceRef(
                label=primary_artifact.key,
                kind="document",
                path=primary_artifact.path,
                stage=result.stage,
            )
        )
    latest_request = latest_operator_intervention_request(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=result.stage,
    )
    if latest_request is not None:
        refs.append(
            OperatorEvidenceRef(
                label=latest_request.request_id,
                kind="operator-request",
                path=workspace_relative_path(workspace_root, latest_request.request_path),
                stage=result.stage,
            )
        )
    refs.append(
        OperatorEvidenceRef(
            label="validator-report",
            kind="document",
            path=result.validator_report_path,
            stage=result.stage,
        )
    )
    for path in result.repair_output_paths:
        refs.append(
            OperatorEvidenceRef(
                label=Path(path).name,
                kind="repair",
                path=path,
                stage=result.stage,
            )
        )
    for path in result.log_artifact_paths:
        refs.append(
            OperatorEvidenceRef(
                label=Path(path).name,
                kind="log",
                path=path,
                stage=result.stage,
            )
        )
    return tuple(refs)


def _blockers(
    *,
    active_stage: str,
    active_stage_view: OperatorStageView | None,
    rail_by_stage: dict[str, OperatorStageRailItem],
) -> tuple[OperatorBlocker, ...]:
    blockers: list[OperatorBlocker] = []
    result = active_stage_view.result if active_stage_view is not None else None
    active_result_stage = result.stage if result is not None else active_stage
    if (
        active_stage_view is not None
        and active_stage_view.questions.unresolved_blocking_question_ids
    ):
        blockers.append(
            OperatorBlocker(
                kind="questions",
                title="Blocking questions",
                detail=", ".join(active_stage_view.questions.unresolved_blocking_question_ids),
                severity="warning",
                stage=active_result_stage,
                path=(
                    "workitems/"
                    f"{active_stage_view.questions.work_item}/stages/"
                    f"{active_stage_view.questions.stage}/answers.md"
                ),
            )
        )
    if result is not None and result.validator_fail_count:
        blockers.append(
            OperatorBlocker(
                kind="validation",
                title="Validation has failures",
                detail=f"{result.validator_fail_count} failing validator result(s)",
                severity="error",
                stage=result.stage,
                path=result.validator_report_path,
            )
        )
    for rail_item in rail_by_stage.values():
        if rail_item.stage == active_result_stage:
            continue
        if rail_item.unresolved_blocking_count:
            blockers.append(
                OperatorBlocker(
                    kind="questions",
                    title=f"Blocking questions in {rail_item.title}",
                    detail=f"{rail_item.unresolved_blocking_count} unresolved blocking question(s)",
                    severity="warning",
                    stage=rail_item.stage,
                )
            )
        if (
            rail_item.validator_fail_count
            and rail_item.status != StageState.SUCCEEDED.value
        ):
            blockers.append(
                OperatorBlocker(
                    kind="validation",
                    title=f"Validation failures in {rail_item.title}",
                    detail=f"{rail_item.validator_fail_count} failing validator result(s)",
                    severity="error",
                    stage=rail_item.stage,
                )
            )
    active_rail = rail_by_stage.get(result.stage if result is not None else active_stage)
    if active_rail is not None and not active_rail.can_run:
        for prefix, kind, title in (
            ("missing prerequisites:", "missing-prerequisite", "Missing prerequisites"),
            ("blocked upstream stages:", "blocked-upstream", "Blocked upstream stage"),
            ("failed upstream stages:", "failed-upstream", "Failed upstream stage"),
        ):
            if active_rail.reason.startswith(prefix):
                blockers.append(
                    OperatorBlocker(
                        kind=kind,
                        title=title,
                        detail=active_rail.reason.removeprefix(prefix).strip(),
                        severity="warning",
                        stage=result.stage if result is not None else active_stage,
                    )
                )
    return tuple(blockers)


def _next_action(
    *,
    metadata: RunMetadataSummary | None,
    active_stage: str,
    active_stage_view: OperatorStageView | None,
    rail_by_stage: dict[str, OperatorStageRailItem],
    stages_with_operator_requests: frozenset[str] = frozenset(),
) -> OperatorNextAction:
    if metadata is None:
        return OperatorNextAction(
            action="choose-runtime",
            label="Select runtime",
            detail="Choose a runtime before starting the workflow.",
            stage=None,
            enabled=False,
        )
    blocked_question_stage = next(
        (item for item in rail_by_stage.values() if item.unresolved_blocking_count),
        None,
    )
    if blocked_question_stage is not None:
        return OperatorNextAction(
            action="answer-questions",
            label=f"Answer {blocked_question_stage.title} questions",
            detail="Resolve blocking questions before resuming execution.",
            stage=blocked_question_stage.stage,
            enabled=True,
        )
    if active_stage_view is not None and (
        active_stage_view.questions.unresolved_blocking_question_ids
    ):
        return OperatorNextAction(
            action="answer-questions",
            label="Answer blocking questions",
            detail="Resolve stage questions before resuming execution.",
            stage=active_stage_view.result.stage,
            enabled=True,
        )
    failed_validation_stage = next(
        (
            item
            for item in rail_by_stage.values()
            if item.validator_fail_count and item.status != StageState.SUCCEEDED.value
        ),
        None,
    )
    if failed_validation_stage is not None:
        if failed_validation_stage.stage in stages_with_operator_requests:
            return OperatorNextAction(
                action="review-intervention",
                label="Review requested change result",
                detail="Latest operator intervention ended with validation failures or blockers.",
                stage=failed_validation_stage.stage,
                enabled=True,
            )
        return OperatorNextAction(
            action="inspect-validation",
            label=f"Inspect {failed_validation_stage.title} validation",
            detail="Review validator output and repair evidence before continuing.",
            stage=failed_validation_stage.stage,
            enabled=True,
        )
    if active_stage_view is not None:
        result = active_stage_view.result
        if result.final_state == StageState.BLOCKED.value:
            return OperatorNextAction(
                action="resume-stage",
                label="Resume stage",
                detail="Answers are present; rerun the selected stage in the same run.",
                stage=result.stage,
                enabled=True,
            )
    blocked_stage = next(
        (item for item in rail_by_stage.values() if item.status == StageState.BLOCKED.value),
        None,
    )
    if blocked_stage is not None:
        return OperatorNextAction(
            action="resume-stage",
            label=f"Resume {blocked_stage.title}",
            detail="Answers are present; rerun the blocked stage in the same run.",
            stage=blocked_stage.stage,
            enabled=True,
        )

    incomplete = [
        item for item in rail_by_stage.values() if item.status != StageState.SUCCEEDED.value
    ]
    if not incomplete:
        return OperatorNextAction(
            action="review-complete",
            label="Review complete",
            detail="All canonical stages have succeeded.",
            stage=None,
            enabled=True,
        )

    runnable = next((item for item in rail_by_stage.values() if item.can_run), None)
    if runnable is None:
        return OperatorNextAction(
            action="run-stage",
            label="No runnable stage",
            detail="Inspect blockers before continuing.",
            stage=active_stage,
            enabled=False,
        )
    target_stage = runnable.stage
    return OperatorNextAction(
        action="run-stage",
        label=f"Run {target_stage}",
        detail=runnable.reason,
        stage=target_stage,
        enabled=True,
    )


def _stage_activity(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary,
) -> list[OperatorActivityEvent]:
    events: list[OperatorActivityEvent] = [
        OperatorActivityEvent(
            time_utc=metadata.created_at_utc,
            level="info",
            source="run",
            event="run.created",
            details=f"Run {metadata.run_id} created for {metadata.stage_target}.",
        ),
        OperatorActivityEvent(
            time_utc=metadata.updated_at_utc,
            level="info",
            source="run",
            event="run.updated",
            details=f"Run {metadata.run_id} updated.",
        ),
    ]
    for stage in STAGES:
        stage_metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=metadata.run_id,
            stage=stage,
        )
        if stage_metadata is None:
            continue
        for change in stage_metadata.status_history:
            events.append(
                OperatorActivityEvent(
                    time_utc=change.changed_at_utc,
                    level=(
                        "error"
                        if change.status == StageState.FAILED.value
                        else "warn"
                        if change.status
                        in {StageState.BLOCKED.value, StageState.REPAIR_NEEDED.value}
                        else "info"
                    ),
                    source=stage,
                    event=f"stage.{change.status}",
                    details=f"{stage} status changed to {change.status}.",
                )
            )
        for repair in stage_metadata.repair_history:
            events.append(
                OperatorActivityEvent(
                    time_utc=repair.recorded_at_utc,
                    level="warn" if "fail" in repair.outcome.lower() else "info",
                    source=stage,
                    event=f"repair.{repair.trigger}",
                    details=f"Attempt {repair.attempt_number}: {repair.outcome}.",
                )
            )
        for request in list_operator_intervention_requests(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        ):
            events.append(
                OperatorActivityEvent(
                    time_utc=request.created_at_utc,
                    level="info",
                    source=stage,
                    event="operator.request.created",
                    details=f"{request.request_id}: {request.request_text[:160]}",
                )
            )
    return events


def _latest_attempt_has_operator_request(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> bool:
    attempt_number = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_number is None:
        return False
    input_bundle_path = (
        run_attempt_root(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
        )
        / RUN_ATTEMPT_INPUT_BUNDLE_FILENAME
    )
    if not input_bundle_path.exists():
        return False
    return "/operator-requests/request-" in input_bundle_path.read_text(encoding="utf-8")


def _stages_with_latest_intervention_attempt(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str | None,
) -> frozenset[str]:
    if run_id is None:
        return frozenset()
    stages: set[str] = set()
    for stage in STAGES:
        if latest_operator_intervention_request(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        ) is not None and (
            _latest_attempt_has_operator_request(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            )
            or _current_attempt_sequence_started_by_intervention(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            )
        ):
            stages.add(stage)
    return frozenset(stages)


def _current_attempt_sequence_started_by_intervention(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> bool:
    attempt_number = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_number is None:
        return False
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if metadata is None or not metadata.repair_history:
        return False

    history = tuple(
        sorted(
            metadata.repair_history,
            key=lambda entry: (entry.attempt_number, entry.recorded_at_utc),
        )
    )
    latest_recorded_attempt = max(entry.attempt_number for entry in history)
    if latest_recorded_attempt < max(1, attempt_number - 1):
        return False

    sequence_start = next(
        (
            entry
            for entry in reversed(history)
            if entry.attempt_number <= attempt_number and entry.trigger != "repair"
        ),
        None,
    )
    return sequence_start is not None and sequence_start.trigger == "intervention"


def _runtime_events_activity(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> list[OperatorActivityEvent]:
    attempt_number = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_number is None:
        return []
    events_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    ) / RUN_EVENTS_JSONL_FILENAME
    if not events_path.exists():
        return []

    events: list[OperatorActivityEvent] = []
    for line_number, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        event_name = str(
            payload.get("type")
            or payload.get("event")
            or payload.get("message_type")
            or f"runtime.event.{line_number}"
        )
        details = str(payload.get("message") or payload.get("text") or payload)[:240]
        events.append(
            OperatorActivityEvent(
                time_utc=str(payload.get("timestamp") or payload.get("time") or ""),
                level=str(payload.get("level") or "info").lower(),
                source=str(payload.get("source") or "runtime"),
                event=event_name,
                details=details,
            )
        )
    return events


def _recent_activity(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary | None,
) -> tuple[OperatorActivityEvent, ...]:
    if metadata is None:
        return ()
    events = _stage_activity(
        workspace_root=workspace_root,
        work_item=work_item,
        metadata=metadata,
    )
    for stage_summary in metadata.stages:
        if stage_summary.attempt_count <= 0:
            continue
        events.extend(
            _runtime_events_activity(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=metadata.run_id,
                stage=stage_summary.stage,
            )
        )
    return tuple(
        sorted(events, key=lambda event: event.time_utc or "", reverse=True)[
            :_MAX_ACTIVITY_EVENTS
        ]
    )


def _recent_artifacts(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary | None,
) -> tuple[OperatorArtifactRef, ...]:
    if metadata is None:
        return ()
    refs: list[OperatorArtifactRef] = []
    for stage_summary in metadata.stages:
        if stage_summary.attempt_count <= 0:
            continue
        try:
            artifacts = resolve_run_artifacts_summary(
                workspace_root=workspace_root,
                work_item=work_item,
                stage=stage_summary.stage,
                run_id=metadata.run_id,
            )
        except ValueError:
            continue
        for kind, entries in (("document", artifacts.documents), ("log", artifacts.logs)):
            for key, path in entries.items():
                byte_size = _artifact_size(
                    workspace_root=workspace_root,
                    relative_path=path,
                )
                if byte_size is None:
                    continue
                refs.append(
                    OperatorArtifactRef(
                        stage=stage_summary.stage,
                        key=key,
                        kind=kind,
                        path=path,
                        byte_size=byte_size,
                        updated_at_utc=stage_summary.updated_at_utc,
                    )
                )
        for request in list_operator_intervention_requests(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage_summary.stage,
        ):
            relative_path = workspace_relative_path(workspace_root, request.request_path)
            byte_size = _artifact_size(
                workspace_root=workspace_root,
                relative_path=relative_path,
            )
            if byte_size is None:
                continue
            refs.append(
                OperatorArtifactRef(
                    stage=stage_summary.stage,
                    key="operator_request",
                    kind="operator-request",
                    path=relative_path,
                    byte_size=byte_size,
                    updated_at_utc=request.created_at_utc,
                )
            )
    return tuple(
        sorted(refs, key=lambda ref: ref.updated_at_utc or "", reverse=True)[
            :_MAX_RECENT_ARTIFACTS
        ]
    )


def _read_qa_verdict(*, workspace_root: Path, work_item: str) -> str | None:
    qa_report = workspace_root / "workitems" / work_item / "stages" / "qa" / "qa-report.md"
    if not qa_report.exists():
        return None
    matched = _QA_VERDICT_PATTERN.search(
        qa_report.read_text(encoding="utf-8", errors="replace")
    )
    return matched.group(1).lower() if matched is not None else None


def _terminal_handoff_status(*, qa_stage_state: str, final_qa_status: str) -> str:
    if qa_stage_state == StageState.SUCCEEDED.value:
        if final_qa_status == "ready-with-risks":
            return "completed-with-warning"
        return "completed"
    return qa_stage_state


def _terminal_final_artifacts(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary,
) -> tuple[OperatorArtifactRef, ...]:
    try:
        artifacts = resolve_run_artifacts_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage="qa",
            run_id=metadata.run_id,
        )
    except ValueError:
        return ()

    updated_at_utc = next(
        (
            stage_summary.updated_at_utc
            for stage_summary in metadata.stages
            if stage_summary.stage == "qa"
        ),
        metadata.updated_at_utc,
    )
    refs: list[OperatorArtifactRef] = []
    for kind, entries in (("document", artifacts.documents), ("log", artifacts.logs)):
        for key, path in entries.items():
            byte_size = _artifact_size(
                workspace_root=workspace_root,
                relative_path=path,
            )
            if byte_size is None:
                continue
            refs.append(
                OperatorArtifactRef(
                    stage="qa",
                    key=key,
                    kind=kind,
                    path=path,
                    byte_size=byte_size,
                    updated_at_utc=updated_at_utc,
                )
            )
    return tuple(sorted(refs, key=lambda ref: (ref.kind, ref.key, ref.path)))


def _terminal_repair_counts(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary,
) -> OperatorRepairCounts:
    attempts = 0
    succeeded = 0
    failed = 0
    for stage in STAGES:
        stage_metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=metadata.run_id,
            stage=stage,
        )
        if stage_metadata is None:
            continue
        for entry in stage_metadata.repair_history:
            if entry.trigger != "repair":
                continue
            attempts += 1
            outcome = entry.outcome.lower()
            if "fail" in outcome or "block" in outcome:
                failed += 1
            elif "pass" in outcome or "succeed" in outcome:
                succeeded += 1
    return OperatorRepairCounts(attempts=attempts, succeeded=succeeded, failed=failed)


def _terminal_approval_counts(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary,
) -> OperatorApprovalCounts:
    requested = 0
    approved = 0
    denied = 0
    cancelled = 0
    pending = 0
    for stage_summary in metadata.stages:
        for attempt_number in range(1, stage_summary.attempt_count + 1):
            attempt_path = run_attempt_root(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=metadata.run_id,
                stage=stage_summary.stage,
                attempt_number=attempt_number,
            )
            requests = load_operator_requests(attempt_path / OPERATOR_REQUESTS_FILENAME)
            decisions = load_operator_decisions(attempt_path / OPERATOR_DECISIONS_FILENAME)
            decisions_by_request_id = {decision.request_id: decision for decision in decisions}
            requested += len(requests)
            for request in requests:
                decision = decisions_by_request_id.get(request.id)
                if decision is None:
                    pending += 1
                elif decision.is_approval:
                    approved += 1
                elif decision.action.value == "deny":
                    denied += 1
                elif decision.action.value == "cancel":
                    cancelled += 1
    return OperatorApprovalCounts(
        requested=requested,
        approved=approved,
        denied=denied,
        cancelled=cancelled,
        pending=pending,
    )


def _terminal_question_counts(
    *,
    workspace_root: Path,
    work_item: str,
) -> tuple[int, int]:
    answered = 0
    total = 0
    for stage in STAGES:
        questions = resolve_operator_questions_view(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        )
        total += len(questions.questions)
        answered += sum(1 for question in questions.questions if question.status == "resolved")
    return answered, total


def _next_flow_recommendations(
    *,
    status: str,
    runtime_id: str,
) -> tuple[OperatorNextFlowRecommendation, ...]:
    if status == "completed":
        follow_up_detail = "Create a scoped follow-up only when the operator selects new work."
    else:
        follow_up_detail = "Create a scoped follow-up from QA findings, blockers, or manual notes."
    return (
        OperatorNextFlowRecommendation(
            action="create-new-work-item",
            label="Create New Work Item",
            detail="Start unrelated work without inheriting completed-run context.",
            enabled=True,
        ),
        OperatorNextFlowRecommendation(
            action="start-follow-up-flow",
            label="Start Follow-up Flow",
            detail=follow_up_detail,
            enabled=True,
        ),
        OperatorNextFlowRecommendation(
            action="clone-flow",
            label="Clone This Flow",
            detail=f"Reuse runtime `{runtime_id}` and configuration in a new run identity.",
            enabled=True,
        ),
        OperatorNextFlowRecommendation(
            action="run-eval-batch",
            label="Run Eval / Scenario Batch",
            detail="Use completed-run evidence for comparison without mutating the source run.",
            enabled=True,
        ),
        OperatorNextFlowRecommendation(
            action="archive-run",
            label="Archive Run",
            detail="Close the run for navigation while preserving read-only artifacts.",
            enabled=True,
        ),
    )


def _terminal_handoff(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary | None,
    blockers: tuple[OperatorBlocker, ...],
) -> OperatorTerminalRunHandoff | None:
    if metadata is None:
        return None
    terminal_stage = _optional_manifest_stage(metadata.workflow_stage_end) or metadata.stage_target
    if terminal_stage != "qa":
        return None
    try:
        qa_result = resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage="qa",
            run_id=metadata.run_id,
        )
    except ValueError:
        return None
    if qa_result.final_state not in {
        StageState.SUCCEEDED.value,
        StageState.FAILED.value,
        StageState.BLOCKED.value,
    }:
        return None

    final_qa_status = (
        _read_qa_verdict(workspace_root=workspace_root, work_item=work_item)
        or qa_result.final_state
    )
    handoff_status = _terminal_handoff_status(
        qa_stage_state=qa_result.final_state,
        final_qa_status=final_qa_status,
    )
    questions_answered, questions_total = _terminal_question_counts(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    return OperatorTerminalRunHandoff(
        status=handoff_status,
        final_qa_status=final_qa_status,
        qa_stage_state=qa_result.final_state,
        final_artifacts=_terminal_final_artifacts(
            workspace_root=workspace_root,
            work_item=work_item,
            metadata=metadata,
        ),
        blockers=blockers,
        repair_counts=_terminal_repair_counts(
            workspace_root=workspace_root,
            work_item=work_item,
            metadata=metadata,
        ),
        approval_counts=_terminal_approval_counts(
            workspace_root=workspace_root,
            work_item=work_item,
            metadata=metadata,
        ),
        questions_answered_count=questions_answered,
        questions_total_count=questions_total,
        recommended_next_flow_actions=_next_flow_recommendations(
            status=handoff_status,
            runtime_id=metadata.runtime_id,
        ),
    )


def resolve_operator_dashboard_view(
    *,
    workspace_root: Path,
    work_item: str,
    active_stage: str = STAGES[0],
    run_id: str | None = None,
    project_root: Path | None = None,
) -> OperatorDashboardView:
    validate_operator_stage(active_stage)
    selected_project_root = (
        project_root.resolve(strict=False) if project_root is not None else Path.cwd()
    )
    try:
        metadata: RunMetadataSummary | None = resolve_run_metadata_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        )
    except ValueError as exc:
        if not str(exc).startswith("No runs found for work item "):
            raise
        metadata = None

    active_stage_view: OperatorStageView | None = None
    if metadata is not None:
        try:
            active_stage_view = resolve_operator_stage_view(
                workspace_root=workspace_root,
                work_item=work_item,
                stage=active_stage,
                run_id=metadata.run_id,
            )
        except ValueError:
            active_stage_view = None

    stages = _stage_rail_items(
        workspace_root=workspace_root,
        work_item=work_item,
        metadata=metadata,
    )
    rail_by_stage = {stage.stage: stage for stage in stages}
    primary_artifact = _primary_artifact(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=active_stage,
        run_id=metadata.run_id if metadata is not None else None,
    )
    stages_with_operator_requests = _stages_with_latest_intervention_attempt(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=metadata.run_id if metadata is not None else None,
    )
    blockers = _blockers(
        active_stage=active_stage,
        active_stage_view=active_stage_view,
        rail_by_stage=rail_by_stage,
    )
    return OperatorDashboardView(
        work_item=work_item,
        workspace_root=workspace_root,
        project_root=selected_project_root,
        active_stage=active_stage,
        run=_run_summary(metadata) if metadata else _empty_run_summary(work_item=work_item),
        stages=stages,
        active_stage_view=active_stage_view,
        primary_artifact=primary_artifact,
        next_action=_next_action(
            metadata=metadata,
            active_stage=active_stage,
            active_stage_view=active_stage_view,
            rail_by_stage=rail_by_stage,
            stages_with_operator_requests=stages_with_operator_requests,
        ),
        blockers=blockers,
        evidence_refs=_evidence_refs(
            workspace_root=workspace_root,
            work_item=work_item,
            active_stage_view=active_stage_view,
            primary_artifact=primary_artifact,
        ),
        activity=_recent_activity(
            workspace_root=workspace_root,
            work_item=work_item,
            metadata=metadata,
        ),
        recent_artifacts=_recent_artifacts(
            workspace_root=workspace_root,
            work_item=work_item,
            metadata=metadata,
        ),
        terminal_handoff=_terminal_handoff(
            workspace_root=workspace_root,
            work_item=work_item,
            metadata=metadata,
            blockers=blockers,
        ),
    )

__all__ = ["resolve_operator_dashboard_view"]

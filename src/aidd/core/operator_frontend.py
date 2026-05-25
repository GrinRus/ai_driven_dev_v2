from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from aidd.core.interview import (
    AnswerResolution,
    InterviewAnswer,
    QuestionPolicy,
    load_answers_document,
    load_questions_document,
    persist_answers_document,
    resolved_question_ids,
    unresolved_blocking_questions,
)
from aidd.core.operator_intervention import (
    latest_operator_intervention_request,
    list_operator_intervention_requests,
)
from aidd.core.run_inspection import (
    RunArtifactDocumentContent,
    RunArtifactsSummary,
    RunLogSummary,
    RunMetadataSummary,
    StageResultSummary,
    resolve_run_artifact_document_content,
    resolve_run_artifacts_summary,
    resolve_run_log_summary,
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
from aidd.core.stage_graph import StageAdvancementSummary, summarize_workflow_advancement
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stages import STAGES, is_valid_stage
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


@dataclass(frozen=True, slots=True)
class OperatorQuestionView:
    question_id: str
    text: str
    policy: QuestionPolicy
    status: str


@dataclass(frozen=True, slots=True)
class OperatorQuestionsView:
    work_item: str
    stage: str
    answers_path: Path
    questions: tuple[OperatorQuestionView, ...]
    unresolved_blocking_question_ids: tuple[str, ...]

    @property
    def has_unresolved_blocking_questions(self) -> bool:
        return bool(self.unresolved_blocking_question_ids)


@dataclass(frozen=True, slots=True)
class OperatorRunView:
    metadata: RunMetadataSummary


@dataclass(frozen=True, slots=True)
class OperatorStageView:
    result: StageResultSummary
    questions: OperatorQuestionsView


@dataclass(frozen=True, slots=True)
class OperatorRunSummary:
    run_id: str | None
    work_item: str
    runtime_id: str | None
    adapter_id: str | None
    stage_target: str | None
    workflow_stage_start: str | None
    workflow_stage_end: str | None
    created_at_utc: str | None
    updated_at_utc: str | None


@dataclass(frozen=True, slots=True)
class OperatorStageRailItem:
    stage: str
    title: str
    subtitle: str
    status: str
    attempt_count: int
    can_run: bool
    reason: str
    question_count: int
    unresolved_blocking_count: int
    validator_pass_count: int
    validator_fail_count: int


@dataclass(frozen=True, slots=True)
class OperatorNextAction:
    action: str
    label: str
    detail: str
    stage: str | None
    enabled: bool


@dataclass(frozen=True, slots=True)
class OperatorBlocker:
    kind: str
    title: str
    detail: str
    severity: str
    stage: str | None = None
    path: str | None = None


@dataclass(frozen=True, slots=True)
class OperatorEvidenceRef:
    label: str
    kind: str
    path: str
    stage: str | None = None


@dataclass(frozen=True, slots=True)
class OperatorActivityEvent:
    time_utc: str
    level: str
    source: str
    event: str
    details: str


@dataclass(frozen=True, slots=True)
class OperatorArtifactRef:
    stage: str
    key: str
    kind: str
    path: str
    byte_size: int | None
    updated_at_utc: str | None


@dataclass(frozen=True, slots=True)
class OperatorPrimaryArtifact:
    key: str
    path: str
    content_type: str
    byte_size: int
    excerpt: str
    truncated: bool


@dataclass(frozen=True, slots=True)
class OperatorDashboardView:
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
    evidence_refs: tuple[OperatorEvidenceRef, ...]
    activity: tuple[OperatorActivityEvent, ...]
    recent_artifacts: tuple[OperatorArtifactRef, ...]


def _validate_stage(stage: str) -> None:
    if not is_valid_stage(stage):
        raise ValueError(f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}.")


def _answers_path(*, workspace_root: Path, work_item: str, stage: str) -> Path:
    return workspace_root / "workitems" / work_item / "stages" / stage / "answers.md"


def resolve_operator_run_view(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str | None = None,
) -> OperatorRunView:
    return OperatorRunView(
        metadata=resolve_run_metadata_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
        )
    )


def resolve_operator_run_log_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunLogSummary:
    _validate_stage(stage)
    return resolve_run_log_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        attempt_number=attempt_number,
    )


def resolve_operator_artifacts_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunArtifactsSummary:
    _validate_stage(stage)
    return resolve_run_artifacts_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        attempt_number=attempt_number,
    )


def resolve_operator_artifact_document_content(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    key: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunArtifactDocumentContent:
    _validate_stage(stage)
    return resolve_run_artifact_document_content(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        key=key,
        run_id=run_id,
        attempt_number=attempt_number,
    )


def resolve_operator_questions_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
) -> OperatorQuestionsView:
    _validate_stage(stage)
    questions = load_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    answers = load_answers_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    resolved_ids = set(resolved_question_ids(answers=answers))
    question_views: list[OperatorQuestionView] = []
    for question in questions:
        if question.question_id in resolved_ids:
            status = "resolved"
        elif question.policy is QuestionPolicy.BLOCKING:
            status = "pending-blocking"
        else:
            status = "pending-non-blocking"
        question_views.append(
            OperatorQuestionView(
                question_id=question.question_id,
                text=question.text,
                policy=question.policy,
                status=status,
            )
        )

    unresolved = unresolved_blocking_questions(
        questions=questions,
        resolved_question_ids=resolved_ids,
    )
    return OperatorQuestionsView(
        work_item=work_item,
        stage=stage,
        answers_path=_answers_path(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        ),
        questions=tuple(question_views),
        unresolved_blocking_question_ids=tuple(
            question.question_id for question in unresolved
        ),
    )


def resolve_operator_stage_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
) -> OperatorStageView:
    _validate_stage(stage)
    return OperatorStageView(
        result=resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        ),
        questions=resolve_operator_questions_view(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
        ),
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
    )


def _optional_manifest_stage(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if not normalized or normalized.lower() == "none":
        return None
    return normalized


def _run_summary(metadata: RunMetadataSummary) -> OperatorRunSummary:
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


def _safe_relative_path(workspace_root: Path, relative_path: str) -> Path | None:
    relative = Path(relative_path)
    if relative.is_absolute():
        return None
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = (workspace_root / relative).resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_workspace):
        return None
    return resolved_path


def _artifact_size(*, workspace_root: Path, relative_path: str) -> int | None:
    path = _safe_relative_path(workspace_root, relative_path)
    if path is None or not path.exists():
        return None
    return path.stat().st_size


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
        content = resolve_run_artifact_document_content(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            key=key,
            run_id=run_id,
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
        truncated=len(content.text) > len(excerpt),
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


def resolve_operator_dashboard_view(
    *,
    workspace_root: Path,
    work_item: str,
    active_stage: str = STAGES[0],
    run_id: str | None = None,
    project_root: Path | None = None,
) -> OperatorDashboardView:
    _validate_stage(active_stage)
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
        blockers=_blockers(
            active_stage=active_stage,
            active_stage_view=active_stage_view,
            rail_by_stage=rail_by_stage,
        ),
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
    )


def persist_operator_answer(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    question_id: str,
    text: str,
    resolution: AnswerResolution = AnswerResolution.RESOLVED,
) -> OperatorQuestionsView:
    _validate_stage(stage)
    questions = load_questions_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    question_ids = {question.question_id for question in questions}
    if question_id not in question_ids:
        raise ValueError(
            f"Question id `{question_id}` does not exist for work item "
            f"`{work_item}` stage `{stage}`."
        )

    persist_answers_document(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        incoming_answers=(
            InterviewAnswer(
                question_id=question_id,
                text=text,
                resolution=resolution,
            ),
        ),
    )
    return resolve_operator_questions_view(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )

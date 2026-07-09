from __future__ import annotations

import json
import re
from pathlib import Path

from aidd.core.operator_frontend_artifacts import (
    _artifact_size,
    operator_artifact_category,
    operator_artifact_is_canonical,
    operator_artifact_safe_key,
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
    OperatorFirstFailure,
    OperatorNextAction,
    OperatorNextFlowRecommendation,
    OperatorPrimaryArtifact,
    OperatorRecoveryAction,
    OperatorRepairCounts,
    OperatorRepairHighlight,
    OperatorRunArchive,
    OperatorRunLineage,
    OperatorRunSummary,
    OperatorStageRailItem,
    OperatorStageView,
    OperatorTerminalRunHandoff,
    OperatorValidationFindingView,
)
from aidd.core.operator_frontend_questions import (
    resolve_operator_questions_view,
    resolve_operator_stage_view,
)
from aidd.core.operator_frontend_validation import load_validator_report_findings
from aidd.core.operator_intervention import (
    latest_operator_intervention_request,
    list_operator_intervention_requests,
)
from aidd.core.remediation import RemediationStaleStage, load_remediation_status
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
    RUN_RUNTIME_EXIT_METADATA_FILENAME,
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
from aidd.core.workspace import work_item_metadata_path

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
_REVIEW_APPROVAL_PATTERN = re.compile(
    r"\b(approved-with-conditions|approved|rejected)\b",
    flags=re.IGNORECASE,
)
_RUNNING_STAGE_STATES = frozenset(
    {
        StageState.PREPARING.value,
        StageState.EXECUTING.value,
        StageState.VALIDATING.value,
    }
)
_RUNTIME_FAILURE_KINDS = frozenset(
    {
        "cancelled",
        "failed",
        "non_zero_exit",
        "non-zero-exit",
        "provider_error",
        "provider-no-progress",
        "runtime-error",
        "runtime-exit-metadata-invalid",
        "runtime-failure",
        "stage-failed",
        "timeout",
    }
)
_MAX_TERMINAL_REPAIR_HIGHLIGHTS = 3
_MAX_REPAIR_REASON_CHARS = 220
_TERMINAL_REQUIRED_EVIDENCE: tuple[tuple[str, str, str], ...] = (
    ("runtime_log", "Runtime log", "raw runtime output"),
    ("qa_report", "QA report", "final QA readiness"),
    ("validator_report", "Validator report", "terminal validation result"),
    ("stage_result", "Stage result", "terminal stage summary"),
)


def _empty_run_lineage() -> OperatorRunLineage:
    return OperatorRunLineage(
        source_run_id=None,
        source_work_item_id=None,
        baseline_id=None,
        baseline_label=None,
        child_work_item_candidates=(),
    )


def _empty_run_archive() -> OperatorRunArchive:
    return OperatorRunArchive(
        archived=False,
        archived_at_utc=None,
        reason=None,
        source=None,
    )


def _lineage_value(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _child_work_item_candidates(
    lineage: dict[str, object],
) -> tuple[OperatorChildWorkItemCandidate, ...]:
    raw_candidates = lineage.get("child_work_item_candidates")
    if not isinstance(raw_candidates, list):
        return ()
    candidates: list[OperatorChildWorkItemCandidate] = []
    for candidate in raw_candidates:
        if not isinstance(candidate, dict):
            continue
        work_item_id = _lineage_value(candidate, "work_item_id")
        if work_item_id is None:
            continue
        candidates.append(
            OperatorChildWorkItemCandidate(
                work_item_id=work_item_id,
                label=_lineage_value(candidate, "label"),
                relationship=_lineage_value(candidate, "relationship"),
                source_run_id=_lineage_value(candidate, "source_run_id"),
            )
        )
    return tuple(candidates)


def _work_item_lineage(
    *,
    workspace_root: Path,
    work_item: str,
) -> OperatorRunLineage:
    metadata_path = work_item_metadata_path(root=workspace_root, work_item=work_item)
    if not metadata_path.exists():
        return _empty_run_lineage()
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _empty_run_lineage()
    if not isinstance(payload, dict):
        return _empty_run_lineage()
    lineage = payload.get("lineage")
    if not isinstance(lineage, dict):
        return _empty_run_lineage()
    return OperatorRunLineage(
        source_run_id=_lineage_value(lineage, "source_run_id"),
        source_work_item_id=_lineage_value(lineage, "source_work_item_id"),
        baseline_id=_lineage_value(lineage, "baseline_id"),
        baseline_label=_lineage_value(lineage, "baseline_label"),
        child_work_item_candidates=_child_work_item_candidates(lineage),
    )


def _empty_run_summary(*, workspace_root: Path, work_item: str) -> OperatorRunSummary:
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
        lineage=_work_item_lineage(workspace_root=workspace_root, work_item=work_item),
        archive=_empty_run_archive(),
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
        archive=OperatorRunArchive(
            archived=metadata.archive.archived,
            archived_at_utc=metadata.archive.archived_at_utc,
            reason=metadata.archive.reason,
            source=metadata.archive.source,
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


def _validation_findings_for_stage(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None,
) -> tuple[OperatorValidationFindingView, ...]:
    result = _stage_result_or_none(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
    )
    if result is None:
        return ()
    return load_validator_report_findings(
        workspace_root=workspace_root,
        validator_report_path=result.validator_report_path,
    )


def _primary_validation_finding_for_stage(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None,
) -> OperatorValidationFindingView | None:
    findings = _validation_findings_for_stage(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
    )
    return findings[0] if findings else None


def _validation_finding_detail(finding: OperatorValidationFindingView) -> str:
    location = finding.path or "unknown location"
    if finding.line_number is not None:
        location = f"{location}:{finding.line_number}"
    return f"{finding.code} in {location}: {finding.message}"


def _advancement_by_stage(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary | None,
) -> dict[str, StageAdvancementSummary]:
    if metadata is None:
        return {}
    try:
        workflow_stage_end = _optional_manifest_stage(metadata.workflow_stage_end)
        advancement = summarize_workflow_advancement(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=metadata.run_id,
            stage_start=_optional_manifest_stage(metadata.workflow_stage_start) or STAGES[0],
            stage_end=workflow_stage_end or STAGES[-1],
        )
    except ValueError:
        return {}
    return {summary.stage: summary for summary in advancement}


def _stage_rail_items(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary | None,
    stale_by_stage: dict[str, RemediationStaleStage] | None = None,
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
    stale_lookup = stale_by_stage or {}
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
        stale_entry = stale_lookup.get(stage)
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
                stale=stale_entry is not None,
                stale_reason=stale_entry.reason if stale_entry is not None else None,
                stale_invalidated_by=(
                    stale_entry.invalidated_by if stale_entry is not None else None
                ),
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
    workspace_root: Path,
    work_item: str,
    run_id: str | None,
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
    if (
        active_stage_view is not None
        and result is not None
        and result.validator_fail_count
    ):
        finding = active_stage_view.diagnostics.validation.primary_validation_finding
        detail = (
            _validation_finding_detail(finding)
            if finding is not None
            else f"{result.validator_fail_count} failing validator result(s)"
        )
        blockers.append(
            OperatorBlocker(
                kind="validation",
                title="Validation has failures",
                detail=detail,
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
            finding = _primary_validation_finding_for_stage(
                workspace_root=workspace_root,
                work_item=work_item,
                stage=rail_item.stage,
                run_id=run_id,
            )
            detail = (
                _validation_finding_detail(finding)
                if finding is not None
                else f"{rail_item.validator_fail_count} failing validator result(s)"
            )
            blockers.append(
                OperatorBlocker(
                    kind="validation",
                    title=f"Validation failures in {rail_item.title}",
                    detail=detail,
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
            ("missing required inputs:", "missing-input", "Missing required input"),
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


def _read_review_approval_status(*, workspace_root: Path, work_item: str) -> str | None:
    review_report = workspace_root / "workitems" / work_item / "stages" / "review" / (
        "review-report.md"
    )
    if not review_report.exists():
        return None
    matched = _REVIEW_APPROVAL_PATTERN.search(
        review_report.read_text(encoding="utf-8", errors="replace")
    )
    return matched.group(1).lower() if matched is not None else None


def _structured_report_blockers(
    *,
    workspace_root: Path,
    work_item: str,
    rail_by_stage: dict[str, OperatorStageRailItem],
) -> tuple[OperatorBlocker, ...]:
    blockers: list[OperatorBlocker] = []
    review = rail_by_stage.get("review")
    if review is not None and review.status == StageState.SUCCEEDED.value:
        approval_status = _read_review_approval_status(
            workspace_root=workspace_root,
            work_item=work_item,
        )
        if approval_status == "rejected":
            blockers.append(
                OperatorBlocker(
                    kind="review-rejected",
                    title="Review rejected",
                    detail=(
                        "review-report.md rejected the implementation. Send selected "
                        "findings back to implement before treating the run as complete."
                    ),
                    severity="error",
                    stage="review",
                )
            )
        elif approval_status == "approved-with-conditions":
            blockers.append(
                OperatorBlocker(
                    kind="review-conditions",
                    title="Review approved with conditions",
                    detail=(
                        "review-report.md requires an explicit operator decision before "
                        "the QA handoff is considered clean."
                    ),
                    severity="warning",
                    stage="review",
                )
            )

    qa = rail_by_stage.get("qa")
    if qa is not None and qa.status == StageState.SUCCEEDED.value:
        qa_verdict = _read_qa_verdict(workspace_root=workspace_root, work_item=work_item)
        if qa_verdict == "not-ready":
            blockers.append(
                OperatorBlocker(
                    kind="qa-not-ready",
                    title="QA not ready",
                    detail=(
                        "qa-report.md is not ready. Send selected risks or issues back "
                        "to implement, or start a follow-up instead of completing the run."
                    ),
                    severity="error",
                    stage="qa",
                )
            )
        elif qa_verdict == "ready-with-risks":
            blockers.append(
                OperatorBlocker(
                    kind="qa-ready-with-risks",
                    title="QA ready with risks",
                    detail=(
                        "qa-report.md is ready with risks. The operator must explicitly "
                        "accept risk or start a follow-up."
                    ),
                    severity="warning",
                    stage="qa",
                )
            )
    return tuple(blockers)


def _missing_terminal_evidence_labels(
    final_artifacts: tuple[OperatorArtifactRef, ...],
) -> tuple[str, ...]:
    available = {artifact.key for artifact in final_artifacts}
    return tuple(
        label for key, label, _detail in _TERMINAL_REQUIRED_EVIDENCE if key not in available
    )


def _terminal_missing_evidence_blockers(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary | None,
    stale_by_stage: dict[str, RemediationStaleStage],
) -> tuple[OperatorBlocker, ...]:
    if metadata is None or "qa" in stale_by_stage:
        return ()
    terminal_stage = _optional_manifest_stage(metadata.workflow_stage_end)
    if terminal_stage is not None and terminal_stage != "qa":
        return ()
    try:
        qa_result = resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage="qa",
            run_id=metadata.run_id,
        )
    except ValueError:
        return ()
    if qa_result.final_state not in {
        StageState.SUCCEEDED.value,
        StageState.FAILED.value,
        StageState.BLOCKED.value,
    }:
        return ()
    missing = _missing_terminal_evidence_labels(
        _terminal_final_artifacts(
            workspace_root=workspace_root,
            work_item=work_item,
            metadata=metadata,
        )
    )
    if not missing:
        return ()
    missing_detail = ", ".join(missing)
    return (
        OperatorBlocker(
            kind="terminal-missing-evidence",
            title="Missing terminal evidence",
            detail=(
                f"Terminal QA handoff is missing {missing_detail}. Restore the "
                "required evidence before starting any next flow."
            ),
            severity="error",
            stage="qa",
        ),
    )


def _runtime_exit_signal(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> OperatorFirstFailure | None:
    attempt_number = latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if attempt_number is None:
        return None
    attempt_root = run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    path = attempt_root / RUN_RUNTIME_EXIT_METADATA_FILENAME
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return OperatorFirstFailure(
            kind="runtime-exit-metadata-invalid",
            title="Runtime exit metadata invalid",
            detail="runtime-exit.json is not valid JSON.",
            stage=stage,
            path=workspace_relative_path(workspace_root, path),
            time_utc=None,
        )
    if not isinstance(payload, dict):
        return None
    exit_code = payload.get("exit_code")
    classification = str(payload.get("exit_classification") or "").strip().lower()
    adapter_outcome = str(payload.get("adapter_outcome") or "").strip().lower()
    decisive = classification not in {"", "success"} or adapter_outcome in {
        "timeout",
        "provider_error",
        "provider-no-progress",
        "failed",
        "cancelled",
    }
    if exit_code not in {None, 0}:
        decisive = True
    if not decisive:
        return None
    title = {
        "timeout": "Runtime timeout",
        "provider_error": "Provider error",
        "provider-no-progress": "Provider no progress",
        "cancelled": "Runtime interrupted",
    }.get(classification or adapter_outcome, "Runtime failure")
    metadata_parts = [
        f"exit_code={exit_code}" if exit_code is not None else "",
        f"classification={classification}" if classification else "",
        f"adapter_outcome={adapter_outcome}" if adapter_outcome else "",
    ]
    metadata_detail = ", ".join(part for part in metadata_parts if part)
    outcome = classification or adapter_outcome
    recovery_detail = {
        "cancelled": (
            "The runtime was interrupted before this stage completed. "
            "Inspect runtime.log, runtime-exit.json, and partial workspace diff before retrying."
        ),
        "provider-no-progress": (
            "The provider made no progress before AIDD received a completed stage artifact. "
            "Inspect runtime.log and runtime-exit.json before retrying."
        ),
        "timeout": (
            "The runtime exceeded its configured timeout before this stage completed. "
            "Inspect runtime.log and runtime-exit.json before retrying."
        ),
        "provider_error": (
            "The provider reported an execution error before this stage completed. "
            "Inspect runtime.log and runtime-exit.json before retrying."
        ),
    }.get(outcome)
    detail = recovery_detail or metadata_detail or "Runtime exit failed."
    return OperatorFirstFailure(
        kind=outcome or "runtime-failure",
        title=title,
        detail=detail,
        stage=stage,
        path=workspace_relative_path(workspace_root, path),
        time_utc=str(payload.get("completed_at_utc") or payload.get("updated_at_utc") or "")
        or None,
    )


def _first_failure(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary | None,
    rail_by_stage: dict[str, OperatorStageRailItem],
) -> OperatorFirstFailure | None:
    if metadata is None:
        return None
    for stage in STAGES:
        stage_metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=metadata.run_id,
            stage=stage,
        )
        rail_item = rail_by_stage.get(stage)
        runtime_signal = _runtime_exit_signal(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=metadata.run_id,
            stage=stage,
        )
        if runtime_signal is not None:
            return runtime_signal
        if rail_item is not None and rail_item.validator_fail_count:
            finding = _primary_validation_finding_for_stage(
                workspace_root=workspace_root,
                work_item=work_item,
                stage=stage,
                run_id=metadata.run_id,
            )
            return OperatorFirstFailure(
                kind="validation-failed",
                title="Validation failed",
                detail=(
                    _validation_finding_detail(finding)
                    if finding is not None
                    else f"{rail_item.validator_fail_count} validator result(s) failed."
                ),
                stage=stage,
                path=f"workitems/{work_item}/stages/{stage}/validator-report.md",
                time_utc=stage_metadata.updated_at_utc if stage_metadata else None,
            )
        if rail_item is not None and rail_item.unresolved_blocking_count:
            return OperatorFirstFailure(
                kind="blocking-questions",
                title="Blocking questions",
                detail=f"{rail_item.unresolved_blocking_count} unresolved blocking question(s).",
                stage=stage,
                path=f"workitems/{work_item}/stages/{stage}/questions.md",
                time_utc=stage_metadata.updated_at_utc if stage_metadata else None,
            )
        if stage_metadata is None:
            continue
        latest_repair = stage_metadata.repair_history[-1] if stage_metadata.repair_history else None
        if latest_repair is not None and any(
            marker in latest_repair.outcome.lower()
            for marker in ("exhaust", "failed", "invalid")
        ):
            return OperatorFirstFailure(
                kind="repair-exhausted",
                title="Repair did not recover the stage",
                detail=f"Attempt {latest_repair.attempt_number}: {latest_repair.outcome}.",
                stage=stage,
                path=latest_repair.repair_brief_path or latest_repair.validator_report_path,
                time_utc=latest_repair.recorded_at_utc,
            )
        if stage_metadata.status == StageState.FAILED.value:
            return OperatorFirstFailure(
                kind="stage-failed",
                title="Stage failed",
                detail=f"{stage} ended as failed without a more specific validator/runtime signal.",
                stage=stage,
                path=None,
                time_utc=stage_metadata.updated_at_utc,
            )
        if stage_metadata.status == StageState.BLOCKED.value:
            return OperatorFirstFailure(
                kind="stage-blocked",
                title="Stage blocked",
                detail=f"{stage} is blocked until operator input or remediation is supplied.",
                stage=stage,
                path=None,
                time_utc=stage_metadata.updated_at_utc,
            )
    return None


def _recovery_actions(
    *,
    next_action: OperatorNextAction,
    first_failure: OperatorFirstFailure | None,
    blockers: tuple[OperatorBlocker, ...],
) -> tuple[OperatorRecoveryAction, ...]:
    actions: list[OperatorRecoveryAction] = []
    if next_action.action in {
        "answer-questions",
        "inspect-validation",
        "resume-stage",
        "review-findings",
        "qa-verdict",
        "rerun-stale-downstream",
    }:
        actions.append(
            OperatorRecoveryAction(
                action=next_action.action,
                label=next_action.label,
                detail=next_action.detail,
                stage=next_action.stage,
                enabled=next_action.enabled,
            )
        )
    if first_failure is not None:
        if first_failure.kind in {"validation-failed", "repair-exhausted"}:
            actions.append(
                OperatorRecoveryAction(
                    action="request-change",
                    label="Request change",
                    detail="Create a durable selected-stage intervention request.",
                    stage=first_failure.stage,
                    enabled=True,
                )
            )
        if first_failure.kind in _RUNTIME_FAILURE_KINDS:
            actions.append(
                OperatorRecoveryAction(
                    action="inspect-runtime-log",
                    label="Open logs",
                    detail="Open runtime log and runtime-exit metadata before retrying.",
                    stage=first_failure.stage,
                    enabled=True,
                )
            )
            if first_failure.stage:
                actions.append(
                    OperatorRecoveryAction(
                        action="request-change",
                        label="Request change",
                        detail=(
                            "Create a durable selected-stage intervention request "
                            "after inspecting runtime evidence."
                        ),
                        stage=first_failure.stage,
                        enabled=True,
                    )
                )
    for blocker in blockers:
        if blocker.kind == "missing-input":
            actions.append(
                OperatorRecoveryAction(
                    action="inspect-blocker",
                    label="Inspect missing input",
                    detail=blocker.detail,
                    stage=blocker.stage,
                    enabled=True,
                )
            )
            break
    return tuple(actions[:4])


def _next_action(
    *,
    metadata: RunMetadataSummary | None,
    active_stage: str,
    active_stage_view: OperatorStageView | None,
    rail_by_stage: dict[str, OperatorStageRailItem],
    report_blockers: tuple[OperatorBlocker, ...] = (),
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
    stale_stage = next((item for item in rail_by_stage.values() if item.stale), None)
    if stale_stage is not None:
        return OperatorNextAction(
            action="rerun-stale-downstream",
            label="Rerun stale downstream",
            detail=stale_stage.stale_reason
            or "A remediation attempt invalidated downstream stage evidence.",
            stage=stale_stage.stage,
            enabled=True,
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
    running_stage = _running_stage_item(rail_by_stage)
    if running_stage is not None:
        return _running_stage_next_action(running_stage)
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
                detail=(
                    "Open validation recovery for the requested change result. "
                    "Request another change if repair is exhausted."
                ),
                stage=failed_validation_stage.stage,
                enabled=True,
            )
        return OperatorNextAction(
            action="inspect-validation",
            label=f"Inspect {failed_validation_stage.title} validation",
            detail=(
                "Open validation recovery. Run Repair if available, or Request Change "
                "if the repair budget is exhausted."
            ),
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
    review_blocker = next(
        (
            blocker
            for blocker in report_blockers
            if blocker.kind in {"review-rejected", "review-conditions"}
        ),
        None,
    )
    if review_blocker is not None:
        return OperatorNextAction(
            action="review-findings",
            label="Resolve review findings",
            detail=review_blocker.detail,
            stage="review",
            enabled=True,
        )
    qa_blocker = next(
        (
            blocker
            for blocker in report_blockers
            if blocker.kind in {"qa-not-ready", "qa-ready-with-risks"}
        ),
        None,
    )
    if qa_blocker is not None:
        return OperatorNextAction(
            action="qa-verdict",
            label="Resolve QA verdict",
            detail=qa_blocker.detail,
            stage="qa",
            enabled=True,
        )
    terminal_evidence_blocker = next(
        (
            blocker
            for blocker in report_blockers
            if blocker.kind == "terminal-missing-evidence"
        ),
        None,
    )
    if terminal_evidence_blocker is not None:
        return OperatorNextAction(
            action="review-complete",
            label="Restore terminal evidence",
            detail=terminal_evidence_blocker.detail,
            stage="qa",
            enabled=True,
        )

    incomplete = [
        item for item in rail_by_stage.values() if item.status != StageState.SUCCEEDED.value
    ]
    if not incomplete:
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


def _running_stage_item(
    rail_by_stage: dict[str, OperatorStageRailItem],
) -> OperatorStageRailItem | None:
    return next(
        (item for item in rail_by_stage.values() if item.status in _RUNNING_STAGE_STATES),
        None,
    )


def _running_stage_next_action(running_stage: OperatorStageRailItem) -> OperatorNextAction:
    return OperatorNextAction(
        action="wait-for-stage",
        label=f"{running_stage.title} running",
        detail="Refresh after the active stage leaves preparing, executing, or validating.",
        stage=running_stage.stage,
        enabled=False,
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
                        category=operator_artifact_category(
                            key=key,
                            kind=kind,
                            path=path,
                        ),
                        canonical=operator_artifact_is_canonical(
                            key=key,
                            kind=kind,
                            path=path,
                        ),
                        safe_key=operator_artifact_safe_key(key),
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
                    category=operator_artifact_category(
                        key="operator_request",
                        kind="operator-request",
                        path=relative_path,
                    ),
                    canonical=False,
                    safe_key=operator_artifact_safe_key("operator_request"),
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
        if final_qa_status == "not-ready":
            return "failed"
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
                    category=operator_artifact_category(
                        key=key,
                        kind=kind,
                        path=path,
                    ),
                    canonical=operator_artifact_is_canonical(
                        key=key,
                        kind=kind,
                        path=path,
                    ),
                    safe_key=operator_artifact_safe_key(key),
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


def _compact_repair_reason(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    normalized = re.sub(r"\s+in `[^`]+`:\s*", ": ", normalized)
    if not normalized:
        return ""
    if len(normalized) <= _MAX_REPAIR_REASON_CHARS:
        return normalized
    return f"{normalized[:_MAX_REPAIR_REASON_CHARS - 1].rstrip()}..."


def _read_repair_reason(
    *,
    workspace_root: Path,
    repair_brief_path: str | None,
) -> str | None:
    if not repair_brief_path:
        return None
    path = workspace_root / repair_brief_path
    if not path.exists() or not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    in_failed_checks = False
    fallback_bullet: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            heading = line.lstrip("#").strip().lower()
            in_failed_checks = heading == "failed checks"
            continue
        if not line.startswith(("- ", "* ")):
            continue
        bullet = line[2:].strip()
        if not bullet or bullet.lower() == "none":
            continue
        if in_failed_checks:
            return _compact_repair_reason(bullet)
        if fallback_bullet is None:
            fallback_bullet = bullet
    if fallback_bullet is None:
        return None
    return _compact_repair_reason(fallback_bullet)


def _terminal_repair_highlights(
    *,
    workspace_root: Path,
    work_item: str,
    metadata: RunMetadataSummary,
) -> tuple[OperatorRepairHighlight, ...]:
    highlights: list[OperatorRepairHighlight] = []
    for stage in STAGES:
        stage_metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=metadata.run_id,
            stage=stage,
        )
        if stage_metadata is None:
            continue
        repair_entries = [
            entry for entry in stage_metadata.repair_history if entry.trigger == "repair"
        ]
        for entry in repair_entries:
            reason = _read_repair_reason(
                workspace_root=workspace_root,
                repair_brief_path=entry.repair_brief_path,
            )
            if reason is None:
                reason = f"Attempt {entry.attempt_number}: {entry.outcome}."
            highlights.append(
                OperatorRepairHighlight(
                    stage=stage,
                    attempt_number=entry.attempt_number,
                    outcome=entry.outcome,
                    reason=reason,
                    validator_report_path=entry.validator_report_path,
                    repair_brief_path=entry.repair_brief_path,
                    recorded_at_utc=entry.recorded_at_utc,
                )
            )
    highlights.sort(key=lambda highlight: highlight.recorded_at_utc, reverse=True)
    return tuple(highlights[:_MAX_TERMINAL_REPAIR_HIGHLIGHTS])


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
    missing_terminal_evidence: bool = False,
) -> tuple[OperatorNextFlowRecommendation, ...]:
    if missing_terminal_evidence:
        return (
            OperatorNextFlowRecommendation(
                action="create-new-work-item",
                label="Create New Work Item",
                detail="Restore terminal QA evidence before starting unrelated work.",
                enabled=False,
            ),
            OperatorNextFlowRecommendation(
                action="start-follow-up-flow",
                label="Start Follow-up Flow",
                detail="Restore terminal QA evidence before drafting follow-up work.",
                enabled=False,
            ),
            OperatorNextFlowRecommendation(
                action="clone-flow",
                label="Clone This Flow",
                detail="Restore terminal QA evidence before cloning this run.",
                enabled=False,
            ),
            OperatorNextFlowRecommendation(
                action="run-eval-batch",
                label="Run Eval / Scenario Batch",
                detail="Restore terminal QA evidence before using this run for comparison.",
                enabled=False,
            ),
            OperatorNextFlowRecommendation(
                action="archive-run",
                label="Archive Run",
                detail="Restore terminal QA evidence before archiving the handoff.",
                enabled=False,
            ),
        )
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
    stale_by_stage: dict[str, RemediationStaleStage] | None = None,
) -> OperatorTerminalRunHandoff | None:
    if metadata is None:
        return None
    if stale_by_stage and "qa" in stale_by_stage:
        return None
    terminal_stage = _optional_manifest_stage(metadata.workflow_stage_end)
    if terminal_stage is not None and terminal_stage != "qa":
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

    final_artifacts = _terminal_final_artifacts(
        workspace_root=workspace_root,
        work_item=work_item,
        metadata=metadata,
    )
    missing_terminal_evidence = _missing_terminal_evidence_labels(final_artifacts)
    qa_verdict = _read_qa_verdict(workspace_root=workspace_root, work_item=work_item)
    final_qa_status = (
        "evidence-incomplete"
        if missing_terminal_evidence
        else qa_verdict or qa_result.final_state
    )
    handoff_status = _terminal_handoff_status(
        qa_stage_state=qa_result.final_state,
        final_qa_status=final_qa_status,
    )
    if missing_terminal_evidence and handoff_status != "failed":
        handoff_status = "blocked"
    questions_answered, questions_total = _terminal_question_counts(
        workspace_root=workspace_root,
        work_item=work_item,
    )
    return OperatorTerminalRunHandoff(
        status=handoff_status,
        final_qa_status=final_qa_status,
        qa_stage_state=qa_result.final_state,
        final_artifacts=final_artifacts,
        blockers=blockers,
        repair_counts=_terminal_repair_counts(
            workspace_root=workspace_root,
            work_item=work_item,
            metadata=metadata,
        ),
        repair_highlights=_terminal_repair_highlights(
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
            missing_terminal_evidence=bool(missing_terminal_evidence),
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
    stale_by_stage: dict[str, RemediationStaleStage] = {}
    if metadata is not None:
        remediation_status = load_remediation_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=metadata.run_id,
        )
        stale_by_stage = {entry.stage: entry for entry in remediation_status.stale_stages}
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
        stale_by_stage=stale_by_stage,
    )
    rail_by_stage = {stage.stage: stage for stage in stages}
    running_stage = _running_stage_item(rail_by_stage)
    if running_stage is not None:
        return OperatorDashboardView(
            work_item=work_item,
            workspace_root=workspace_root,
            project_root=selected_project_root,
            active_stage=active_stage,
            run=(
                _run_summary(metadata)
                if metadata
                else _empty_run_summary(workspace_root=workspace_root, work_item=work_item)
            ),
            stages=stages,
            active_stage_view=None,
            primary_artifact=None,
            next_action=_running_stage_next_action(running_stage),
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
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=metadata.run_id if metadata is not None else None,
        active_stage=active_stage,
        active_stage_view=active_stage_view,
        rail_by_stage=rail_by_stage,
    )
    report_blockers = _structured_report_blockers(
        workspace_root=workspace_root,
        work_item=work_item,
        rail_by_stage=rail_by_stage,
    )
    terminal_evidence_blockers = _terminal_missing_evidence_blockers(
        workspace_root=workspace_root,
        work_item=work_item,
        metadata=metadata,
        stale_by_stage=stale_by_stage,
    )
    blockers = (*blockers, *report_blockers, *terminal_evidence_blockers)
    first_failure = _first_failure(
        workspace_root=workspace_root,
        work_item=work_item,
        metadata=metadata,
        rail_by_stage=rail_by_stage,
    )
    if first_failure is not None and first_failure.kind in _RUNTIME_FAILURE_KINDS:
        blockers = (
            *blockers,
            OperatorBlocker(
                kind=first_failure.kind,
                title=first_failure.title,
                detail=first_failure.detail,
                severity="error",
                stage=first_failure.stage,
                path=first_failure.path,
            ),
        )
    next_action = _next_action(
        metadata=metadata,
        active_stage=active_stage,
        active_stage_view=active_stage_view,
        rail_by_stage=rail_by_stage,
        report_blockers=(*report_blockers, *terminal_evidence_blockers),
        stages_with_operator_requests=stages_with_operator_requests,
    )
    validation_stage = active_stage
    if (
        next_action.action in {"inspect-validation", "review-intervention"}
        and next_action.stage
    ):
        validation_stage = next_action.stage
    elif (
        first_failure is not None
        and first_failure.kind == "validation-failed"
        and first_failure.stage
    ):
        validation_stage = first_failure.stage
    validation_findings = _validation_findings_for_stage(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=validation_stage,
        run_id=metadata.run_id if metadata is not None else None,
    )
    return OperatorDashboardView(
        work_item=work_item,
        workspace_root=workspace_root,
        project_root=selected_project_root,
        active_stage=active_stage,
        run=(
            _run_summary(metadata)
            if metadata
            else _empty_run_summary(workspace_root=workspace_root, work_item=work_item)
        ),
        stages=stages,
        active_stage_view=active_stage_view,
        primary_artifact=primary_artifact,
        next_action=next_action,
        blockers=blockers,
        first_failure=first_failure,
        validation_findings=validation_findings,
        primary_validation_finding=(
            validation_findings[0] if validation_findings else None
        ),
        recovery_actions=_recovery_actions(
            next_action=next_action,
            first_failure=first_failure,
            blockers=blockers,
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
        terminal_handoff=_terminal_handoff(
            workspace_root=workspace_root,
            work_item=work_item,
            metadata=metadata,
            blockers=blockers,
            stale_by_stage=stale_by_stage,
        ),
    )

__all__ = ["resolve_operator_dashboard_view"]

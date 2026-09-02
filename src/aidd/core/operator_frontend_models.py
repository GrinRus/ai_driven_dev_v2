from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.core.interview import AnswerResolution, QuestionPolicy
from aidd.core.run_inspection import RunLogSummary, RunMetadataSummary, StageResultSummary


@dataclass(frozen=True, slots=True)
class OperatorQuestionView:
    question_id: str
    text: str
    policy: QuestionPolicy
    status: str
    answer_text: str | None = None
    answer_resolution: AnswerResolution | None = None
    answer_evidence_links: tuple[str, ...] = ()
    answer_unblock_consequence: str | None = None


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
class OperatorRunLogView:
    summary: RunLogSummary
    text: str
    byte_size: int
    start_byte: int
    end_byte: int
    retained_bytes: int
    requested_bytes: int
    max_bytes: int
    truncated: bool
    truncated_head: bool
    truncated_tail: bool
    partial_head_line: bool
    partial_tail_line: bool
    oversized_line: bool

    @property
    def runtime_log_path(self) -> Path:
        return self.summary.runtime_log_path


@dataclass(frozen=True, slots=True)
class OperatorBlockingQuestionDiagnostics:
    status: str
    unresolved_count: int
    unresolved_question_ids: tuple[str, ...]
    answers_path: str


@dataclass(frozen=True, slots=True)
class OperatorValidationFindingView:
    category: str
    code: str
    severity: str
    path: str | None
    line_number: int | None
    message: str
    occurrence_count: int = 1
    operator_hint: str | None = None


@dataclass(frozen=True, slots=True)
class OperatorRepairAttemptDiagnostics:
    attempt_number: int
    trigger: str
    outcome: str
    recorded_at_utc: str
    validator_report_path: str | None
    repair_brief_path: str | None


@dataclass(frozen=True, slots=True)
class OperatorRepairExtensionPreview:
    """Core-owned, read-only projection for the one-time repair extension."""

    work_item: str
    run_id: str
    stage: str
    runtime_id: str | None
    eligible: bool
    disabled_reason: str | None
    primary_cause: OperatorValidationFindingView | None
    current_findings: tuple[OperatorValidationFindingView, ...]
    automatic_repair_attempts_used: int
    automatic_repair_attempts_max: int
    automatic_repair_attempts_remaining: int
    manual_grant_used: bool
    validator_report_path: str | None
    validator_report_sha256: str | None
    repair_brief_path: str | None
    repair_brief_sha256: str | None
    selected_runner: str | None
    downstream_succeeded: tuple[str, ...]
    configuration_identity: str | None

    def __post_init__(self) -> None:
        if self.eligible and self.disabled_reason is not None:
            raise ValueError("An eligible repair-extension preview cannot have a disabled reason.")
        if not self.eligible and not (self.disabled_reason or "").strip():
            raise ValueError("An ineligible repair-extension preview must have a disabled reason.")
        if self.automatic_repair_attempts_used < 0:
            raise ValueError("Automatic repair attempts used must be non-negative.")
        if self.automatic_repair_attempts_max < 0:
            raise ValueError("Automatic repair attempts maximum must be non-negative.")
        if self.automatic_repair_attempts_remaining < 0:
            raise ValueError("Automatic repair attempts remaining must be non-negative.")


@dataclass(frozen=True, slots=True)
class OperatorValidationRepairDiagnostics:
    status: str
    final_state: str
    validator_pass_count: int
    validator_fail_count: int
    validator_report_path: str
    repair_attempts: tuple[OperatorRepairAttemptDiagnostics, ...]
    validation_findings: tuple[OperatorValidationFindingView, ...]
    primary_validation_finding: OperatorValidationFindingView | None
    repair_extension: OperatorRepairExtensionPreview | None = None


@dataclass(frozen=True, slots=True)
class OperatorRawLogSourceDiagnostics:
    status: str
    path: str | None
    byte_size: int | None
    start_byte: int | None
    end_byte: int | None
    truncated: bool
    truncated_head: bool
    truncated_tail: bool
    message: str | None


@dataclass(frozen=True, slots=True)
class OperatorRuntimeApprovalQueueDiagnostics:
    status: str
    requests_path: str
    decisions_path: str
    requested_count: int
    pending_count: int
    approved_count: int
    denied_count: int
    cancelled_count: int
    pending_request_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OperatorInterviewCandidateDiagnostics:
    """Core-owned, bounded recovery state for a rejected runtime interview candidate."""

    status: str
    document: str | None
    canonical_question: OperatorQuestionView | None
    raw_candidate_path: str | None
    raw_candidate: str | None
    raw_candidate_truncated: bool
    disposition_path: str | None
    source_attempt: int | None
    attempt_mode: str | None
    runtime_id: str | None
    reason: str | None
    eligible_recovery_action: str | None
    eligible_recovery_detail: str | None


@dataclass(frozen=True, slots=True)
class OperatorRequestChangeContext:
    status: str
    eligible: bool
    latest_request_id: str | None
    latest_request_path: str | None
    latest_request_excerpt: str | None
    target_documents: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class OperatorStoppedDiagnostics:
    stopped: bool
    source: str | None
    detail: str | None


@dataclass(frozen=True, slots=True)
class OperatorStageDiagnostics:
    status: str
    blocking_questions: OperatorBlockingQuestionDiagnostics
    interview_candidate: OperatorInterviewCandidateDiagnostics
    validation: OperatorValidationRepairDiagnostics
    raw_log: OperatorRawLogSourceDiagnostics
    approvals: OperatorRuntimeApprovalQueueDiagnostics
    request_change: OperatorRequestChangeContext
    stopped: OperatorStoppedDiagnostics


@dataclass(frozen=True, slots=True)
class OperatorStageView:
    result: StageResultSummary
    questions: OperatorQuestionsView
    diagnostics: OperatorStageDiagnostics


@dataclass(frozen=True, slots=True)
class OperatorChildWorkItemCandidate:
    work_item_id: str
    label: str | None
    relationship: str | None
    source_run_id: str | None


@dataclass(frozen=True, slots=True)
class OperatorRunLineage:
    source_run_id: str | None
    source_work_item_id: str | None
    baseline_id: str | None
    baseline_label: str | None
    child_work_item_candidates: tuple[OperatorChildWorkItemCandidate, ...]


@dataclass(frozen=True, slots=True)
class OperatorRunArchive:
    archived: bool
    archived_at_utc: str | None
    reason: str | None
    source: str | None


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
    lineage: OperatorRunLineage
    archive: OperatorRunArchive


@dataclass(frozen=True, slots=True)
class OperatorProjectSetRootSummary:
    root_id: str
    root: str
    relative_root: str
    role: str | None


@dataclass(frozen=True, slots=True)
class OperatorWorkItemSummary:
    work_item: str
    has_request_context: bool
    intent: OperatorIntentSummary
    latest_run: OperatorRunSummary
    active_stage: str
    stage_progress_label: str
    stage_progress_count: int
    stage_total_count: int
    blocker_count: int
    terminal_state: str
    project_set_roots: tuple[OperatorProjectSetRootSummary, ...]


@dataclass(frozen=True, slots=True)
class OperatorIntentSummary:
    """Bounded, read-only projection of the operator's Work Item request."""

    work_item: str
    excerpt: str
    source_path: str | None
    has_request_context: bool
    title: str = ""
    brief: str = ""
    context: str = ""
    constraints: str = ""
    additional_information: str = ""
    structured: bool = False


@dataclass(frozen=True, slots=True)
class OperatorProjectHomeView:
    project_root: Path
    workspace_root: Path
    workspace_exists: bool
    work_items: tuple[OperatorWorkItemSummary, ...]
    recent_project_roots: tuple[str, ...]
    selected_work_item: str | None
    selected_work_item_resume: OperatorWorkItemSummary | None


@dataclass(frozen=True, slots=True)
class OperatorInboxRoute:
    intent: str
    work_item: str
    run_id: str | None
    stage: str


@dataclass(frozen=True, slots=True)
class OperatorInboxItem:
    item_id: str
    state: str
    status_label: str
    title: str
    summary: str
    route: OperatorInboxRoute
    primary_action: OperatorNextAction


@dataclass(frozen=True, slots=True)
class OperatorInboxSection:
    key: str
    label: str
    items: tuple[OperatorInboxItem, ...]


@dataclass(frozen=True, slots=True)
class OperatorInboxEntryRecommendation:
    action: str
    label: str
    detail: str
    work_item: str | None = None
    route: OperatorInboxRoute | None = None


@dataclass(frozen=True, slots=True)
class OperatorInboxView:
    project_root: Path
    workspace_root: Path
    sections: tuple[OperatorInboxSection, ...]
    entry_recommendation: OperatorInboxEntryRecommendation | None = None

    @property
    def item_count(self) -> int:
        return sum(len(section.items) for section in self.sections)


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
    stale: bool = False
    stale_reason: str | None = None
    stale_invalidated_by: str | None = None


@dataclass(frozen=True, slots=True)
class OperatorIntentPhaseSummary:
    """Read-only grouping of canonical stages for intent-centered navigation."""

    phase_id: str
    label: str
    stages: tuple[str, ...]
    status: str


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
class OperatorFirstFailure:
    kind: str
    title: str
    detail: str
    stage: str | None
    path: str | None
    time_utc: str | None


@dataclass(frozen=True, slots=True)
class OperatorRecoveryAction:
    action: str
    label: str
    detail: str
    stage: str | None
    enabled: bool


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
    category: str = "canonical-stage-document"
    canonical: bool = False
    latest: bool = True
    stale: bool = False
    generated: bool = True
    available: bool = True
    safe_key: str | None = None


@dataclass(frozen=True, slots=True)
class OperatorPrimaryArtifact:
    key: str
    path: str
    content_type: str
    byte_size: int
    excerpt: str
    truncated: bool


@dataclass(frozen=True, slots=True)
class OperatorRepairCounts:
    attempts: int
    succeeded: int
    failed: int


@dataclass(frozen=True, slots=True)
class OperatorRepairHighlight:
    stage: str
    attempt_number: int
    outcome: str
    reason: str
    validator_report_path: str | None
    repair_brief_path: str | None
    recorded_at_utc: str


@dataclass(frozen=True, slots=True)
class OperatorApprovalCounts:
    requested: int
    approved: int
    denied: int
    cancelled: int
    pending: int


@dataclass(frozen=True, slots=True)
class OperatorNextFlowRecommendation:
    action: str
    label: str
    detail: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class OperatorTerminalRunHandoff:
    status: str
    final_qa_status: str
    qa_stage_state: str
    final_artifacts: tuple[OperatorArtifactRef, ...]
    blockers: tuple[OperatorBlocker, ...]
    repair_counts: OperatorRepairCounts
    repair_highlights: tuple[OperatorRepairHighlight, ...]
    approval_counts: OperatorApprovalCounts
    questions_answered_count: int
    questions_total_count: int
    recommended_outcome: str | None
    recommendation_rationale: str | None
    recommended_next_flow_actions: tuple[OperatorNextFlowRecommendation, ...]


@dataclass(frozen=True, slots=True)
class OperatorArtifactDocumentView:
    run_id: str
    stage: str
    attempt_number: int
    key: str
    path: str
    text: str
    byte_size: int
    content_type: str
    mode: str
    start_byte: int
    end_byte: int
    requested_bytes: int
    max_bytes: int
    truncated: bool
    truncated_head: bool
    truncated_tail: bool


@dataclass(frozen=True, slots=True)
class OperatorStageWorkbenchDocument:
    key: str
    path: str
    status: str
    message: str | None
    content_type: str | None
    byte_size: int | None
    preview: OperatorArtifactDocumentView | None
    source: OperatorArtifactDocumentView | None


@dataclass(frozen=True, slots=True)
class OperatorStageDocumentRequirement:
    kind: str
    label: str
    path: str | None
    status: str
    source: str


@dataclass(frozen=True, slots=True)
class OperatorStageDocumentValidationResult:
    label: str
    status: str
    path: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class OperatorStageDocumentReference:
    label: str
    kind: str
    path: str
    stage: str | None = None
    category: str = "canonical-stage-document"


@dataclass(frozen=True, slots=True)
class OperatorStageDocumentDiffInput:
    label: str
    kind: str
    key: str
    path: str
    attempt_number: int | None


@dataclass(frozen=True, slots=True)
class OperatorStageDocumentVersion:
    label: str
    key: str
    path: str
    run_id: str
    attempt_number: int
    updated_at_utc: str | None
    source: str


@dataclass(frozen=True, slots=True)
class OperatorEvidenceGraphNode:
    node_id: str
    label: str
    kind: str
    stage: str | None
    path: str | None
    status: str
    detail: str
    byte_size: int | None
    updated_at_utc: str | None


@dataclass(frozen=True, slots=True)
class OperatorEvidenceGraphEdge:
    source_id: str
    target_id: str
    kind: str
    label: str


@dataclass(frozen=True, slots=True)
class OperatorEvidenceGraphView:
    run_id: str
    stage: str
    attempt_number: int
    mode: str
    nodes: tuple[OperatorEvidenceGraphNode, ...]
    edges: tuple[OperatorEvidenceGraphEdge, ...]
    artifact_table: tuple[OperatorArtifactRef, ...]
    incomplete_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OperatorStageDocumentWorkbench:
    run_id: str
    stage: str
    attempt_number: int
    selected_key: str
    document: OperatorStageWorkbenchDocument
    requirements: tuple[OperatorStageDocumentRequirement, ...]
    validation_results: tuple[OperatorStageDocumentValidationResult, ...]
    references: tuple[OperatorStageDocumentReference, ...]
    diff_inputs: tuple[OperatorStageDocumentDiffInput, ...]
    versions: tuple[OperatorStageDocumentVersion, ...]


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
    first_failure: OperatorFirstFailure | None
    validation_findings: tuple[OperatorValidationFindingView, ...]
    primary_validation_finding: OperatorValidationFindingView | None
    recovery_actions: tuple[OperatorRecoveryAction, ...]
    evidence_refs: tuple[OperatorEvidenceRef, ...]
    activity: tuple[OperatorActivityEvent, ...]
    recent_artifacts: tuple[OperatorArtifactRef, ...]
    terminal_handoff: OperatorTerminalRunHandoff | None
    phases: tuple[OperatorIntentPhaseSummary, ...] = ()


__all__ = [
    "OperatorActivityEvent",
    "OperatorApprovalCounts",
    "OperatorArtifactDocumentView",
    "OperatorArtifactRef",
    "OperatorBlocker",
    "OperatorBlockingQuestionDiagnostics",
    "OperatorChildWorkItemCandidate",
    "OperatorDashboardView",
    "OperatorEvidenceRef",
    "OperatorEvidenceGraphEdge",
    "OperatorEvidenceGraphNode",
    "OperatorEvidenceGraphView",
    "OperatorNextAction",
    "OperatorNextFlowRecommendation",
    "OperatorFirstFailure",
    "OperatorInboxItem",
    "OperatorInboxEntryRecommendation",
    "OperatorInboxRoute",
    "OperatorInboxSection",
    "OperatorInboxView",
    "OperatorIntentSummary",
    "OperatorIntentPhaseSummary",
    "OperatorPrimaryArtifact",
    "OperatorProjectHomeView",
    "OperatorProjectSetRootSummary",
    "OperatorWorkItemSummary",
    "OperatorQuestionView",
    "OperatorQuestionsView",
    "OperatorRawLogSourceDiagnostics",
    "OperatorRepairAttemptDiagnostics",
    "OperatorRepairHighlight",
    "OperatorRequestChangeContext",
    "OperatorRepairCounts",
    "OperatorRecoveryAction",
    "OperatorRunArchive",
    "OperatorRunLogView",
    "OperatorRunLineage",
    "OperatorRunSummary",
    "OperatorRunView",
    "OperatorRuntimeApprovalQueueDiagnostics",
    "OperatorStageDiagnostics",
    "OperatorStageRailItem",
    "OperatorStageDocumentDiffInput",
    "OperatorStageDocumentReference",
    "OperatorStageDocumentRequirement",
    "OperatorStageDocumentValidationResult",
    "OperatorStageDocumentVersion",
    "OperatorStageDocumentWorkbench",
    "OperatorStageWorkbenchDocument",
    "OperatorStageView",
    "OperatorStoppedDiagnostics",
    "OperatorTerminalRunHandoff",
    "OperatorValidationFindingView",
    "OperatorValidationRepairDiagnostics",
]

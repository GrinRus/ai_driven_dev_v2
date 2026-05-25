from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from aidd.core.state_machine import StageState
from aidd.validators.models import ValidationFinding


@dataclass(frozen=True, slots=True)
class StagePreparationBundle:
    stage: str
    work_item: str
    stage_brief_markdown: str
    expected_input_bundle: tuple[Path, ...]
    expected_output_documents: tuple[Path, ...]
    project_set_context_path: Path | None = None


@dataclass(frozen=True, slots=True)
class StageExecutionState:
    stage: str
    work_item: str
    run_id: str
    attempt_number: int
    attempt_path: Path
    stage_metadata_path: Path


@dataclass(frozen=True, slots=True)
class AdapterInvocationBundle:
    stage: str
    work_item: str
    run_id: str
    attempt_number: int
    repair_mode: bool
    stage_brief_markdown: str
    repair_context_markdown: str | None
    repair_brief_path: Path | None
    repair_brief_markdown: str | None
    input_bundle_path: Path
    input_bundle_markdown: str
    expected_input_bundle: tuple[Path, ...]
    expected_output_documents: tuple[Path, ...]
    attempt_mode: str = "initial"
    operator_request_path: Path | None = None
    operator_request_markdown: str | None = None


@dataclass(frozen=True, slots=True)
class StageOutputDiscovery:
    stage: str
    work_item: str
    run_id: str
    attempt_number: int
    expected_markdown_documents: tuple[Path, ...]
    discovered_markdown_documents: tuple[Path, ...]
    missing_markdown_documents: tuple[Path, ...]


class ValidationVerdict(StrEnum):
    PASS = "pass"
    REPAIR = "repair"
    BLOCKED = "blocked"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class StageValidationState:
    stage: str
    work_item: str
    run_id: str
    verdict: ValidationVerdict
    next_state: StageState
    stage_metadata_path: Path


@dataclass(frozen=True, slots=True)
class StageStructuralValidationResult:
    stage: str
    work_item: str
    run_id: str
    attempt_number: int
    validator_report_path: Path
    findings: tuple[ValidationFinding, ...]


@dataclass(frozen=True, slots=True)
class StageOutputPublication:
    stage: str
    work_item: str
    run_id: str
    published_output_root: Path
    published_documents: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class StageInterviewRouting:
    stage: str
    work_item: str
    run_id: str
    attempt_number: int
    questions_path: Path
    answers_path: Path
    unresolved_blocking_question_ids: tuple[str, ...]
    requires_interview: bool


@dataclass(frozen=True, slots=True)
class RepairBudgetValidationTransition:
    stage: str
    work_item: str
    run_id: str
    requested_verdict: ValidationVerdict
    resolved_verdict: ValidationVerdict
    budget_exhausted: bool
    remaining_repair_attempts: int | None
    validation_state: StageValidationState


class PostValidationAction(StrEnum):
    ADVANCE = "advance"
    REPAIR = "repair"
    WAIT = "wait"
    STOP = "stop"


@dataclass(frozen=True, slots=True)
class PostValidationTransition:
    stage: str
    work_item: str
    run_id: str
    next_state: StageState
    action: PostValidationAction
    is_terminal: bool
    stage_metadata_path: Path


@dataclass(frozen=True, slots=True)
class StageUnblockState:
    stage: str
    work_item: str
    run_id: str
    was_blocked: bool
    unblocked: bool
    next_state: StageState | None
    stage_metadata_path: Path | None


@dataclass(frozen=True, slots=True)
class StageResumeResult:
    stage: str
    work_item: str
    run_id: str
    unblock_state: StageUnblockState
    preparation_bundle: StagePreparationBundle | None
    execution_state: StageExecutionState | None
    adapter_invocation: AdapterInvocationBundle | None


@dataclass(frozen=True, slots=True)
class AdapterExecutionOutcome:
    succeeded: bool
    details: str | None = None


@dataclass(frozen=True, slots=True)
class StageOrchestrationResult:
    stage: str
    work_item: str
    run_id: str
    preparation_bundle: StagePreparationBundle
    execution_state: StageExecutionState
    adapter_invocation: AdapterInvocationBundle
    adapter_outcome: AdapterExecutionOutcome
    discovery: StageOutputDiscovery | None
    validation_result: StageStructuralValidationResult | None
    interview_routing: StageInterviewRouting | None
    validation_transition: RepairBudgetValidationTransition | None
    transition: PostValidationTransition


__all__ = [
    "AdapterExecutionOutcome",
    "AdapterInvocationBundle",
    "PostValidationAction",
    "PostValidationTransition",
    "RepairBudgetValidationTransition",
    "StageExecutionState",
    "StageInterviewRouting",
    "StageOrchestrationResult",
    "StageOutputDiscovery",
    "StageOutputPublication",
    "StagePreparationBundle",
    "StageResumeResult",
    "StageStructuralValidationResult",
    "StageUnblockState",
    "StageValidationState",
    "ValidationVerdict",
]

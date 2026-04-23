from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from shutil import copy2

from aidd.core.interview import (
    load_answers_document,
    load_questions_document,
    resolved_question_ids,
    stage_has_unresolved_blocking_questions,
    unresolved_blocking_questions,
)
from aidd.core.repair import RepairBudgetPolicy, evaluate_stage_repair_counter
from aidd.core.run_store import (
    RUN_ATTEMPT_PREFIX,
    create_next_attempt_directory,
    load_stage_metadata,
    persist_stage_status,
    run_stage_metadata_path,
)
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    load_stage_manifest,
    resolve_expected_output_documents,
    resolve_required_input_documents,
)
from aidd.core.state_machine import StageState, is_terminal_state, transition_stage_state
from aidd.core.workspace import stage_output_root as workspace_stage_output_root
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.validators.cross_document import (
    BLOCKING_UNANSWERED_CODE,
    validate_cross_document_consistency,
)
from aidd.validators.models import ValidationFinding
from aidd.validators.reports import write_validator_report
from aidd.validators.semantic import validate_semantic_outputs
from aidd.validators.structural import (
    validate_required_document_existence,
    validate_required_sections,
)


@dataclass(frozen=True, slots=True)
class StagePreparationBundle:
    stage: str
    work_item: str
    stage_brief_markdown: str
    expected_input_bundle: tuple[Path, ...]
    expected_output_documents: tuple[Path, ...]


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
    input_bundle_path: Path
    input_bundle_markdown: str
    expected_input_bundle: tuple[Path, ...]
    expected_output_documents: tuple[Path, ...]


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


def derive_validation_verdict(
    *,
    findings: tuple[ValidationFinding, ...],
    interview_routing: StageInterviewRouting | None = None,
) -> ValidationVerdict:
    if any(finding.code == BLOCKING_UNANSWERED_CODE for finding in findings):
        return ValidationVerdict.BLOCKED
    if findings:
        return ValidationVerdict.REPAIR
    if interview_routing is not None and interview_routing.requires_interview:
        return ValidationVerdict.BLOCKED
    return ValidationVerdict.PASS


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


ATTEMPT_INPUT_BUNDLE_FILENAME = "input-bundle.md"


def _to_workspace_relative_paths(workspace_root: Path, paths: tuple[Path, ...]) -> tuple[str, ...]:
    resolved_workspace = workspace_root.resolve(strict=False)
    return tuple(
        path.resolve(strict=False).relative_to(resolved_workspace).as_posix() for path in paths
    )


def _workspace_relative_path(workspace_root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(workspace_root.resolve(strict=False)).as_posix()


def _render_stage_brief(
    *,
    stage: str,
    purpose: str | None,
    expected_input_bundle: tuple[str, ...],
    expected_output_documents: tuple[str, ...],
) -> str:
    lines = [
        "# Stage",
        "",
        stage,
        "",
        "# Purpose",
        "",
        purpose or "No purpose provided in stage contract.",
        "",
        "# Expected input bundle",
        "",
    ]
    lines.extend(f"- `{path}`" for path in expected_input_bundle)
    lines.extend(["", "# Expected output documents", ""])
    lines.extend(f"- `{path}`" for path in expected_output_documents)
    lines.append("")
    return "\n".join(lines)


def prepare_stage_bundle(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> StagePreparationBundle:
    manifest = load_stage_manifest(stage=stage, contracts_root=contracts_root)
    expected_inputs = resolve_required_input_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    expected_outputs = resolve_expected_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    stage_brief = _render_stage_brief(
        stage=stage,
        purpose=manifest.purpose,
        expected_input_bundle=_to_workspace_relative_paths(workspace_root, expected_inputs),
        expected_output_documents=_to_workspace_relative_paths(workspace_root, expected_outputs),
    )
    return StagePreparationBundle(
        stage=stage,
        work_item=work_item,
        stage_brief_markdown=stage_brief,
        expected_input_bundle=expected_inputs,
        expected_output_documents=expected_outputs,
    )


def _attempt_number_from_path(attempt_path: Path) -> int:
    if not attempt_path.name.startswith(RUN_ATTEMPT_PREFIX):
        raise ValueError(f"Invalid attempt directory name: {attempt_path.name}")
    suffix = attempt_path.name.removeprefix(RUN_ATTEMPT_PREFIX)
    if not suffix.isdigit():
        raise ValueError(f"Invalid attempt directory suffix: {attempt_path.name}")
    return int(suffix)


def persist_execution_state(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    changed_at_utc: datetime | None = None,
) -> StageExecutionState:
    attempt_path = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    stage_metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=StageState.EXECUTING.value,
        changed_at_utc=changed_at_utc,
    )
    return StageExecutionState(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        attempt_number=_attempt_number_from_path(attempt_path),
        attempt_path=attempt_path,
        stage_metadata_path=stage_metadata_path,
    )


def _render_repair_context(
    *,
    workspace_root: Path,
    attempt_number: int,
    repair_brief_path: Path,
    repair_brief_markdown: str,
) -> str:
    lines = [
        "# Repair context",
        "",
        "- Mode: `repair`",
        f"- Attempt number: `{attempt_number}`",
        f"- Repair brief source: `{_workspace_relative_path(workspace_root, repair_brief_path)}`",
        "",
        "## Repair instructions",
        "",
        repair_brief_markdown.strip(),
        "",
    ]
    return "\n".join(lines)


def _render_input_bundle_markdown(
    *,
    workspace_root: Path,
    expected_input_bundle: tuple[Path, ...],
) -> str:
    lines = [
        "# Input bundle",
        "",
        "Resolved stage inputs for this attempt.",
        "",
    ]
    for document_path in expected_input_bundle:
        relative_path = _workspace_relative_path(workspace_root, document_path)
        if not document_path.exists():
            raise FileNotFoundError(
                "Input bundle preparation requires an existing input document: "
                f"{relative_path}"
            )
        document_content = document_path.read_text(encoding="utf-8").strip()
        lines.extend(
            [
                f"## `{relative_path}`",
                "",
                document_content if document_content else "(empty document)",
                "",
            ]
        )
    return "\n".join(lines)


def _prepare_attempt_input_bundle(
    *,
    workspace_root: Path,
    attempt_path: Path,
    expected_input_bundle: tuple[Path, ...],
) -> tuple[Path, str]:
    input_bundle_markdown = _render_input_bundle_markdown(
        workspace_root=workspace_root,
        expected_input_bundle=expected_input_bundle,
    )
    input_bundle_path = attempt_path / ATTEMPT_INPUT_BUNDLE_FILENAME
    input_bundle_path.write_text(input_bundle_markdown, encoding="utf-8")
    return input_bundle_path, input_bundle_markdown


def prepare_adapter_invocation(
    *,
    workspace_root: Path,
    preparation_bundle: StagePreparationBundle,
    execution_state: StageExecutionState,
) -> AdapterInvocationBundle:
    if preparation_bundle.stage != execution_state.stage:
        raise ValueError(
            "Preparation bundle stage does not match execution state stage: "
            f"{preparation_bundle.stage} != {execution_state.stage}"
        )
    if preparation_bundle.work_item != execution_state.work_item:
        raise ValueError(
            "Preparation bundle work item does not match execution state work item: "
            f"{preparation_bundle.work_item} != {execution_state.work_item}"
        )

    repair_mode = execution_state.attempt_number > 1
    repair_brief_path: Path | None = None
    repair_context_markdown: str | None = None

    if repair_mode:
        repair_brief_path = (
            workspace_stage_root(
                root=workspace_root,
                work_item=execution_state.work_item,
                stage=execution_state.stage,
            )
            / "repair-brief.md"
        )
        if not repair_brief_path.exists():
            raise FileNotFoundError(
                "Repair rerun requires an existing repair brief: "
                f"{_workspace_relative_path(workspace_root, repair_brief_path)}"
            )
        repair_brief_markdown = repair_brief_path.read_text(encoding="utf-8").strip()
        if not repair_brief_markdown:
            raise ValueError(
                "Repair rerun requires a non-empty repair brief: "
                f"{_workspace_relative_path(workspace_root, repair_brief_path)}"
            )
        repair_context_markdown = _render_repair_context(
            workspace_root=workspace_root,
            attempt_number=execution_state.attempt_number,
            repair_brief_path=repair_brief_path,
            repair_brief_markdown=repair_brief_markdown,
        )

    input_bundle_path, input_bundle_markdown = _prepare_attempt_input_bundle(
        workspace_root=workspace_root,
        attempt_path=execution_state.attempt_path,
        expected_input_bundle=preparation_bundle.expected_input_bundle,
    )

    return AdapterInvocationBundle(
        stage=execution_state.stage,
        work_item=execution_state.work_item,
        run_id=execution_state.run_id,
        attempt_number=execution_state.attempt_number,
        repair_mode=repair_mode,
        stage_brief_markdown=preparation_bundle.stage_brief_markdown,
        repair_context_markdown=repair_context_markdown,
        repair_brief_path=repair_brief_path,
        input_bundle_path=input_bundle_path,
        input_bundle_markdown=input_bundle_markdown,
        expected_input_bundle=preparation_bundle.expected_input_bundle,
        expected_output_documents=preparation_bundle.expected_output_documents,
    )


def discover_stage_markdown_outputs(
    *,
    execution_state: StageExecutionState,
    invocation_bundle: AdapterInvocationBundle,
) -> StageOutputDiscovery:
    if execution_state.stage != invocation_bundle.stage:
        raise ValueError(
            "Execution state stage does not match adapter invocation stage: "
            f"{execution_state.stage} != {invocation_bundle.stage}"
        )
    if execution_state.work_item != invocation_bundle.work_item:
        raise ValueError(
            "Execution state work item does not match adapter invocation work item: "
            f"{execution_state.work_item} != {invocation_bundle.work_item}"
        )
    if execution_state.run_id != invocation_bundle.run_id:
        raise ValueError(
            "Execution state run id does not match adapter invocation run id: "
            f"{execution_state.run_id} != {invocation_bundle.run_id}"
        )
    if execution_state.attempt_number != invocation_bundle.attempt_number:
        raise ValueError(
            "Execution state attempt number does not match adapter invocation attempt number: "
            f"{execution_state.attempt_number} != {invocation_bundle.attempt_number}"
        )

    expected_markdown_documents = tuple(
        path
        for path in invocation_bundle.expected_output_documents
        if path.suffix.lower() == ".md"
    )
    discovered_markdown_documents = tuple(
        path for path in expected_markdown_documents if path.exists()
    )
    missing_markdown_documents = tuple(
        path for path in expected_markdown_documents if not path.exists()
    )
    return StageOutputDiscovery(
        stage=execution_state.stage,
        work_item=execution_state.work_item,
        run_id=execution_state.run_id,
        attempt_number=execution_state.attempt_number,
        expected_markdown_documents=expected_markdown_documents,
        discovered_markdown_documents=discovered_markdown_documents,
        missing_markdown_documents=missing_markdown_documents,
    )


def run_structural_validation_after_output_discovery(
    *,
    workspace_root: Path,
    discovery: StageOutputDiscovery,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> StageStructuralValidationResult:
    structural_findings = validate_required_document_existence(
        stage=discovery.stage,
        work_item=discovery.work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    section_findings = validate_required_sections(
        stage=discovery.stage,
        work_item=discovery.work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    findings: tuple[ValidationFinding, ...]
    findings = (*structural_findings, *section_findings)
    if not findings:
        semantic_findings = validate_semantic_outputs(
            stage=discovery.stage,
            work_item=discovery.work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
        cross_document_findings = validate_cross_document_consistency(
            stage=discovery.stage,
            work_item=discovery.work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
        findings = (*semantic_findings, *cross_document_findings)

    stage_root = workspace_stage_root(
        root=workspace_root,
        work_item=discovery.work_item,
        stage=discovery.stage,
    )
    stage_root.mkdir(parents=True, exist_ok=True)
    validator_report_path = stage_root / "validator-report.md"
    write_validator_report(path=validator_report_path, findings=findings)
    return StageStructuralValidationResult(
        stage=discovery.stage,
        work_item=discovery.work_item,
        run_id=discovery.run_id,
        attempt_number=discovery.attempt_number,
        validator_report_path=validator_report_path,
        findings=findings,
    )


def _deduplicate_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    deduplicated: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        normalized = path.resolve(strict=False)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(path)
    return tuple(deduplicated)


def publish_stage_outputs_after_validation_pass(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> StageOutputPublication:
    stage_documents_root = workspace_stage_root(
        root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    published_output_root = workspace_stage_output_root(
        root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    published_output_root.mkdir(parents=True, exist_ok=True)

    declared_primary_outputs = resolve_expected_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    source_documents = _deduplicate_paths(
        (
            *declared_primary_outputs,
            stage_documents_root / "stage-result.md",
            stage_documents_root / "validator-report.md",
        )
    )

    published_documents: list[Path] = []
    for source_document in source_documents:
        if source_document.suffix.lower() != ".md":
            continue
        if not source_document.exists():
            raise FileNotFoundError(
                "Stage output publishing requires an existing source document: "
                f"{_workspace_relative_path(workspace_root, source_document)}"
            )
        destination_document = published_output_root / source_document.name
        copy2(source_document, destination_document)
        published_documents.append(destination_document)

    return StageOutputPublication(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        published_output_root=published_output_root,
        published_documents=tuple(published_documents),
    )


def route_stage_questions_to_interview(
    *,
    workspace_root: Path,
    discovery: StageOutputDiscovery,
) -> StageInterviewRouting:
    stage_documents_root = workspace_stage_root(
        root=workspace_root,
        work_item=discovery.work_item,
        stage=discovery.stage,
    )
    questions_path = stage_documents_root / "questions.md"
    answers_path = stage_documents_root / "answers.md"

    questions = load_questions_document(
        workspace_root=workspace_root,
        work_item=discovery.work_item,
        stage=discovery.stage,
    )
    answers = load_answers_document(
        workspace_root=workspace_root,
        work_item=discovery.work_item,
        stage=discovery.stage,
    )
    unresolved = unresolved_blocking_questions(
        questions=questions,
        resolved_question_ids=resolved_question_ids(answers=answers),
    )
    unresolved_ids = tuple(question.question_id for question in unresolved)
    return StageInterviewRouting(
        stage=discovery.stage,
        work_item=discovery.work_item,
        run_id=discovery.run_id,
        attempt_number=discovery.attempt_number,
        questions_path=questions_path,
        answers_path=answers_path,
        unresolved_blocking_question_ids=unresolved_ids,
        requires_interview=bool(unresolved_ids),
    )


def persist_validation_state(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    verdict: ValidationVerdict,
    from_state: StageState = StageState.VALIDATING,
    changed_at_utc: datetime | None = None,
) -> StageValidationState:
    next_state_map = {
        ValidationVerdict.PASS: StageState.SUCCEEDED,
        ValidationVerdict.REPAIR: StageState.REPAIR_NEEDED,
        ValidationVerdict.BLOCKED: StageState.BLOCKED,
        ValidationVerdict.FAIL: StageState.FAILED,
    }
    next_state = next_state_map[verdict]
    transition_stage_state(from_state=from_state, to_state=next_state)

    stage_metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=next_state.value,
        changed_at_utc=changed_at_utc,
    )
    return StageValidationState(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        verdict=verdict,
        next_state=next_state,
        stage_metadata_path=stage_metadata_path,
    )


def persist_validation_state_with_repair_budget(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    verdict: ValidationVerdict,
    repair_policy: RepairBudgetPolicy | None = None,
    from_state: StageState = StageState.VALIDATING,
    changed_at_utc: datetime | None = None,
) -> RepairBudgetValidationTransition:
    resolved_verdict = verdict
    budget_exhausted = False
    remaining_repair_attempts: int | None = None

    if verdict is ValidationVerdict.REPAIR:
        repair_counter = evaluate_stage_repair_counter(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            policy=repair_policy,
        )
        budget_exhausted = repair_counter.budget_exhausted
        remaining_repair_attempts = repair_counter.remaining_repair_attempts
        if budget_exhausted:
            resolved_verdict = ValidationVerdict.FAIL

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        verdict=resolved_verdict,
        from_state=from_state,
        changed_at_utc=changed_at_utc,
    )
    return RepairBudgetValidationTransition(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        requested_verdict=verdict,
        resolved_verdict=resolved_verdict,
        budget_exhausted=budget_exhausted,
        remaining_repair_attempts=remaining_repair_attempts,
        validation_state=validation_state,
    )


def update_stage_unblock_state(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    changed_at_utc: datetime | None = None,
) -> StageUnblockState:
    stage_metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if stage_metadata is None:
        return StageUnblockState(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            was_blocked=False,
            unblocked=False,
            next_state=None,
            stage_metadata_path=None,
        )

    current_status = stage_metadata.status.lower()
    if current_status != StageState.BLOCKED.value:
        try:
            next_state: StageState | None = StageState(current_status)
        except ValueError:
            next_state = None
        return StageUnblockState(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            was_blocked=False,
            unblocked=False,
            next_state=next_state,
            stage_metadata_path=run_stage_metadata_path(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            ),
        )

    if stage_has_unresolved_blocking_questions(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    ):
        return StageUnblockState(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            was_blocked=True,
            unblocked=False,
            next_state=StageState.BLOCKED,
            stage_metadata_path=run_stage_metadata_path(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            ),
        )

    transition_stage_state(from_state=StageState.BLOCKED, to_state=StageState.PREPARING)
    stage_metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=StageState.PREPARING.value,
        changed_at_utc=changed_at_utc,
    )
    return StageUnblockState(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        was_blocked=True,
        unblocked=True,
        next_state=StageState.PREPARING,
        stage_metadata_path=stage_metadata_path,
    )


def prepare_stage_resume_after_answers(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    changed_at_utc: datetime | None = None,
) -> StageResumeResult:
    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        changed_at_utc=changed_at_utc,
    )
    if not unblock_state.unblocked:
        return StageResumeResult(
            stage=stage,
            work_item=work_item,
            run_id=run_id,
            unblock_state=unblock_state,
            preparation_bundle=None,
            execution_state=None,
            adapter_invocation=None,
        )

    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        contracts_root=contracts_root,
    )
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        changed_at_utc=changed_at_utc,
    )
    adapter_invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    return StageResumeResult(
        stage=stage,
        work_item=work_item,
        run_id=run_id,
        unblock_state=unblock_state,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
        adapter_invocation=adapter_invocation,
    )


def decide_post_validation_transition(
    validation_state: StageValidationState,
    *,
    workspace_root: Path | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> PostValidationTransition:
    next_state = validation_state.next_state
    stage_metadata_path = validation_state.stage_metadata_path

    if (
        workspace_root is not None
        and next_state == StageState.SUCCEEDED
        and stage_has_unresolved_blocking_questions(
            workspace_root=workspace_root,
            work_item=validation_state.work_item,
            stage=validation_state.stage,
        )
    ):
        next_state = StageState.BLOCKED
        stage_metadata_path = persist_stage_status(
            workspace_root=workspace_root,
            work_item=validation_state.work_item,
            run_id=validation_state.run_id,
            stage=validation_state.stage,
            status=StageState.BLOCKED.value,
        )
    elif workspace_root is not None and next_state == StageState.SUCCEEDED:
        publish_stage_outputs_after_validation_pass(
            workspace_root=workspace_root,
            work_item=validation_state.work_item,
            run_id=validation_state.run_id,
            stage=validation_state.stage,
            contracts_root=contracts_root,
        )

    action_map: dict[StageState, PostValidationAction] = {
        StageState.SUCCEEDED: PostValidationAction.ADVANCE,
        StageState.REPAIR_NEEDED: PostValidationAction.REPAIR,
        StageState.BLOCKED: PostValidationAction.WAIT,
        StageState.FAILED: PostValidationAction.STOP,
    }
    if next_state not in action_map:
        raise ValueError(
            "Unsupported post-validation state: "
            f"{next_state}"
        )

    return PostValidationTransition(
        stage=validation_state.stage,
        work_item=validation_state.work_item,
        run_id=validation_state.run_id,
        next_state=next_state,
        action=action_map[next_state],
        is_terminal=is_terminal_state(next_state),
        stage_metadata_path=stage_metadata_path,
    )

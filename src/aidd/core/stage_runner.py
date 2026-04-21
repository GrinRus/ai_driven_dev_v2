from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from aidd.core.interview import stage_has_unresolved_blocking_questions
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


def _to_workspace_relative_paths(workspace_root: Path, paths: tuple[Path, ...]) -> tuple[str, ...]:
    resolved_workspace = workspace_root.resolve(strict=False)
    return tuple(
        path.resolve(strict=False).relative_to(resolved_workspace).as_posix() for path in paths
    )


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


def decide_post_validation_transition(
    validation_state: StageValidationState,
    *,
    workspace_root: Path | None = None,
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

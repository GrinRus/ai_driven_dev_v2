from __future__ import annotations

from pathlib import Path

from aidd.core.models.run import StageRunMetadata
from aidd.core.run_store import (
    RUN_ATTEMPT_INPUT_BUNDLE_FILENAME,
    RUN_ATTEMPT_REPAIR_CONTEXT_FILENAME,
    load_stage_metadata,
    write_attempt_artifact_index,
)
from aidd.core.stage_models import (
    AdapterInvocationBundle,
    StageExecutionState,
    StagePreparationBundle,
)
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stage_registry import DEFAULT_STAGE_CONTRACTS_ROOT
from aidd.core.state_machine import StageState
from aidd.core.workspace import stage_root as workspace_stage_root

ATTEMPT_INPUT_BUNDLE_FILENAME = RUN_ATTEMPT_INPUT_BUNDLE_FILENAME
ATTEMPT_REPAIR_CONTEXT_FILENAME = RUN_ATTEMPT_REPAIR_CONTEXT_FILENAME


def _missing_input_document_message(relative_path: str) -> str:
    message = f"Input bundle preparation requires an existing input document: {relative_path}"
    if relative_path.endswith("/context/intake.md"):
        return (
            f"{message}. Intake context is missing; initialize the work item with "
            '`aidd init --work-item <id> --request "..." --root <root>` '
            "or create the required context documents before running a stage."
        )
    return message


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
        f"- Repair brief source: `{workspace_relative_path(workspace_root, repair_brief_path)}`",
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
        relative_path = workspace_relative_path(workspace_root, document_path)
        if not document_path.exists():
            raise FileNotFoundError(_missing_input_document_message(relative_path))
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


def _write_attempt_repair_context(
    *,
    workspace_root: Path,
    execution_state: StageExecutionState,
    repair_context_markdown: str | None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> Path | None:
    if repair_context_markdown is None or not repair_context_markdown.strip():
        return None
    repair_context_path = execution_state.attempt_path / ATTEMPT_REPAIR_CONTEXT_FILENAME
    repair_context_path.write_text(
        repair_context_markdown.rstrip() + "\n",
        encoding="utf-8",
    )
    write_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=execution_state.work_item,
        run_id=execution_state.run_id,
        stage=execution_state.stage,
        attempt_number=execution_state.attempt_number,
        contracts_root=contracts_root,
    )
    return repair_context_path


def _previous_stage_status_before_current_attempt(
    *,
    stage_metadata: StageRunMetadata | None,
) -> str | None:
    if stage_metadata is None:
        return None
    status_history = stage_metadata.status_history
    if len(status_history) < 2:
        return None
    if status_history[-1].status == StageState.EXECUTING.value:
        return status_history[-2].status
    return status_history[-1].status


def _is_repair_context_attempt(
    *,
    execution_state: StageExecutionState,
    stage_metadata: StageRunMetadata | None,
    previous_status: str | None,
) -> bool:
    if execution_state.attempt_number <= 1:
        return False
    if previous_status == StageState.REPAIR_NEEDED.value:
        return True
    if previous_status != StageState.PREPARING.value or stage_metadata is None:
        return False
    if not stage_metadata.repair_history:
        return False
    return any(
        status_change.status == StageState.BLOCKED.value
        for status_change in stage_metadata.status_history
    )


def historical_repair_brief_trace_path(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> Path | None:
    stage_documents_root = workspace_stage_root(
        root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    candidate = stage_documents_root / "repair-brief.md"
    if not candidate.exists():
        return None

    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if metadata is None:
        return None

    relative_candidate = workspace_relative_path(workspace_root, candidate)
    if any(entry.repair_brief_path == relative_candidate for entry in metadata.repair_history):
        return candidate
    return None


def prepare_adapter_invocation(
    *,
    workspace_root: Path,
    preparation_bundle: StagePreparationBundle,
    execution_state: StageExecutionState,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    intervention_request_path: Path | None = None,
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

    stage_documents_root = workspace_stage_root(
        root=workspace_root,
        work_item=execution_state.work_item,
        stage=execution_state.stage,
    )
    candidate_repair_brief_path = stage_documents_root / "repair-brief.md"
    stage_metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=execution_state.work_item,
        run_id=execution_state.run_id,
        stage=execution_state.stage,
    )
    previous_status = _previous_stage_status_before_current_attempt(
        stage_metadata=stage_metadata,
    )
    repair_mode = _is_repair_context_attempt(
        execution_state=execution_state,
        stage_metadata=stage_metadata,
        previous_status=previous_status,
    )
    intervention_mode = intervention_request_path is not None
    if intervention_mode:
        repair_mode = False
    repair_brief_path: Path | None = None
    repair_brief_markdown: str | None = None
    repair_context_markdown: str | None = None
    operator_request_markdown: str | None = None

    if intervention_mode:
        assert intervention_request_path is not None
        if not intervention_request_path.exists():
            raise FileNotFoundError(
                "Operator intervention requires an existing operator request: "
                f"{workspace_relative_path(workspace_root, intervention_request_path)}"
            )
        operator_request_markdown = intervention_request_path.read_text(encoding="utf-8")
        if not operator_request_markdown.strip():
            raise ValueError(
                "Operator intervention requires a non-empty operator request: "
                f"{workspace_relative_path(workspace_root, intervention_request_path)}"
            )
    elif repair_mode:
        repair_brief_path = candidate_repair_brief_path
        if not repair_brief_path.exists():
            raise FileNotFoundError(
                "Repair rerun requires an existing repair brief: "
                f"{workspace_relative_path(workspace_root, repair_brief_path)}"
            )
        repair_brief_markdown = repair_brief_path.read_text(encoding="utf-8")
        if not repair_brief_markdown.strip():
            raise ValueError(
                "Repair rerun requires a non-empty repair brief: "
                f"{workspace_relative_path(workspace_root, repair_brief_path)}"
            )
        repair_context_markdown = _render_repair_context(
            workspace_root=workspace_root,
            attempt_number=execution_state.attempt_number,
            repair_brief_path=repair_brief_path,
            repair_brief_markdown=repair_brief_markdown.strip(),
        )
        _write_attempt_repair_context(
            workspace_root=workspace_root,
            execution_state=execution_state,
            repair_context_markdown=repair_context_markdown,
            contracts_root=contracts_root,
        )
    elif (
        candidate_repair_brief_path.exists()
        and historical_repair_brief_trace_path(
            workspace_root=workspace_root,
            work_item=execution_state.work_item,
            run_id=execution_state.run_id,
            stage=execution_state.stage,
        )
        is None
    ):
        candidate_repair_brief_path.unlink()

    input_bundle_path, input_bundle_markdown = _prepare_attempt_input_bundle(
        workspace_root=workspace_root,
        attempt_path=execution_state.attempt_path,
        expected_input_bundle=preparation_bundle.expected_input_bundle,
    )
    attempt_mode = "intervention" if intervention_mode else "repair" if repair_mode else "initial"
    write_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=execution_state.work_item,
        run_id=execution_state.run_id,
        stage=execution_state.stage,
        attempt_number=execution_state.attempt_number,
        contracts_root=contracts_root,
        attempt_mode=attempt_mode,
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
        repair_brief_markdown=repair_brief_markdown,
        input_bundle_path=input_bundle_path,
        input_bundle_markdown=input_bundle_markdown,
        expected_input_bundle=preparation_bundle.expected_input_bundle,
        expected_output_documents=preparation_bundle.expected_output_documents,
        attempt_mode=attempt_mode,
        operator_request_path=intervention_request_path,
        operator_request_markdown=operator_request_markdown,
    )


def restore_core_owned_repair_brief(
    *,
    invocation_bundle: AdapterInvocationBundle,
    workspace_root: Path | None = None,
) -> Path | None:
    if (
        invocation_bundle.repair_brief_path is None
        or invocation_bundle.repair_brief_markdown is None
    ):
        if (
            workspace_root is None
            or invocation_bundle.repair_mode
            or invocation_bundle.attempt_mode == "intervention"
        ):
            return None
        model_authored_repair_brief_path = (
            workspace_stage_root(
                root=workspace_root,
                work_item=invocation_bundle.work_item,
                stage=invocation_bundle.stage,
            )
            / "repair-brief.md"
        )
        if (
            historical_repair_brief_trace_path(
                workspace_root=workspace_root,
                work_item=invocation_bundle.work_item,
                run_id=invocation_bundle.run_id,
                stage=invocation_bundle.stage,
            )
            is not None
        ):
            return model_authored_repair_brief_path
        if model_authored_repair_brief_path.exists():
            model_authored_repair_brief_path.unlink()
            return model_authored_repair_brief_path
        return None

    current_text = None
    if invocation_bundle.repair_brief_path.exists():
        current_text = invocation_bundle.repair_brief_path.read_text(encoding="utf-8")
    if current_text == invocation_bundle.repair_brief_markdown:
        return invocation_bundle.repair_brief_path

    invocation_bundle.repair_brief_path.parent.mkdir(parents=True, exist_ok=True)
    invocation_bundle.repair_brief_path.write_text(
        invocation_bundle.repair_brief_markdown,
        encoding="utf-8",
    )
    return invocation_bundle.repair_brief_path


__all__ = [
    "ATTEMPT_INPUT_BUNDLE_FILENAME",
    "ATTEMPT_REPAIR_CONTEXT_FILENAME",
    "historical_repair_brief_trace_path",
    "prepare_adapter_invocation",
    "restore_core_owned_repair_brief",
]

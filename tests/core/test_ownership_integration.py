from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aidd.core.run_store import create_run_manifest, persist_stage_status
from aidd.core.stage_registry import resolve_stage_output_registry
from aidd.core.stage_runner import (
    AdapterInvocationBundle,
    StageExecutionState,
    StagePreparationBundle,
    discover_stage_markdown_outputs,
    persist_execution_state,
    prepare_adapter_invocation,
    prepare_stage_bundle,
    publish_stage_outputs_after_validation_pass,
)
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState


def _materialize_documents(paths: tuple[Path, ...], *, label: str) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {label}\n\nPresent for `{path.name}`.\n", encoding="utf-8")


def _prepare_invocation(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_mode: str,
) -> tuple[StagePreparationBundle, StageExecutionState, AdapterInvocationBundle]:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target=stage,
        config_snapshot={"mode": "ownership-integration"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    )
    _materialize_documents(preparation_bundle.expected_input_bundle, label="Input")
    if attempt_mode == "repair":
        persist_execution_state(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_mode="initial",
        )
        repair_brief = (
            workspace_root / "workitems" / work_item / "stages" / stage / "repair-brief.md"
        )
        repair_brief.parent.mkdir(parents=True, exist_ok=True)
        repair_brief.write_text(
            "# Repair brief\n\n- Correct the runtime content.\n", encoding="utf-8"
        )
        persist_stage_status(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            status=StageState.REPAIR_NEEDED.value,
        )
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_mode=attempt_mode,
    )
    operator_request_path: Path | None = None
    if attempt_mode == "intervention":
        operator_request_path = (
            workspace_root
            / "workitems"
            / work_item
            / "stages"
            / stage
            / "operator-requests"
            / "request-1.md"
        )
        operator_request_path.parent.mkdir(parents=True, exist_ok=True)
        operator_request_path.write_text(
            "# Operator Request\n\nClarify the current stage output.\n",
            encoding="utf-8",
        )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
        intervention_request_path=operator_request_path,
    )
    return preparation_bundle, execution_state, invocation


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("attempt_mode", ("initial", "repair", "intervention"))
def test_ownership_matrix_controls_discovery_and_publication_for_every_stage_mode(
    tmp_path: Path,
    stage: str,
    attempt_mode: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-OWNERSHIP-MATRIX"
    run_id = f"run-{stage}-{attempt_mode}"
    registry = resolve_stage_output_registry(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
    )
    preparation_bundle, execution_state, invocation = _prepare_invocation(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_mode=attempt_mode,
    )

    assert invocation.expected_output_documents == registry.runtime_authored
    protected_documents = (*registry.aidd_generated, *registry.interview_control)
    assert set(invocation.expected_output_documents).isdisjoint(protected_documents)

    _materialize_documents(invocation.expected_output_documents, label="Runtime output")
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )
    assert discovery.expected_markdown_documents == registry.runtime_authored
    assert discovery.discovered_markdown_documents == registry.runtime_authored
    assert discovery.missing_markdown_documents == ()

    unsafe_invocation = replace(invocation, expected_output_documents=registry.published)
    with pytest.raises(ValueError, match="AIDD-owned or non-runtime output documents"):
        discover_stage_markdown_outputs(
            execution_state=execution_state,
            invocation_bundle=unsafe_invocation,
        )

    _materialize_documents(registry.published, label="Published output")
    publication = publish_stage_outputs_after_validation_pass(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    assert {path.name for path in publication.published_documents} == {
        path.name for path in registry.published
    }
    assert preparation_bundle.expected_output_documents == registry.published

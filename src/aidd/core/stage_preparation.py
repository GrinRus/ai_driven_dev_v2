from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aidd.core.project_set import ResolvedProjectSet, persist_project_set_context
from aidd.core.run_store import (
    RUN_ATTEMPT_PREFIX,
    create_next_attempt_directory,
    persist_stage_status,
)
from aidd.core.stage_models import StageExecutionState, StagePreparationBundle
from aidd.core.stage_paths import workspace_relative_paths
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    load_stage_manifest,
    resolve_expected_output_documents,
    resolve_required_input_documents,
)
from aidd.core.state_machine import StageState


def render_stage_brief(
    *,
    stage: str,
    purpose: str | None,
    expected_input_bundle: tuple[str, ...],
    expected_output_documents: tuple[str, ...],
    project_set: ResolvedProjectSet | None = None,
    project_set_context_path: str | None = None,
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
    if project_set is not None and project_set_context_path is not None:
        lines.extend(
            [
                "",
                "# Declared project set",
                "",
                f"- Project context: `{project_set_context_path}`",
                "- Project ids: "
                + ", ".join(f"`{project.id}`" for project in project_set.projects),
                "- Stage outputs may cite these project ids when work spans declared roots.",
            ]
        )
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
    project_set: ResolvedProjectSet | None = None,
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
    project_set_context_path: Path | None = None
    if project_set is not None and project_set.projects:
        project_set_context_path = persist_project_set_context(
            workspace_root=workspace_root,
            work_item=work_item,
            project_set=project_set,
        )
        expected_inputs = (*expected_inputs, project_set_context_path)

    stage_brief = render_stage_brief(
        stage=stage,
        purpose=manifest.purpose,
        expected_input_bundle=workspace_relative_paths(workspace_root, expected_inputs),
        expected_output_documents=workspace_relative_paths(workspace_root, expected_outputs),
        project_set=project_set,
        project_set_context_path=(
            None
            if project_set_context_path is None
            else workspace_relative_paths(workspace_root, (project_set_context_path,))[0]
        ),
    )
    return StagePreparationBundle(
        stage=stage,
        work_item=work_item,
        stage_brief_markdown=stage_brief,
        expected_input_bundle=expected_inputs,
        expected_output_documents=expected_outputs,
        project_set_context_path=project_set_context_path,
    )


def attempt_number_from_path(attempt_path: Path) -> int:
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
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    changed_at_utc: datetime | None = None,
) -> StageExecutionState:
    attempt_path = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        contracts_root=contracts_root,
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
        attempt_number=attempt_number_from_path(attempt_path),
        attempt_path=attempt_path,
        stage_metadata_path=stage_metadata_path,
    )


__all__ = [
    "attempt_number_from_path",
    "persist_execution_state",
    "prepare_stage_bundle",
    "render_stage_brief",
]

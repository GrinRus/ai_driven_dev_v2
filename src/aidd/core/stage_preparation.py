from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aidd.core.markdown import extract_required_sections_from_document_contract
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
    resolve_optional_input_documents,
    resolve_required_input_documents,
)
from aidd.core.state_machine import StageState

_STAGE_RESULT_SKELETON = """```md
# Stage Result

## Stage

- Stage: `<canonical-stage-id>`

## Attempt history

- Attempt 1 (`initial`): <outcome and evidence>

## Status

- Status: `<succeeded|failed|blocked|needs-input>`

## Produced outputs

- `<workspace-relative-path>`

## Validation summary

- Validator verdict: `<pass|fail|not-run>`
- Validator report: `workitems/<id>/stages/<stage>/validator-report.md`

## Blockers

- none

## Next actions

- <operator or downstream action>

## Terminal state notes

- <why the stage ended in the declared status>
```"""

_VALIDATOR_REPORT_SKELETON = """```md
# Validator Report

## Summary

- Total issues: `<number>`
- Blocking issues: `<yes|no>`
- Affected documents: `<workspace-relative paths or none>`

## Structural checks

- none

## Semantic checks

- none

## Cross-document checks

- none

## Result

- Validator verdict: `<pass|fail>`
- Repair required: `<yes|no>`
```"""

_COMMON_OUTPUT_SKELETONS = {
    "stage-result.md": _STAGE_RESULT_SKELETON,
    "validator-report.md": _VALIDATOR_REPORT_SKELETON,
}
_SKIPPED_CONTRACT_SKELETONS = {"answers.md", "questions.md"}


class StageInputPreflightError(FileNotFoundError):
    """Raised before attempt creation when required stage inputs are unavailable."""


def _document_title_from_name(document_name: str) -> str:
    words = Path(document_name).stem.split("-")
    return " ".join("QA" if word == "qa" else word.capitalize() for word in words)


def _contract_output_skeleton(
    *,
    document_name: str,
    contracts_root: Path,
) -> str | None:
    if (
        document_name in _COMMON_OUTPUT_SKELETONS
        or document_name in _SKIPPED_CONTRACT_SKELETONS
    ):
        return None

    document_contract_path = contracts_root.parent / "documents" / document_name
    if not document_contract_path.exists():
        return None

    required_sections = extract_required_sections_from_document_contract(
        document_contract_path.read_text(encoding="utf-8")
    )
    if not required_sections:
        return None

    lines = ["```md", f"# {_document_title_from_name(document_name)}", ""]
    for section in required_sections:
        lines.extend((f"## {section}", "", "- <replace with stage-specific content>", ""))
    lines.append("```")
    return "\n".join(lines)


def _append_output_skeletons(
    *,
    lines: list[str],
    expected_output_documents: tuple[str, ...],
    contracts_root: Path,
) -> None:
    expected_names = {Path(path).name for path in expected_output_documents}
    skeletons: list[tuple[str, str]] = []
    for document_name in sorted(expected_names):
        common_skeleton = _COMMON_OUTPUT_SKELETONS.get(document_name)
        if common_skeleton is not None:
            skeletons.append((document_name, common_skeleton))
            continue

        contract_skeleton = _contract_output_skeleton(
            document_name=document_name,
            contracts_root=contracts_root,
        )
        if contract_skeleton is not None:
            skeletons.append((document_name, contract_skeleton))

    if not skeletons:
        return

    lines.extend(
        [
            "",
            "# Required output skeletons",
            "",
            "Use these exact section headings when writing these output documents.",
        ]
    )
    for document_name, skeleton in skeletons:
        lines.extend(["", f"## `{document_name}`", "", skeleton])


def render_stage_brief(
    *,
    stage: str,
    purpose: str | None,
    expected_input_bundle: tuple[str, ...],
    expected_output_documents: tuple[str, ...],
    project_set: ResolvedProjectSet | None = None,
    project_set_context_path: str | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
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
                "- Project roots: "
                + ", ".join(f"`{project.relative_root}`" for project in project_set.projects),
                (
                    "- `stage-result.md` must include a `Project-set evidence` section that "
                    "cites the project context path plus every declared project id and root, "
                    "or marks an unaffected project explicitly."
                ),
            ]
        )
    lines.extend(["", "# Expected output documents", ""])
    lines.extend(f"- `{path}`" for path in expected_output_documents)
    _append_output_skeletons(
        lines=lines,
        expected_output_documents=expected_output_documents,
        contracts_root=contracts_root,
    )
    lines.append("")
    return "\n".join(lines)


def prepare_stage_bundle(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
    project_set: ResolvedProjectSet | None = None,
    include_existing_stage_outputs: bool = False,
    extra_input_documents: tuple[Path, ...] = (),
) -> StagePreparationBundle:
    manifest = load_stage_manifest(stage=stage, contracts_root=contracts_root)
    expected_inputs = resolve_required_input_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    required_inputs = expected_inputs
    optional_inputs = tuple(
        path
        for path in resolve_optional_input_documents(
            stage=stage,
            work_item=work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
        if path.exists()
    )
    expected_inputs = (*expected_inputs, *optional_inputs)
    expected_outputs = resolve_expected_output_documents(
        stage=stage,
        work_item=work_item,
        workspace_root=workspace_root,
        contracts_root=contracts_root,
    )
    if include_existing_stage_outputs:
        existing_outputs = tuple(path for path in expected_outputs if path.exists())
        expected_inputs = (*expected_inputs, *existing_outputs)
    if extra_input_documents:
        seen_inputs = {path.resolve(strict=False) for path in expected_inputs}
        unique_extra_inputs: list[Path] = []
        for path in extra_input_documents:
            resolved = path.resolve(strict=False)
            if resolved in seen_inputs:
                continue
            unique_extra_inputs.append(path)
            seen_inputs.add(resolved)
        expected_inputs = (*expected_inputs, *tuple(unique_extra_inputs))
    project_set_context_path: Path | None = None
    if project_set is not None and project_set.projects:
        project_set_context_path = persist_project_set_context(
            workspace_root=workspace_root,
            work_item=work_item,
            project_set=project_set,
        )
        expected_inputs = (*expected_inputs, project_set_context_path)
        required_inputs = (*required_inputs, project_set_context_path)

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
        contracts_root=contracts_root,
    )
    return StagePreparationBundle(
        stage=stage,
        work_item=work_item,
        stage_brief_markdown=stage_brief,
        required_input_documents=required_inputs,
        optional_input_documents=optional_inputs,
        expected_input_bundle=expected_inputs,
        expected_output_documents=expected_outputs,
        project_set_context_path=project_set_context_path,
    )


def validate_required_stage_inputs(
    *,
    workspace_root: Path,
    preparation_bundle: StagePreparationBundle,
) -> None:
    def _validate_document(document_path: Path, *, input_kind: str) -> None:
        relative_path = workspace_relative_paths(workspace_root, (document_path,))[0]
        if not document_path.exists():
            raise StageInputPreflightError(
                f"Stage input preflight failed: missing {input_kind} input document: "
                f"{relative_path}"
            )
        try:
            document_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise StageInputPreflightError(
                f"Stage input preflight failed: {input_kind} input document is not "
                "UTF-8 text: "
                f"{relative_path}"
            ) from exc
        except OSError as exc:
            raise StageInputPreflightError(
                f"Stage input preflight failed: {input_kind} input document is not readable: "
                f"{relative_path}"
            ) from exc

    for document_path in preparation_bundle.required_input_documents:
        _validate_document(document_path, input_kind="required")
    for document_path in preparation_bundle.optional_input_documents:
        _validate_document(document_path, input_kind="optional")


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
    "StageInputPreflightError",
    "validate_required_stage_inputs",
]

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    load_stage_manifest,
    resolve_expected_output_documents,
    resolve_required_input_documents,
)


@dataclass(frozen=True, slots=True)
class StagePreparationBundle:
    stage: str
    work_item: str
    stage_brief_markdown: str
    expected_input_bundle: tuple[Path, ...]
    expected_output_documents: tuple[Path, ...]


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

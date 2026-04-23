from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from aidd.adapters.base import CapabilityReport
from aidd.adapters.claude_code import probe as probe_claude_code
from aidd.adapters.claude_code.runner import (
    ClaudeCodeCommandContext,
    ClaudeCodeExitClassification,
)
from aidd.adapters.claude_code.runner import (
    build_subprocess_spec as build_claude_code_subprocess_spec,
)
from aidd.adapters.codex import probe as probe_codex
from aidd.adapters.codex.runner import CodexCommandContext, CodexExitClassification
from aidd.adapters.codex.runner import (
    build_subprocess_spec as build_codex_subprocess_spec,
)
from aidd.adapters.generic_cli import probe as probe_generic_cli
from aidd.adapters.generic_cli.runner import (
    GenericCliExitClassification,
    GenericCliStageContext,
)
from aidd.adapters.generic_cli.runner import (
    build_subprocess_spec as build_generic_cli_subprocess_spec,
)
from aidd.adapters.opencode import probe as probe_opencode
from aidd.adapters.opencode.runner import OpenCodeCommandContext, OpenCodeExitClassification
from aidd.adapters.opencode.runner import (
    build_subprocess_spec as build_opencode_subprocess_spec,
)
from aidd.harness.conformance_matrix import (
    RuntimeConformanceMatrix,
    RuntimeConformanceRow,
    load_runtime_conformance_matrix,
)

_CONFORMANCE_PROBE_COMMAND = "aidd-conformance-missing-runtime-binary"
_CONFORMANCE_STAGE = "idea"
_CONFORMANCE_WORK_ITEM = "WI-CONFORMANCE"
_CONFORMANCE_RUN_ID = "run-conformance"


@dataclass(frozen=True)
class RuntimeConformanceResult:
    runtime_id: str
    expected_dimensions: dict[str, str]
    observed_dimensions: dict[str, bool]

    def failed_required_dimensions(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                dimension
                for dimension, expectation in self.expected_dimensions.items()
                if expectation == "required" and not self.observed_dimensions.get(dimension, False)
            )
        )


@dataclass(frozen=True)
class _AdapterConformanceSurface:
    probe: Callable[[str], CapabilityReport]
    build_subprocess_spec: Callable[[Path], Any]
    exit_classification_enum: type[StrEnum]


def _build_generic_cli_spec(workspace_root: Path) -> Any:
    context = GenericCliStageContext(
        stage=_CONFORMANCE_STAGE,
        work_item=_CONFORMANCE_WORK_ITEM,
        run_id=_CONFORMANCE_RUN_ID,
        prompt_pack_path=workspace_root / "prompt-pack.md",
    )
    return build_generic_cli_subprocess_spec(
        configured_command="generic-cli-conformance",
        workspace_root=workspace_root,
        context=context,
        repository_root=workspace_root,
    )


def _build_claude_code_spec(workspace_root: Path) -> Any:
    context = ClaudeCodeCommandContext(
        stage=_CONFORMANCE_STAGE,
        work_item=_CONFORMANCE_WORK_ITEM,
        run_id=_CONFORMANCE_RUN_ID,
        workspace_root=workspace_root,
        stage_brief_path=workspace_root / "stage-brief.md",
        prompt_pack_paths=(workspace_root / "prompt-pack.md",),
    )
    return build_claude_code_subprocess_spec(
        configured_command="claude-code-conformance",
        context=context,
        repository_root=workspace_root,
    )


def _build_codex_spec(workspace_root: Path) -> Any:
    context = CodexCommandContext(
        stage=_CONFORMANCE_STAGE,
        work_item=_CONFORMANCE_WORK_ITEM,
        run_id=_CONFORMANCE_RUN_ID,
        workspace_root=workspace_root,
        stage_brief_path=workspace_root / "stage-brief.md",
        prompt_pack_paths=(workspace_root / "prompt-pack.md",),
    )
    return build_codex_subprocess_spec(
        configured_command="codex-conformance",
        context=context,
        repository_root=workspace_root,
    )


def _build_opencode_spec(workspace_root: Path) -> Any:
    context = OpenCodeCommandContext(
        stage=_CONFORMANCE_STAGE,
        work_item=_CONFORMANCE_WORK_ITEM,
        run_id=_CONFORMANCE_RUN_ID,
        workspace_root=workspace_root,
        stage_brief_path=workspace_root / "stage-brief.md",
        prompt_pack_paths=(workspace_root / "prompt-pack.md",),
    )
    return build_opencode_subprocess_spec(
        configured_command="opencode-conformance",
        context=context,
        repository_root=workspace_root,
    )


_ADAPTER_CONFORMANCE_SURFACES: dict[str, _AdapterConformanceSurface] = {
    "generic-cli": _AdapterConformanceSurface(
        probe=probe_generic_cli,
        build_subprocess_spec=_build_generic_cli_spec,
        exit_classification_enum=GenericCliExitClassification,
    ),
    "claude-code": _AdapterConformanceSurface(
        probe=probe_claude_code,
        build_subprocess_spec=_build_claude_code_spec,
        exit_classification_enum=ClaudeCodeExitClassification,
    ),
    "codex": _AdapterConformanceSurface(
        probe=probe_codex,
        build_subprocess_spec=_build_codex_spec,
        exit_classification_enum=CodexExitClassification,
    ),
    "opencode": _AdapterConformanceSurface(
        probe=probe_opencode,
        build_subprocess_spec=_build_opencode_spec,
        exit_classification_enum=OpenCodeExitClassification,
    ),
}


def evaluate_runtime_conformance_row(
    *,
    row: RuntimeConformanceRow,
    workspace_root: Path,
) -> RuntimeConformanceResult:
    surface = _ADAPTER_CONFORMANCE_SURFACES.get(row.runtime_id)
    if surface is None:
        raise ValueError(f"No adapter-conformance surface registered for runtime: {row.runtime_id}")

    observed_dimensions = _collect_observed_dimensions(
        runtime_id=row.runtime_id,
        surface=surface,
        workspace_root=workspace_root.resolve(strict=False),
    )
    unknown_dimensions = sorted(set(row.dimensions) - set(observed_dimensions))
    if unknown_dimensions:
        raise ValueError(
            "Conformance matrix references unsupported dimensions for runtime "
            f"{row.runtime_id}: {', '.join(unknown_dimensions)}"
        )

    return RuntimeConformanceResult(
        runtime_id=row.runtime_id,
        expected_dimensions=dict(row.dimensions),
        observed_dimensions={
            dimension: observed_dimensions[dimension]
            for dimension in row.dimensions
        },
    )


def evaluate_conformance_matrix(
    *,
    matrix_path: Path,
    workspace_root: Path,
) -> tuple[RuntimeConformanceResult, ...]:
    matrix = load_runtime_conformance_matrix(matrix_path)
    return evaluate_conformance_matrix_model(matrix=matrix, workspace_root=workspace_root)


def evaluate_conformance_matrix_model(
    *,
    matrix: RuntimeConformanceMatrix,
    workspace_root: Path,
) -> tuple[RuntimeConformanceResult, ...]:
    resolved_workspace_root = workspace_root.resolve(strict=False)
    return tuple(
        evaluate_runtime_conformance_row(row=row, workspace_root=resolved_workspace_root)
        for row in matrix.rows
    )


def _collect_observed_dimensions(
    *,
    runtime_id: str,
    surface: _AdapterConformanceSurface,
    workspace_root: Path,
) -> dict[str, bool]:
    report = surface.probe(_CONFORMANCE_PROBE_COMMAND)
    subprocess_spec = surface.build_subprocess_spec(workspace_root)
    workspace_root_text = workspace_root.as_posix()

    return {
        "probe_behavior": (
            report.runtime_id == runtime_id
            and isinstance(report.available, bool)
            and bool(report.command.strip())
        ),
        "capability_declaration": _has_capability_boolean_fields(report),
        "raw_log_capture": isinstance(report.supports_raw_log_stream, bool),
        "failure_mapping": _has_failure_mapping_members(surface.exit_classification_enum),
        "question_surfacing": isinstance(report.supports_questions, bool),
        "timeout_behavior": "TIMEOUT" in surface.exit_classification_enum.__members__,
        "workspace_targeting": (
            getattr(subprocess_spec, "cwd", None) == workspace_root
            and isinstance(getattr(subprocess_spec, "env", None), dict)
            and getattr(subprocess_spec, "env", {}).get("AIDD_WORKSPACE_ROOT")
            == workspace_root_text
        ),
    }


def _has_capability_boolean_fields(report: CapabilityReport) -> bool:
    flags = (
        report.supports_raw_log_stream,
        report.supports_structured_log_stream,
        report.supports_questions,
        report.supports_resume,
        report.supports_subagents,
        report.supports_non_interactive_mode,
        report.supports_working_directory_control,
        report.supports_env_injection,
    )
    return all(isinstance(flag, bool) for flag in flags)


def _has_failure_mapping_members(exit_enum: type[StrEnum]) -> bool:
    enum_members = exit_enum.__members__
    return "SUCCESS" in enum_members and "TIMEOUT" in enum_members and len(enum_members) >= 3

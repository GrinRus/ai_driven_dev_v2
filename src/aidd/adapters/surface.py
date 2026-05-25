from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from aidd.adapters.base import CapabilityReport
from aidd.adapters.claude_code import probe as probe_claude_code
from aidd.adapters.claude_code.runner import (
    ClaudeCodeCommandContext,
    ClaudeCodeExitClassification,
)
from aidd.adapters.claude_code.runner import (
    build_subprocess_spec as build_claude_code_subprocess_spec,
)
from aidd.adapters.claude_code.runner import (
    persist_attempt_runtime_log as persist_claude_code_runtime_log,
)
from aidd.adapters.claude_code.runner import (
    run_subprocess_with_streaming as run_claude_code_subprocess_with_streaming,
)
from aidd.adapters.codex import probe as probe_codex
from aidd.adapters.codex.runner import CodexCommandContext, CodexExitClassification
from aidd.adapters.codex.runner import build_subprocess_spec as build_codex_subprocess_spec
from aidd.adapters.codex.runner import persist_attempt_runtime_log as persist_codex_runtime_log
from aidd.adapters.codex.runner import (
    run_subprocess_with_streaming as run_codex_subprocess_with_streaming,
)
from aidd.adapters.generic_cli import probe as probe_generic_cli
from aidd.adapters.generic_cli.runner import (
    GenericCliExitClassification,
    GenericCliStageContext,
)
from aidd.adapters.generic_cli.runner import build_subprocess_spec as build_generic_cli_spec
from aidd.adapters.generic_cli.runner import (
    persist_attempt_runtime_artifacts as persist_generic_cli_runtime_artifacts,
)
from aidd.adapters.generic_cli.runner import (
    run_subprocess_with_streaming as run_generic_cli_subprocess_with_streaming,
)
from aidd.adapters.opencode import probe as probe_opencode
from aidd.adapters.opencode.runner import OpenCodeCommandContext, OpenCodeExitClassification
from aidd.adapters.opencode.runner import build_subprocess_spec as build_opencode_subprocess_spec
from aidd.adapters.opencode.runner import (
    persist_attempt_runtime_log as persist_opencode_runtime_log,
)
from aidd.adapters.opencode.runner import (
    run_subprocess_with_streaming as run_opencode_subprocess_with_streaming,
)
from aidd.adapters.runtime_events import (
    detect_question_or_pause_events,
    normalize_structured_events,
    persist_adapter_question_events,
    persist_runtime_event_artifacts,
)
from aidd.adapters.runtime_execution import StageRuntimeRequest
from aidd.adapters.runtime_registry import RuntimeExecutionMode, runtime_ids

_CONFORMANCE_STAGE = "idea"
_CONFORMANCE_WORK_ITEM = "WI-CONFORMANCE"
_CONFORMANCE_RUN_ID = "run-conformance"

StageRequestExecutor = Callable[..., "RuntimeAdapterExecutionResult"]
ConformanceSpecBuilder = Callable[[Path], object]


@dataclass(frozen=True, slots=True)
class RuntimeAdapterExecutionResult:
    succeeded: bool
    details: str
    runtime_jsonl_path: Path | None = None
    events_jsonl_path: Path | None = None
    questions_path: Path | None = None


@dataclass(frozen=True, slots=True)
class RuntimeAdapterSurface:
    runtime_id: str
    probe: Callable[[str], CapabilityReport]
    exit_classification_enum: type[StrEnum]
    success_value: StrEnum
    execute_stage_request_fn: StageRequestExecutor
    conformance_spec_builder: ConformanceSpecBuilder
    default_execution_mode: RuntimeExecutionMode

    def execute_stage_request(
        self,
        *,
        configured_command: str,
        request: StageRuntimeRequest,
        attempt_path: Path,
        base_env: Mapping[str, str],
        on_stdout: Callable[[str], None] | None = None,
        on_stderr: Callable[[str], None] | None = None,
    ) -> RuntimeAdapterExecutionResult:
        return self.execute_stage_request_fn(
            configured_command=configured_command,
            request=request,
            attempt_path=attempt_path,
            base_env=base_env,
            on_stdout=on_stdout,
            on_stderr=on_stderr,
        )

    def build_conformance_subprocess_spec(self, workspace_root: Path) -> object:
        return self.conformance_spec_builder(workspace_root)


def _success_result(exit_classification: StrEnum, success_value: StrEnum) -> bool:
    return exit_classification is success_value


def _build_generic_cli_conformance_spec(workspace_root: Path) -> object:
    generic_context = GenericCliStageContext(
        stage=_CONFORMANCE_STAGE,
        work_item=_CONFORMANCE_WORK_ITEM,
        run_id=_CONFORMANCE_RUN_ID,
        prompt_pack_path=workspace_root / "prompt-pack.md",
    )
    return build_generic_cli_spec(
        configured_command="generic-cli-conformance",
        workspace_root=workspace_root,
        context=generic_context,
        repository_root=workspace_root,
    )


def _build_claude_code_conformance_spec(workspace_root: Path) -> object:
    claude_context = ClaudeCodeCommandContext(
        stage=_CONFORMANCE_STAGE,
        work_item=_CONFORMANCE_WORK_ITEM,
        run_id=_CONFORMANCE_RUN_ID,
        workspace_root=workspace_root,
        stage_brief_path=workspace_root / "stage-brief.md",
        prompt_pack_paths=(workspace_root / "prompt-pack.md",),
    )
    return build_claude_code_subprocess_spec(
        configured_command="claude-code-conformance",
        context=claude_context,
        repository_root=workspace_root,
    )


def _build_codex_conformance_spec(workspace_root: Path) -> object:
    codex_context = CodexCommandContext(
        stage=_CONFORMANCE_STAGE,
        work_item=_CONFORMANCE_WORK_ITEM,
        run_id=_CONFORMANCE_RUN_ID,
        workspace_root=workspace_root,
        stage_brief_path=workspace_root / "stage-brief.md",
        prompt_pack_paths=(workspace_root / "prompt-pack.md",),
    )
    return build_codex_subprocess_spec(
        configured_command="codex-conformance",
        context=codex_context,
        repository_root=workspace_root,
    )


def _build_opencode_conformance_spec(workspace_root: Path) -> object:
    opencode_context = OpenCodeCommandContext(
        stage=_CONFORMANCE_STAGE,
        work_item=_CONFORMANCE_WORK_ITEM,
        run_id=_CONFORMANCE_RUN_ID,
        workspace_root=workspace_root,
        stage_brief_path=workspace_root / "stage-brief.md",
        prompt_pack_paths=(workspace_root / "prompt-pack.md",),
    )
    return build_opencode_subprocess_spec(
        configured_command="opencode-conformance",
        context=opencode_context,
        repository_root=workspace_root,
    )


def _execute_generic_cli(
    *,
    configured_command: str,
    request: StageRuntimeRequest,
    attempt_path: Path,
    base_env: Mapping[str, str],
    on_stdout: Callable[[str], None] | None,
    on_stderr: Callable[[str], None] | None,
) -> RuntimeAdapterExecutionResult:
    prompt_pack_path = request.prompt_pack_paths[0]
    context = GenericCliStageContext(
        stage=request.stage,
        work_item=request.work_item,
        run_id=request.run_id,
        prompt_pack_path=prompt_pack_path,
        attempt_number=request.attempt_number,
        attempt_mode=request.attempt_mode,
        repair_mode=request.repair_mode,
        input_bundle_path=request.input_bundle_path,
        repair_brief_path=request.repair_brief_path,
        operator_request_path=request.operator_request_path,
    )
    spec = build_generic_cli_spec(
        configured_command=configured_command,
        workspace_root=request.workspace_root,
        context=context,
        base_env=base_env,
        repository_root=request.repository_root,
    )
    run_result = run_generic_cli_subprocess_with_streaming(
        spec=spec,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
        timeout_seconds=request.timeout_seconds,
    )
    persist_generic_cli_runtime_artifacts(attempt_path=attempt_path, run_result=run_result)
    return RuntimeAdapterExecutionResult(
        succeeded=_success_result(
            run_result.exit_classification,
            GenericCliExitClassification.SUCCESS,
        ),
        details=run_result.exit_classification.value,
    )


def _execute_claude_code(
    *,
    configured_command: str,
    request: StageRuntimeRequest,
    attempt_path: Path,
    base_env: Mapping[str, str],
    on_stdout: Callable[[str], None] | None,
    on_stderr: Callable[[str], None] | None,
) -> RuntimeAdapterExecutionResult:
    context = ClaudeCodeCommandContext(
        stage=request.stage,
        work_item=request.work_item,
        run_id=request.run_id,
        workspace_root=request.workspace_root,
        stage_brief_path=request.stage_brief_path,
        prompt_pack_paths=request.prompt_pack_paths,
        attempt_number=request.attempt_number,
        attempt_mode=request.attempt_mode,
        repair_mode=request.repair_mode,
        input_bundle_path=request.input_bundle_path,
        repair_brief_path=request.repair_brief_path,
        repair_context_markdown=request.repair_context_markdown,
        operator_request_path=request.operator_request_path,
        operator_request_markdown=request.operator_request_markdown,
    )
    spec = build_claude_code_subprocess_spec(
        configured_command=configured_command,
        context=context,
        base_env=base_env,
        repository_root=request.repository_root,
        execution_mode=request.execution_mode,
    )
    run_result = run_claude_code_subprocess_with_streaming(
        spec=spec,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
        timeout_seconds=request.timeout_seconds,
    )
    persist_claude_code_runtime_log(attempt_path=attempt_path, run_result=run_result)
    event_artifacts = persist_runtime_event_artifacts(
        attempt_path=attempt_path,
        run_result=run_result,
    )
    question_detection = detect_question_or_pause_events(
        normalized_events=normalize_structured_events(run_result=run_result),
    )
    questions_path = persist_adapter_question_events(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        stage=request.stage,
        adapter_question_events=question_detection.question_events,
    )
    return RuntimeAdapterExecutionResult(
        succeeded=_success_result(
            run_result.exit_classification,
            ClaudeCodeExitClassification.SUCCESS,
        ),
        details=run_result.exit_classification.value,
        runtime_jsonl_path=event_artifacts.runtime_jsonl_path,
        events_jsonl_path=event_artifacts.events_jsonl_path,
        questions_path=questions_path,
    )


def _execute_codex(
    *,
    configured_command: str,
    request: StageRuntimeRequest,
    attempt_path: Path,
    base_env: Mapping[str, str],
    on_stdout: Callable[[str], None] | None,
    on_stderr: Callable[[str], None] | None,
) -> RuntimeAdapterExecutionResult:
    context = CodexCommandContext(
        stage=request.stage,
        work_item=request.work_item,
        run_id=request.run_id,
        workspace_root=request.workspace_root,
        stage_brief_path=request.stage_brief_path,
        prompt_pack_paths=request.prompt_pack_paths,
        attempt_number=request.attempt_number,
        attempt_mode=request.attempt_mode,
        repair_mode=request.repair_mode,
        input_bundle_path=request.input_bundle_path,
        repair_brief_path=request.repair_brief_path,
        repair_context_markdown=request.repair_context_markdown,
        operator_request_path=request.operator_request_path,
        operator_request_markdown=request.operator_request_markdown,
    )
    spec = build_codex_subprocess_spec(
        configured_command=configured_command,
        context=context,
        base_env=base_env,
        repository_root=request.repository_root,
        execution_mode=request.execution_mode,
    )
    run_result = run_codex_subprocess_with_streaming(
        spec=spec,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
        timeout_seconds=request.timeout_seconds,
    )
    persist_codex_runtime_log(attempt_path=attempt_path, run_result=run_result)
    event_artifacts = persist_runtime_event_artifacts(
        attempt_path=attempt_path,
        run_result=run_result,
    )
    question_detection = detect_question_or_pause_events(
        normalized_events=normalize_structured_events(run_result=run_result),
    )
    questions_path = persist_adapter_question_events(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        stage=request.stage,
        adapter_question_events=question_detection.question_events,
    )
    return RuntimeAdapterExecutionResult(
        succeeded=_success_result(run_result.exit_classification, CodexExitClassification.SUCCESS),
        details=run_result.exit_classification.value,
        runtime_jsonl_path=event_artifacts.runtime_jsonl_path,
        events_jsonl_path=event_artifacts.events_jsonl_path,
        questions_path=questions_path,
    )


def _execute_opencode(
    *,
    configured_command: str,
    request: StageRuntimeRequest,
    attempt_path: Path,
    base_env: Mapping[str, str],
    on_stdout: Callable[[str], None] | None,
    on_stderr: Callable[[str], None] | None,
) -> RuntimeAdapterExecutionResult:
    context = OpenCodeCommandContext(
        stage=request.stage,
        work_item=request.work_item,
        run_id=request.run_id,
        workspace_root=request.workspace_root,
        stage_brief_path=request.stage_brief_path,
        prompt_pack_paths=request.prompt_pack_paths,
        attempt_number=request.attempt_number,
        attempt_mode=request.attempt_mode,
        repair_mode=request.repair_mode,
        input_bundle_path=request.input_bundle_path,
        repair_brief_path=request.repair_brief_path,
        repair_context_markdown=request.repair_context_markdown,
        operator_request_path=request.operator_request_path,
        operator_request_markdown=request.operator_request_markdown,
    )
    spec = build_opencode_subprocess_spec(
        configured_command=configured_command,
        context=context,
        base_env=base_env,
        repository_root=request.repository_root,
        execution_mode=request.execution_mode,
    )
    run_result = run_opencode_subprocess_with_streaming(
        spec=spec,
        on_stdout=on_stdout,
        on_stderr=on_stderr,
        timeout_seconds=request.timeout_seconds,
        document_completion_paths=request.expected_output_documents,
    )
    persist_opencode_runtime_log(attempt_path=attempt_path, run_result=run_result)
    event_artifacts = persist_runtime_event_artifacts(
        attempt_path=attempt_path,
        run_result=run_result,
    )
    question_detection = detect_question_or_pause_events(
        normalized_events=normalize_structured_events(run_result=run_result),
    )
    questions_path = persist_adapter_question_events(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        stage=request.stage,
        adapter_question_events=question_detection.question_events,
    )
    return RuntimeAdapterExecutionResult(
        succeeded=run_result.exit_classification
        in (
            OpenCodeExitClassification.SUCCESS,
            OpenCodeExitClassification.DOCUMENT_COMPLETE,
        ),
        details=run_result.exit_classification.value,
        runtime_jsonl_path=event_artifacts.runtime_jsonl_path,
        events_jsonl_path=event_artifacts.events_jsonl_path,
        questions_path=questions_path,
    )


_SURFACES_BY_RUNTIME: dict[str, RuntimeAdapterSurface] = {
    "generic-cli": RuntimeAdapterSurface(
        runtime_id="generic-cli",
        probe=probe_generic_cli,
        exit_classification_enum=GenericCliExitClassification,
        success_value=GenericCliExitClassification.SUCCESS,
        execute_stage_request_fn=_execute_generic_cli,
        conformance_spec_builder=_build_generic_cli_conformance_spec,
        default_execution_mode=RuntimeExecutionMode.ADAPTER_FLAGS,
    ),
    "claude-code": RuntimeAdapterSurface(
        runtime_id="claude-code",
        probe=probe_claude_code,
        exit_classification_enum=ClaudeCodeExitClassification,
        success_value=ClaudeCodeExitClassification.SUCCESS,
        execute_stage_request_fn=_execute_claude_code,
        conformance_spec_builder=_build_claude_code_conformance_spec,
        default_execution_mode=RuntimeExecutionMode.NATIVE,
    ),
    "codex": RuntimeAdapterSurface(
        runtime_id="codex",
        probe=probe_codex,
        exit_classification_enum=CodexExitClassification,
        success_value=CodexExitClassification.SUCCESS,
        execute_stage_request_fn=_execute_codex,
        conformance_spec_builder=_build_codex_conformance_spec,
        default_execution_mode=RuntimeExecutionMode.NATIVE,
    ),
    "opencode": RuntimeAdapterSurface(
        runtime_id="opencode",
        probe=probe_opencode,
        exit_classification_enum=OpenCodeExitClassification,
        success_value=OpenCodeExitClassification.SUCCESS,
        execute_stage_request_fn=_execute_opencode,
        conformance_spec_builder=_build_opencode_conformance_spec,
        default_execution_mode=RuntimeExecutionMode.NATIVE,
    ),
}
RUNTIME_ADAPTER_SURFACES: dict[str, RuntimeAdapterSurface] = {
    runtime_id: _SURFACES_BY_RUNTIME[runtime_id] for runtime_id in runtime_ids()
}


def get_runtime_adapter_surface(runtime_id: str) -> RuntimeAdapterSurface:
    try:
        return RUNTIME_ADAPTER_SURFACES[runtime_id]
    except KeyError as exc:
        supported = ", ".join(RUNTIME_ADAPTER_SURFACES)
        raise ValueError(f"Unsupported runtime id: {runtime_id}. Supported: {supported}.") from exc


def runtime_adapter_surfaces() -> tuple[RuntimeAdapterSurface, ...]:
    return tuple(RUNTIME_ADAPTER_SURFACES.values())


def runtime_adapter_surface_ids() -> tuple[str, ...]:
    return tuple(RUNTIME_ADAPTER_SURFACES)


def default_execution_mode_for_surface(surface: RuntimeAdapterSurface) -> RuntimeExecutionMode:
    return surface.default_execution_mode

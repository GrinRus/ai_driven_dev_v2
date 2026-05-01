from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from aidd.adapters.runtime_registry import RuntimeExecutionMode

ExitClassificationT = TypeVar("ExitClassificationT")


@dataclass(frozen=True, slots=True)
class StageRuntimeRequest:
    runtime_id: str
    execution_mode: RuntimeExecutionMode
    timeout_seconds: float | None
    stage: str
    work_item: str
    run_id: str
    workspace_root: Path
    stage_brief_path: Path
    prompt_pack_paths: tuple[Path, ...]
    repository_root: Path
    attempt_number: int = 1
    repair_mode: bool = False
    input_bundle_path: Path | None = None
    repair_brief_path: Path | None = None
    repair_context_markdown: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeSubprocessSpec:
    command: tuple[str, ...]
    cwd: Path
    env: dict[str, str]
    stdin_text: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeRunResult[ExitClassificationT]:
    exit_code: int
    stdout_text: str
    stderr_text: str
    runtime_log_text: str
    exit_classification: ExitClassificationT

    @property
    def stdout(self) -> str:
        return self.stdout_text

    @property
    def stderr(self) -> str:
        return self.stderr_text

    @property
    def runtime_log(self) -> str:
        return self.runtime_log_text

    @property
    def normalized_exit_classification(self) -> ExitClassificationT:
        return self.exit_classification

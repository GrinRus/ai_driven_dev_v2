from __future__ import annotations

import shlex
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from aidd.harness.process_lifecycle import HarnessLifecycleBudget, run_owned_process
from aidd.harness.runner import HarnessCommandTranscript
from aidd.harness.scenarios import ScenarioAuthoredTask

DEFAULT_TARGET_READINESS_TIMEOUT_SECONDS = 10 * 60.0

_AIDD_ARTIFACT_MARKERS = (
    ".aidd/",
    "stage-result.md",
    "validator-report.md",
    "quality-report.md",
)


class LiveTargetReadinessError(RuntimeError):
    def __init__(self, message: str, *, result: LiveTargetReadinessResult) -> None:
        super().__init__(message)
        self.result = result
        self.command_transcripts = result.command_transcripts


@dataclass(frozen=True, slots=True)
class TargetCommandPrerequisite:
    command: str
    path: str
    exists: bool
    executable: bool


@dataclass(frozen=True, slots=True)
class LiveTargetReadinessResult:
    schema_version: int
    classification: str
    timeout_seconds: float
    authored_commands: tuple[str, ...]
    smoke_commands: tuple[str, ...]
    deferred_artifact_commands: tuple[str, ...]
    prerequisites: tuple[TargetCommandPrerequisite, ...]
    command_transcripts: tuple[HarnessCommandTranscript, ...]
    failure_reason: str | None

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


def _is_post_stage_artifact_check(command: str) -> bool:
    normalized = command.replace("\\", "/").lower()
    return any(marker in normalized for marker in _AIDD_ARTIFACT_MARKERS)


def select_target_readiness_commands(
    task: ScenarioAuthoredTask,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    smoke: list[str] = []
    deferred: list[str] = []
    for command in task.verification:
        if _is_post_stage_artifact_check(command):
            deferred.append(command)
        else:
            smoke.append(command)
    return tuple(smoke), tuple(deferred)


def _command_prerequisite(
    command: str,
    *,
    working_copy_path: Path,
) -> TargetCommandPrerequisite | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if not tokens:
        return None
    executable = tokens[0]
    candidate = Path(executable)
    if candidate.is_absolute() or "/" not in executable:
        return None
    resolved = (working_copy_path / candidate).resolve(strict=False)
    try:
        resolved.relative_to(working_copy_path.resolve(strict=False))
    except ValueError:
        return TargetCommandPrerequisite(
            command=command,
            path=resolved.as_posix(),
            exists=False,
            executable=False,
        )
    return TargetCommandPrerequisite(
        command=command,
        path=resolved.as_posix(),
        exists=resolved.is_file(),
        executable=resolved.is_file() and resolved.stat().st_mode & 0o111 != 0,
    )


def run_live_target_readiness(
    *,
    task: ScenarioAuthoredTask,
    working_copy_path: Path,
    environment: Mapping[str, str],
    timeout_seconds: float = DEFAULT_TARGET_READINESS_TIMEOUT_SECONDS,
) -> LiveTargetReadinessResult:
    if timeout_seconds <= 0:
        raise ValueError("Target readiness timeout must be greater than zero.")
    if not working_copy_path.is_dir():
        raise ValueError("Target readiness requires an existing working copy.")
    smoke_commands, deferred_commands = select_target_readiness_commands(task)
    prerequisites = tuple(
        prerequisite
        for command in smoke_commands
        if (
            prerequisite := _command_prerequisite(
                command,
                working_copy_path=working_copy_path,
            )
        )
        is not None
    )
    missing = tuple(
        prerequisite
        for prerequisite in prerequisites
        if not prerequisite.exists or not prerequisite.executable
    )
    if not smoke_commands:
        result = LiveTargetReadinessResult(
            schema_version=1,
            classification="target-setup",
            timeout_seconds=timeout_seconds,
            authored_commands=task.verification,
            smoke_commands=tuple(),
            deferred_artifact_commands=deferred_commands,
            prerequisites=prerequisites,
            command_transcripts=tuple(),
            failure_reason="Authored task has no provider-free verification smoke command.",
        )
        raise LiveTargetReadinessError(result.failure_reason or "", result=result)
    if missing:
        paths = ", ".join(item.path for item in missing)
        result = LiveTargetReadinessResult(
            schema_version=1,
            classification="target-setup",
            timeout_seconds=timeout_seconds,
            authored_commands=task.verification,
            smoke_commands=smoke_commands,
            deferred_artifact_commands=deferred_commands,
            prerequisites=prerequisites,
            command_transcripts=tuple(),
            failure_reason=f"Target command prerequisite is unavailable: {paths}",
        )
        raise LiveTargetReadinessError(result.failure_reason or "", result=result)

    budget = HarnessLifecycleBudget.start(timeout_seconds)
    transcripts: list[HarnessCommandTranscript] = []
    for command in smoke_commands:
        remaining = budget.remaining_seconds()
        completed = run_owned_process(
            command=("/bin/sh", "-c", command),
            cwd=working_copy_path,
            environment=dict(environment),
            timeout_seconds=remaining,
        )
        transcript = HarnessCommandTranscript(
            command=command,
            exit_code=completed.exit_code,
            stdout_text=completed.stdout_text,
            stderr_text=completed.stderr_text,
            duration_seconds=completed.duration_seconds,
            timed_out=completed.timed_out,
            timeout_seconds=completed.timeout_seconds,
        )
        transcripts.append(transcript)
        if completed.exit_code != 0:
            detail = (
                completed.stderr_text.strip()
                or completed.stdout_text.strip()
                or "no command output"
            )
            result = LiveTargetReadinessResult(
                schema_version=1,
                classification="target-setup",
                timeout_seconds=timeout_seconds,
                authored_commands=task.verification,
                smoke_commands=smoke_commands,
                deferred_artifact_commands=deferred_commands,
                prerequisites=prerequisites,
                command_transcripts=tuple(transcripts),
                failure_reason=(
                    f"Target readiness command failed ({completed.exit_code}): "
                    f"{command}\n{detail}"
                ),
            )
            raise LiveTargetReadinessError(result.failure_reason or "", result=result)

    return LiveTargetReadinessResult(
        schema_version=1,
        classification="pass",
        timeout_seconds=timeout_seconds,
        authored_commands=task.verification,
        smoke_commands=smoke_commands,
        deferred_artifact_commands=deferred_commands,
        prerequisites=prerequisites,
        command_transcripts=tuple(transcripts),
        failure_reason=None,
    )


__all__ = [
    "DEFAULT_TARGET_READINESS_TIMEOUT_SECONDS",
    "LiveTargetReadinessError",
    "LiveTargetReadinessResult",
    "TargetCommandPrerequisite",
    "run_live_target_readiness",
    "select_target_readiness_commands",
]

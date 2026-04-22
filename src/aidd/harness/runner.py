from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from aidd.harness.scenarios import Scenario


class HarnessSetupError(RuntimeError):
    """Raised when a setup command fails."""


class HarnessVerificationError(RuntimeError):
    """Raised when a verification command fails."""


class HarnessTeardownError(RuntimeError):
    """Raised when a teardown command fails."""


@dataclass(frozen=True, slots=True)
class HarnessCommandTranscript:
    command: str
    exit_code: int
    stdout_text: str
    stderr_text: str
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class HarnessSetupResult:
    executed_commands: tuple[str, ...]
    command_transcripts: tuple[HarnessCommandTranscript, ...]
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class HarnessAiddRunResult:
    command: tuple[str, ...]
    runtime_id: str
    work_item: str
    exit_code: int
    stdout_text: str
    stderr_text: str
    duration_seconds: float
    command_transcript: HarnessCommandTranscript


@dataclass(frozen=True, slots=True)
class HarnessVerificationResult:
    executed_commands: tuple[str, ...]
    aidd_exit_code: int
    command_transcripts: tuple[HarnessCommandTranscript, ...]
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class HarnessTeardownResult:
    executed_commands: tuple[str, ...]
    command_transcripts: tuple[HarnessCommandTranscript, ...]
    duration_seconds: float


def _validate_working_copy_path(working_copy_path: Path) -> None:
    if not working_copy_path.exists() or not working_copy_path.is_dir():
        raise ValueError(
            f"Working copy path must be an existing directory: {working_copy_path.as_posix()}"
        )


def _run_shell_commands(
    *,
    commands: tuple[str, ...],
    working_copy_path: Path,
    command_env: Mapping[str, str],
    error_label: str,
    error_type: type[RuntimeError],
) -> tuple[HarnessCommandTranscript, ...]:
    command_transcripts: list[HarnessCommandTranscript] = []
    for command in commands:
        start = time.monotonic()
        completed = subprocess.run(
            ["/bin/sh", "-lc", command],
            cwd=working_copy_path,
            env=command_env,
            capture_output=True,
            text=True,
            check=False,
        )
        duration_seconds = time.monotonic() - start
        transcript = HarnessCommandTranscript(
            command=command,
            exit_code=completed.returncode,
            stdout_text=completed.stdout,
            stderr_text=completed.stderr,
            duration_seconds=duration_seconds,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip() or "no command output"
            raise error_type(
                f"{error_label} command failed with non-zero exit "
                f"({completed.returncode}): {command}\n{stderr}"
            )
        command_transcripts.append(transcript)
    return tuple(command_transcripts)


def run_setup_steps(
    *,
    scenario: Scenario,
    working_copy_path: Path,
    environment: Mapping[str, str] | None = None,
) -> HarnessSetupResult:
    _validate_working_copy_path(working_copy_path)

    command_env = dict(os.environ)
    if environment is not None:
        command_env.update(environment)

    command_transcripts = _run_shell_commands(
        commands=scenario.setup.commands,
        working_copy_path=working_copy_path,
        command_env=command_env,
        error_label="Setup",
        error_type=HarnessSetupError,
    )
    return HarnessSetupResult(
        executed_commands=tuple(transcript.command for transcript in command_transcripts),
        command_transcripts=command_transcripts,
        duration_seconds=sum(transcript.duration_seconds for transcript in command_transcripts),
    )


def invoke_aidd_run(
    *,
    scenario: Scenario,
    working_copy_path: Path,
    runtime_id: str,
    work_item: str,
    aidd_command: tuple[str, ...] = ("uv", "run", "aidd"),
    environment: Mapping[str, str] | None = None,
) -> HarnessAiddRunResult:
    _validate_working_copy_path(working_copy_path)
    if runtime_id not in scenario.runtime_targets:
        supported = ", ".join(scenario.runtime_targets)
        raise ValueError(
            f"Runtime '{runtime_id}' is not allowed by scenario '{scenario.scenario_id}'. "
            f"Supported runtime targets: {supported}."
        )
    if not work_item.strip():
        raise ValueError("work_item must be non-empty.")
    if not aidd_command:
        raise ValueError("aidd_command must contain at least one token.")

    command = (*aidd_command, "run", "--work-item", work_item, "--runtime", runtime_id)
    command_env = dict(os.environ)
    command_env.update(
        {
            "AIDD_HARNESS_SCENARIO_ID": scenario.scenario_id,
            "AIDD_HARNESS_RUNTIME_ID": runtime_id,
            "AIDD_HARNESS_WORK_ITEM": work_item,
        }
    )
    if environment is not None:
        command_env.update(environment)

    start = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=working_copy_path,
        env=command_env,
        capture_output=True,
        text=True,
        check=False,
    )
    duration_seconds = time.monotonic() - start
    command_transcript = HarnessCommandTranscript(
        command=" ".join(command),
        exit_code=completed.returncode,
        stdout_text=completed.stdout,
        stderr_text=completed.stderr,
        duration_seconds=duration_seconds,
    )
    return HarnessAiddRunResult(
        command=command,
        runtime_id=runtime_id,
        work_item=work_item,
        exit_code=completed.returncode,
        stdout_text=completed.stdout,
        stderr_text=completed.stderr,
        duration_seconds=duration_seconds,
        command_transcript=command_transcript,
    )


def run_verification_steps(
    *,
    scenario: Scenario,
    working_copy_path: Path,
    aidd_run_result: HarnessAiddRunResult,
    environment: Mapping[str, str] | None = None,
) -> HarnessVerificationResult:
    _validate_working_copy_path(working_copy_path)

    command_env = dict(os.environ)
    command_env["AIDD_HARNESS_AIDD_EXIT_CODE"] = str(aidd_run_result.exit_code)
    if environment is not None:
        command_env.update(environment)

    command_transcripts = _run_shell_commands(
        commands=scenario.verify.commands,
        working_copy_path=working_copy_path,
        command_env=command_env,
        error_label="Verification",
        error_type=HarnessVerificationError,
    )
    return HarnessVerificationResult(
        executed_commands=tuple(transcript.command for transcript in command_transcripts),
        aidd_exit_code=aidd_run_result.exit_code,
        command_transcripts=command_transcripts,
        duration_seconds=sum(transcript.duration_seconds for transcript in command_transcripts),
    )


def run_teardown_steps(
    *,
    teardown_commands: tuple[str, ...],
    working_copy_path: Path,
    environment: Mapping[str, str] | None = None,
) -> HarnessTeardownResult:
    _validate_working_copy_path(working_copy_path)

    command_env = dict(os.environ)
    if environment is not None:
        command_env.update(environment)

    command_transcripts = _run_shell_commands(
        commands=teardown_commands,
        working_copy_path=working_copy_path,
        command_env=command_env,
        error_label="Teardown",
        error_type=HarnessTeardownError,
    )
    return HarnessTeardownResult(
        executed_commands=tuple(transcript.command for transcript in command_transcripts),
        command_transcripts=command_transcripts,
        duration_seconds=sum(transcript.duration_seconds for transcript in command_transcripts),
    )


def run_with_teardown[T](
    *,
    action: Callable[[], T],
    teardown_commands: tuple[str, ...],
    working_copy_path: Path,
    environment: Mapping[str, str] | None = None,
) -> tuple[T, HarnessTeardownResult]:
    result_marker = object()
    action_result: T | object = result_marker
    action_error: BaseException | None = None
    try:
        action_result = action()
    except BaseException as exc:  # pragma: no cover - exercised by failure-path tests.
        action_error = exc

    try:
        teardown_result = run_teardown_steps(
            teardown_commands=teardown_commands,
            working_copy_path=working_copy_path,
            environment=environment,
        )
    except BaseException as teardown_error:
        if action_error is not None:
            if isinstance(action_error, Exception) and isinstance(teardown_error, Exception):
                raise ExceptionGroup(
                    "Scenario execution and teardown both failed.",
                    [action_error, teardown_error],
                ) from None
            raise BaseExceptionGroup(
                "Scenario execution and teardown both failed.",
                [action_error, teardown_error],
            ) from None
        raise

    if action_error is not None:
        raise action_error
    return cast(T, action_result), teardown_result

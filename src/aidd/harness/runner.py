from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from aidd.harness.scenarios import Scenario


class HarnessSetupError(RuntimeError):
    """Raised when a setup command fails."""


@dataclass(frozen=True, slots=True)
class HarnessSetupResult:
    executed_commands: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HarnessAiddRunResult:
    command: tuple[str, ...]
    runtime_id: str
    work_item: str
    exit_code: int
    stdout_text: str
    stderr_text: str


def run_setup_steps(
    *,
    scenario: Scenario,
    working_copy_path: Path,
    environment: Mapping[str, str] | None = None,
) -> HarnessSetupResult:
    if not working_copy_path.exists() or not working_copy_path.is_dir():
        raise ValueError(
            f"Working copy path must be an existing directory: {working_copy_path.as_posix()}"
        )

    command_env = dict(os.environ)
    if environment is not None:
        command_env.update(environment)

    executed_commands: list[str] = []
    for command in scenario.setup.commands:
        completed = subprocess.run(
            ["/bin/sh", "-lc", command],
            cwd=working_copy_path,
            env=command_env,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or completed.stdout.strip() or "no command output"
            raise HarnessSetupError(
                "Setup command failed with non-zero exit "
                f"({completed.returncode}): {command}\n{stderr}"
            )
        executed_commands.append(command)

    return HarnessSetupResult(executed_commands=tuple(executed_commands))


def invoke_aidd_run(
    *,
    scenario: Scenario,
    working_copy_path: Path,
    runtime_id: str,
    work_item: str,
    aidd_command: tuple[str, ...] = ("uv", "run", "aidd"),
    environment: Mapping[str, str] | None = None,
) -> HarnessAiddRunResult:
    if not working_copy_path.exists() or not working_copy_path.is_dir():
        raise ValueError(
            f"Working copy path must be an existing directory: {working_copy_path.as_posix()}"
        )
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

    completed = subprocess.run(
        command,
        cwd=working_copy_path,
        env=command_env,
        capture_output=True,
        text=True,
        check=False,
    )
    return HarnessAiddRunResult(
        command=command,
        runtime_id=runtime_id,
        work_item=work_item,
        exit_code=completed.returncode,
        stdout_text=completed.stdout,
        stderr_text=completed.stderr,
    )

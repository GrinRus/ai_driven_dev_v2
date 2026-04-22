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

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from aidd.core.contracts import repo_root_from
from aidd.harness.scenarios import load_scenario


@dataclass(frozen=True, slots=True)
class CiScenarioManifest:
    scenario_id: str
    path: Path


@dataclass(frozen=True, slots=True)
class CiScenarioExecution:
    scenario_id: str
    path: Path
    exit_code: int
    stdout_text: str
    stderr_text: str


@dataclass(frozen=True, slots=True)
class CiScenarioLaneResult:
    discovered_ids: tuple[str, ...]
    executed_ids: tuple[str, ...]
    executions: tuple[CiScenarioExecution, ...]

    @property
    def succeeded(self) -> bool:
        return (
            self.discovered_ids == self.executed_ids
            and all(execution.exit_code == 0 for execution in self.executions)
        )


class CiScenarioDiscoveryError(ValueError):
    """Raised when CI scenario discovery is ambiguous."""


def discover_ci_scenarios(scenario_root: Path) -> tuple[CiScenarioManifest, ...]:
    manifests = tuple(
        CiScenarioManifest(scenario_id=scenario.scenario_id, path=path.resolve())
        for path in sorted(scenario_root.rglob("*.yaml"))
        if (scenario := load_scenario(path)).automation_lane == "ci"
    )
    ordered = tuple(sorted(manifests, key=lambda item: (item.scenario_id, item.path.as_posix())))
    duplicate_ids = tuple(
        sorted(
            scenario_id
            for scenario_id in {item.scenario_id for item in ordered}
            if sum(item.scenario_id == scenario_id for item in ordered) > 1
        )
    )
    if duplicate_ids:
        raise CiScenarioDiscoveryError(
            "Duplicate CI scenario ids: " + ", ".join(duplicate_ids) + "."
        )
    return ordered


def execute_ci_scenario_lane(
    *,
    scenario_root: Path,
    workspace_root: Path,
    aidd_command: tuple[str, ...] = (sys.executable, "-m", "aidd.cli.main"),
) -> CiScenarioLaneResult:
    manifests = discover_ci_scenarios(scenario_root)
    repository_root = repo_root_from(scenario_root.resolve(strict=False))
    executions: list[CiScenarioExecution] = []
    for manifest in manifests:
        command = (
            *aidd_command,
            "eval",
            "execute",
            manifest.path.as_posix(),
            "--root",
            workspace_root.as_posix(),
        )
        completed = subprocess.run(
            command,
            cwd=repository_root,
            capture_output=True,
            text=True,
            check=False,
        )
        executions.append(
            CiScenarioExecution(
                scenario_id=manifest.scenario_id,
                path=manifest.path,
                exit_code=completed.returncode,
                stdout_text=completed.stdout,
                stderr_text=completed.stderr,
            )
        )
    discovered_ids = tuple(item.scenario_id for item in manifests)
    executed_ids = tuple(item.scenario_id for item in executions)
    return CiScenarioLaneResult(
        discovered_ids=discovered_ids,
        executed_ids=executed_ids,
        executions=tuple(executions),
    )


__all__ = [
    "CiScenarioDiscoveryError",
    "CiScenarioExecution",
    "CiScenarioLaneResult",
    "CiScenarioManifest",
    "discover_ci_scenarios",
    "execute_ci_scenario_lane",
]

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    task: str
    runtime_targets: tuple[str, ...]
    raw: dict[str, Any]


def load_scenario(path: Path) -> Scenario:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    scenario_id = str(data["id"])
    task = str(data["task"])
    runtime_targets = tuple(data.get("runtime_targets", []))
    return Scenario(
        scenario_id=scenario_id,
        task=task,
        runtime_targets=runtime_targets,
        raw=data,
    )

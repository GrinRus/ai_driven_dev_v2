from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class RunRecord:
    run_id: str
    stage: str
    status: str

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultBundle:
    run_id: str
    status: str

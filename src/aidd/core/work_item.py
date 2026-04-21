from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class WorkItem:
    work_item_id: str

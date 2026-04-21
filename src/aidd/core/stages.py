from __future__ import annotations

STAGES: tuple[str, ...] = (
    "idea",
    "research",
    "plan",
    "review-spec",
    "tasklist",
    "implement",
    "review",
    "qa",
)


def is_valid_stage(stage: str) -> bool:
    return stage in STAGES


def stage_index(stage: str) -> int:
    if not is_valid_stage(stage):
        raise ValueError(f"Unknown stage: {stage}")
    return STAGES.index(stage)


def next_stage(stage: str) -> str | None:
    index = stage_index(stage)
    if index == len(STAGES) - 1:
        return None
    return STAGES[index + 1]

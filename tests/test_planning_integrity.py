from __future__ import annotations

from pathlib import Path

import pytest

from tests.planning_integrity import roadmap_backlog_integrity_errors


def _roadmap(*tasks: str) -> str:
    return "\n".join(
        (
            "## Wave 1 — wave (`planned`)",
            "### Epic W1-E1 — epic (`planned`)",
            "#### Slice W1-E1-S1 — slice (`planned`)",
            "Local tasks:",
            *tasks,
        )
    )


def _backlog(
    *,
    next_ids: tuple[str, ...] = (),
    soon_ids: tuple[str, ...] = (),
    parked_ids: tuple[str, ...] = (),
) -> str:
    def entries(ids: tuple[str, ...]) -> list[str]:
        return [f"- `{task_id}` — task" for task_id in ids]

    return "\n".join(
        (
            "# Active Backlog",
            "## Next",
            *entries(next_ids),
            "## Soon",
            *entries(soon_ids),
            "## Parking lot",
            *entries(parked_ids),
            "## Update rules",
        )
    )


def test_repository_roadmap_and_backlog_obey_generic_integrity_rules() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    roadmap = (repo_root / "docs/backlog/roadmap.md").read_text(encoding="utf-8")
    backlog = (repo_root / "docs/backlog/backlog.md").read_text(encoding="utf-8")

    assert roadmap_backlog_integrity_errors(roadmap, backlog) == ()


@pytest.mark.parametrize(
    ("roadmap", "backlog", "expected"),
    (
        (
            _roadmap("- `W1-E1-S1-T1` (next) Do work."),
            _backlog(next_ids=("W1-E1-S1-T2",)),
            "backlog task is absent from roadmap",
        ),
        (
            _roadmap(
                "- `W1-E1-S1-T1` (next) Do work.",
                "- `W1-E1-S1-T1` (next) Duplicate work.",
            ),
            _backlog(next_ids=("W1-E1-S1-T1",)),
            "duplicate roadmap task definition",
        ),
        (
            _roadmap("- `W1-E1-S1-T1` (next) Do work."),
            _backlog(next_ids=("W1-E1-S1-T1", "W1-E1-S1-T1")),
            "duplicate backlog entry",
        ),
        (
            _roadmap("- `W1-E1-S1-T1` (done) Do work."),
            _backlog(next_ids=("W1-E1-S1-T1",)),
            "terminal task is queued",
        ),
        (
            _roadmap("- `W1-E1-S1-T1` (next) Do work."),
            _backlog(next_ids=("W1-E1-S1",)),
            "backlog entry is not a local task",
        ),
        (
            _roadmap("- `W1-E1-S1-T1` (soon) Do work."),
            _backlog(next_ids=("W1-E1-S1-T1",)),
            "backlog status mismatch",
        ),
        (
            _roadmap(
                "- `W1-E1-S1-T1` (next) Do work.",
                "- `W1-E1-S1-T3` (soon) Skip work.",
            ),
            _backlog(next_ids=("W1-E1-S1-T1",), soon_ids=("W1-E1-S1-T3",)),
            "Soon task is not a successor of Next",
        ),
    ),
)
def test_generic_integrity_rules_reject_invalid_planning_documents(
    roadmap: str,
    backlog: str,
    expected: str,
) -> None:
    assert any(expected in error for error in roadmap_backlog_integrity_errors(roadmap, backlog))


def test_soon_accepts_an_explicit_dependency_on_next() -> None:
    roadmap = _roadmap(
        "- `W1-E1-S1-T1` (next) Do work.",
        "- `W1-E1-S1-T3` (soon) Follow work.",
        "  - Dependencies: `W1-E1-S1-T1`.",
    )

    assert roadmap_backlog_integrity_errors(
        roadmap,
        _backlog(next_ids=("W1-E1-S1-T1",), soon_ids=("W1-E1-S1-T3",)),
    ) == ()

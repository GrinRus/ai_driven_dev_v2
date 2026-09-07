from __future__ import annotations

from pathlib import Path

import pytest

from tests.planning_integrity import (
    backlog_reconciliation_errors,
    parent_status_rollup_errors,
    roadmap_backlog_integrity_errors,
)


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
    assert backlog_reconciliation_errors(backlog) == ()


@pytest.mark.parametrize(
    "body",
    (
        "",
        "- `2026-09-05` Current\n- `2026-09-04` Old instruction\n",
        "- `2026-09-05` Current\n" + "  Older evidence\n" * 40,
    ),
)
def test_backlog_reconciliation_rejects_missing_or_accumulated_history(body: str) -> None:
    assert backlog_reconciliation_errors("## Current reconciliation\n" + body)


def test_backlog_reconciliation_accepts_one_bounded_note_and_archive_link() -> None:
    backlog = (
        "## Current reconciliation\n\n"
        "- `2026-09-05` Current work and remaining blocker.\n\n"
        "Earlier evidence: [archive](reconciliation-history-2026-09-05.md).\n"
    )
    assert backlog_reconciliation_errors(backlog) == ()


def test_backlog_reconciliation_rejects_duplicate_current_notes() -> None:
    backlog = (
        "## Current reconciliation\n\n"
        "- `2026-09-05` First current note.\n"
        "- `2026-09-05` Duplicate current note.\n"
    )

    assert backlog_reconciliation_errors(backlog)


def _rollup_roadmap(*task_statuses: str) -> str:
    parent_status = (
        "done"
        if task_statuses and all(status == "done" for status in task_statuses)
        else "planned"
    )
    tasks = [
        f"- `W1-E1-S1-T{number}` ({status}) Task {number}."
        for number, status in enumerate(task_statuses, start=1)
    ]
    return "\n".join(
        (
            f"## Wave 1 — wave (`{parent_status}`)",
            f"### Epic W1-E1 — epic (`{parent_status}`)",
            f"#### Slice W1-E1-S1 — slice (`{parent_status}`)",
            "Local tasks:",
            *tasks,
        )
    )


@pytest.mark.parametrize(
    "task_statuses",
    (
        ("done", "done"),
        ("done", "planned"),
        ("done", "parked"),
        ("parked", "parked"),
        ("done", "blocked"),
    ),
)
def test_parent_status_rollup_accepts_documented_child_states(
    task_statuses: tuple[str, ...],
) -> None:
    assert parent_status_rollup_errors(_rollup_roadmap(*task_statuses)) == ()


def test_parent_status_rollup_rejects_stale_completed_parent() -> None:
    roadmap = _rollup_roadmap("done", "planned").replace(
        "#### Slice W1-E1-S1 — slice (`planned`)",
        "#### Slice W1-E1-S1 — slice (`done`)",
    )

    errors = parent_status_rollup_errors(roadmap)

    assert any("parent status mismatch for W1-E1-S1" in error for error in errors)


def test_parent_status_rollup_rejects_done_container_without_children() -> None:
    roadmap = "\n".join(
        (
            "## Wave 1 — wave (`done`)",
            "### Epic W1-E1 — epic (`done`)",
            "#### Slice W1-E1-S1 — slice (`done`)",
        )
    )

    errors = parent_status_rollup_errors(roadmap)

    assert any("expected 'planned'" in error for error in errors)


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

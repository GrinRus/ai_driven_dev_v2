from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.run_packaged_ui_scenarios import (
    JOURNEY_NODE_IDS,
    _validate_manifest_entries,
    discover_packaged_ui_journeys,
    execute_packaged_ui_scenarios,
)


def _entry(journey: str, **extra: Any) -> dict[str, object]:
    return {"id": journey, "journey": journey, **extra}


def test_packaged_ui_discovery_matches_all_manifest_journeys() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    discovered = discover_packaged_ui_journeys(repository_root)

    assert discovered == tuple(f"W36-E7-S1-T{number}" for number in range(1, 13))
    assert set(JOURNEY_NODE_IDS) == set(discovered)
    assert all(JOURNEY_NODE_IDS[journey] for journey in discovered)


@pytest.mark.parametrize(
    ("entries", "message"),
    (
        ([_entry("W36-E7-S1-T1"), _entry("W36-E7-S1-T1")], "Duplicate"),
        ([_entry("W36-E7-S1-T1", provider="codex")], "Live-provider"),
        ([_entry("W36-E7-S1-T1", requiresLiveProvider=True)], "Live-provider"),
        ([_entry("W36-E7-S1-T99")], "registry mismatch"),
    ),
)
def test_packaged_ui_manifest_preflight_fails_closed(
    entries: list[dict[str, object]],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _validate_manifest_entries(entries)


def test_packaged_ui_runner_continues_after_failure_and_preserves_order() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    executed: list[tuple[str, ...]] = []

    def runner(_root: Path, node_ids: Sequence[str]) -> int:
        normalized = tuple(node_ids)
        executed.append(normalized)
        return 1 if len(executed) == 2 else 0

    results = execute_packaged_ui_scenarios(repository_root, runner=runner)

    assert tuple(result.journey_id for result in results) == tuple(
        f"W36-E7-S1-T{number}" for number in range(1, 13)
    )
    assert len(executed) == 12
    assert [result.return_code for result in results].count(1) == 1


def test_ci_enforces_the_shared_packaged_ui_browser_runner() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load(
        (repository_root / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
    )
    jobs = workflow["jobs"]
    browser_job = jobs["packaged-ui-browser"]
    serialized_steps = yaml.safe_dump(browser_job["steps"], sort_keys=False)

    assert browser_job["timeout-minutes"] == 45
    assert browser_job["needs"] == "lint-type-test"
    assert "actions/cache@" in serialized_steps
    assert "~/.cache/ms-playwright" in serialized_steps
    assert "python -m playwright install-deps chromium" in serialized_steps
    assert "python -m playwright install chromium" in serialized_steps
    assert "python scripts/run_packaged_ui_scenarios.py" in serialized_steps
    assert "AIDD_EVAL_" not in serialized_steps
    assert "OPENAI_API_KEY" not in serialized_steps
    assert "packaged-ui-browser" in jobs["build"]["needs"]

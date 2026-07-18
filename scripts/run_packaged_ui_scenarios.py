from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

JOURNEY_NODE_IDS: dict[str, tuple[str, ...]] = {
    "W36-E7-S1-T1": (
        "browser_tests/test_journey_guided_setup.py::test_guided_setup_create_or_resume_launches_into_inbox",
    ),
    "W36-E7-S1-T2": (
        "browser_tests/test_journey_active_studio.py::test_active_studio_reconnects_cancels_and_returns_to_durable_logs",
    ),
    "W36-E7-S1-T3": ("browser_tests/test_journey_runtime_validation_recovery.py",),
    "W36-E7-S1-T4": ("browser_tests/test_journey_review_qa.py",),
    "W36-E7-S1-T5": (
        "browser_tests/test_history_journey.py::test_history_journey_preserves_retained_runs",
    ),
    "W36-E7-S1-T6": (
        "browser_tests/test_journey_question_recovery.py::test_question_recovery_restores_draft_and_resumes_from_durable_answer",
    ),
    "W36-E7-S1-T7": (
        "browser_tests/test_journey_document_evidence.py::test_document_canvas_and_evidence_inspector_preserve_safe_context",
    ),
    "W36-E7-S1-T8": ("browser_tests/test_terminal_journey.py",),
    "W36-E7-S1-T9": ("browser_tests/test_journey_implementation.py",),
    "W36-E7-S1-T10": ("browser_tests/test_journey_intervention_recovery.py",),
    "W36-E7-S1-T11": ("browser_tests/test_journey_approval_recovery.py",),
    "W36-E7-S1-T12": ("browser_tests/test_journey_inbox.py",),
}

_JOURNEY_ID = re.compile(r"^W36-E7-S1-T(?P<number>[1-9][0-9]*)$")
_NODE_EVALUATOR = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
const script = new vm.Script(`${source}\n;JSON.stringify(SURFACE_PARITY_MANIFEST);`);
process.stdout.write(script.runInNewContext(Object.create(null), {timeout: 1000}));
"""


@dataclass(frozen=True, slots=True)
class JourneyExecution:
    journey_id: str
    node_ids: tuple[str, ...]
    return_code: int


def _journey_sort_key(journey_id: str) -> int:
    match = _JOURNEY_ID.fullmatch(journey_id)
    if match is None:
        raise ValueError(f"Unsupported packaged-UI journey id: {journey_id}")
    return int(match.group("number"))


def _validate_manifest_entries(entries: object) -> tuple[str, ...]:
    if not isinstance(entries, list):
        raise ValueError("Packaged UI parity manifest must evaluate to a JSON array.")
    journeys: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Packaged UI parity entries must be JSON objects.")
        journey = entry.get("journey")
        if not isinstance(journey, str) or not journey.strip():
            raise ValueError("Packaged UI parity entry is missing its journey id.")
        live_provider = entry.get("requiresLiveProvider") is True
        unsupported_provider = entry.get("provider") not in {None, "local"}
        if live_provider or unsupported_provider:
            raise ValueError(f"Live-provider packaged UI journey is forbidden: {journey}")
        journeys.append(journey)
    duplicates = sorted({item for item in journeys if journeys.count(item) > 1})
    if duplicates:
        raise ValueError(f"Duplicate packaged-UI journey ids: {', '.join(duplicates)}")
    discovered = tuple(sorted(journeys, key=_journey_sort_key))
    registered = tuple(sorted(JOURNEY_NODE_IDS, key=_journey_sort_key))
    if discovered != registered:
        missing = sorted(set(discovered) - set(registered), key=_journey_sort_key)
        extra = sorted(set(registered) - set(discovered), key=_journey_sort_key)
        raise ValueError(
            "Packaged-UI journey registry mismatch: "
            f"missing registry entries={missing}, undeclared registry entries={extra}"
        )
    return discovered


def discover_packaged_ui_journeys(repository_root: Path) -> tuple[str, ...]:
    manifest_path = repository_root / "src/aidd/cli/static/operator-surface-parity.js"
    completed = subprocess.run(
        ("node", "-e", _NODE_EVALUATOR, manifest_path.as_posix()),
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "Node evaluation failed without diagnostics."
        raise RuntimeError(f"Unable to evaluate packaged UI parity manifest: {detail}")
    try:
        entries = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Packaged UI parity manifest emitted invalid JSON.") from exc
    return _validate_manifest_entries(entries)


def _run_pytest(repository_root: Path, node_ids: Sequence[str]) -> int:
    completed = subprocess.run(
        (sys.executable, "-m", "pytest", "-q", *node_ids),
        cwd=repository_root,
        check=False,
    )
    return completed.returncode


def execute_packaged_ui_scenarios(
    repository_root: Path,
    *,
    runner: Callable[[Path, Sequence[str]], int] = _run_pytest,
) -> tuple[JourneyExecution, ...]:
    discovered_ids = discover_packaged_ui_journeys(repository_root)
    results: list[JourneyExecution] = []
    for journey_id in discovered_ids:
        node_ids = JOURNEY_NODE_IDS[journey_id]
        return_code = runner(repository_root, node_ids)
        results.append(JourneyExecution(journey_id, node_ids, return_code))
    executed_ids = tuple(result.journey_id for result in results)
    if executed_ids != discovered_ids:
        raise RuntimeError(
            f"Packaged-UI execution mismatch: discovered_ids={discovered_ids}, "
            f"executed_ids={executed_ids}"
        )
    return tuple(results)


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    try:
        results = execute_packaged_ui_scenarios(repository_root)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"packaged-ui preflight failed: {exc}", file=sys.stderr)
        return 2
    failed = [result.journey_id for result in results if result.return_code != 0]
    print(json.dumps({
        "discovered_ids": [result.journey_id for result in results],
        "executed_ids": [result.journey_id for result in results],
        "failed_ids": failed,
    }))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

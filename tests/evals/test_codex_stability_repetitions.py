from __future__ import annotations

import json
from pathlib import Path

from aidd.evals.codex_stability_profile import (
    CODEX_STABILITY_METRIC_IDS,
    load_codex_stability_profile,
    validate_repetition_evidence,
)

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "w43-e5-s2-t2-codex-stability"
    / "repetitions.json"
)


def test_three_fresh_repetitions_are_pinned_and_fail_closed() -> None:
    profile = load_codex_stability_profile()
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    repetitions = tuple(
        validate_repetition_evidence(profile, repetition)
        for repetition in payload["repetitions"]
    )

    assert len(repetitions) == profile.minimum_repetitions
    assert {item.runtime_id for item in repetitions} == {"codex"}
    assert {item.target_revision for item in repetitions} == {profile.target_revision}
    assert {item.config_identity for item in repetitions} == {profile.config_identity}
    assert {item.status for item in repetitions} == {"infra-fail"}
    assert all(tuple(item.metrics) == CODEX_STABILITY_METRIC_IDS for item in repetitions)


def test_aggregate_fixture_does_not_claim_stability() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert payload["status"] == "infra-fail"
    assert all(item["status"] == "infra-fail" for item in payload["repetitions"])

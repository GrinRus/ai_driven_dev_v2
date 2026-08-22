from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.evals.codex_stability_profile import (
    CODEX_STABILITY_METRIC_IDS,
    CODEX_STABILITY_REQUIRED_ARTIFACTS,
    DEFAULT_CODEX_STABILITY_PROFILE_PATH,
    DEFAULT_CODEX_STABILITY_SCENARIO_PATH,
    CodexStabilityProfile,
    CodexStabilityProfileError,
    load_codex_stability_profile,
    validate_profile_against_scenario,
    validate_repetition_evidence,
)

runner = CliRunner()


def _profile() -> CodexStabilityProfile:
    profile = load_codex_stability_profile()
    validate_profile_against_scenario(profile)
    return profile


def _repetition_evidence(
    profile: CodexStabilityProfile, repetition_id: str
) -> dict[str, object]:
    metrics: dict[str, dict[str, float]] = {}
    for metric_id in CODEX_STABILITY_METRIC_IDS:
        denominator = 2.0
        numerator = 2.0
        if metric_id in {"exhaustion", "findings-per-root-cause", "false-budget-consumption"}:
            numerator = 0.0
        metrics[metric_id] = {
            "numerator": numerator,
            "denominator": denominator,
            "value": numerator / denominator,
        }
    return {
        "schema_version": profile.schema_version,
        "repetition_id": repetition_id,
        "scenario_id": profile.scenario_id,
        "run_id": f"eval-live-007-codex-{repetition_id}",
        "runtime_id": profile.runtime_id,
        "target_revision": profile.target_revision,
        "config_identity": profile.config_identity,
        "status": "pass",
        "stage_scope": [profile.stage_start, profile.stage_end],
        "attempts": [
            {"attempt_id": "idea-1", "stage": "idea", "mode": "automatic", "status": "pass"}
        ],
        "evidence_links": list(CODEX_STABILITY_REQUIRED_ARTIFACTS),
        "first_failure_boundary": {
            "category": "none",
            "signal": "none",
            "source": "verdict.md",
        },
        "metrics": metrics,
    }


def test_codex_profile_is_pinned_to_aidd_live_007_and_has_canonical_metrics() -> None:
    profile = _profile()

    assert profile.profile_id == "w43-e5-s2-codex-stability-v1"
    assert profile.runtime_id == "codex"
    assert profile.scenario_id == "AIDD-LIVE-007"
    assert profile.representative_task_id == "TASK-LIVE-HONO-NON-ERROR-THROW"
    assert profile.target_revision == "cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba"
    assert profile.minimum_repetitions == 3
    assert tuple(metric.metric_id for metric in profile.metrics) == CODEX_STABILITY_METRIC_IDS
    assert set(CODEX_STABILITY_REQUIRED_ARTIFACTS).issubset(
        profile.evidence_schema.required_artifacts
    )


def test_profile_scenario_passes_existing_eval_doctor_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    codex = bin_dir / "codex"
    codex.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"login\" ] && [ \"$2\" = \"status\" ]; then exit 0; fi\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'codex 0.144.1'; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    monkeypatch.delenv("AIDD_EVAL_CODEX_COMMAND", raising=False)
    monkeypatch.setenv("PATH", f"{bin_dir.as_posix()}:{os.environ.get('PATH', '')}")

    result = runner.invoke(
        app,
        ["eval", "doctor", DEFAULT_CODEX_STABILITY_SCENARIO_PATH.as_posix(), "--runtime", "codex"],
    )

    assert result.exit_code == 0, result.output
    normalized = " ".join(result.stdout.split())
    assert "AIDD-LIVE-007" in normalized
    assert "Runtime" in normalized
    assert "codex" in normalized
    assert "Provider available" in normalized


def test_one_evidence_schema_applies_to_three_codex_repetitions() -> None:
    profile = _profile()

    repetitions = tuple(
        validate_repetition_evidence(
            profile, _repetition_evidence(profile, f"repetition-{index:02d}")
        )
        for index in range(1, profile.minimum_repetitions + 1)
    )

    assert len(repetitions) == 3
    assert {repetition.runtime_id for repetition in repetitions} == {"codex"}
    assert all(repetition.stage_scope == ("idea", "qa") for repetition in repetitions)
    assert all(
        set(repetition.metrics) == set(CODEX_STABILITY_METRIC_IDS)
        for repetition in repetitions
    )


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("runtime_id", "claude-code", "scenario/runtime"),
        ("target_revision", "0" * 40, "pin"),
        ("config_identity", "different-profile-v1", "pin"),
    ),
)
def test_repetition_evidence_rejects_drift(
    field: str,
    replacement: str,
    message: str,
) -> None:
    profile = _profile()
    evidence = _repetition_evidence(profile, "repetition-01")
    evidence[field] = replacement

    with pytest.raises(CodexStabilityProfileError, match=message):
        validate_repetition_evidence(profile, evidence)


def test_repetition_evidence_rejects_missing_canonical_artifact() -> None:
    profile = _profile()
    evidence = _repetition_evidence(profile, "repetition-01")
    evidence["evidence_links"] = ["runtime.log"]

    # Evidence links are intentionally bounded by the profile contract for every repetition.
    with pytest.raises(CodexStabilityProfileError, match="evidence_links"):
        validate_repetition_evidence(profile, evidence)


def test_profile_fixture_round_trips_to_machine_readable_schema() -> None:
    profile = _profile()
    raw = json.loads(DEFAULT_CODEX_STABILITY_PROFILE_PATH.read_text(encoding="utf-8"))

    assert raw["schema_version"] == profile.schema_version
    assert raw["scenario"]["id"] == profile.scenario_id
    assert raw["runtime_config"]["config_identity"] == profile.config_identity
    assert [item["metric_id"] for item in raw["metrics"]] == list(CODEX_STABILITY_METRIC_IDS)


def test_profile_rejects_scenario_revision_drift(tmp_path: Path) -> None:
    source = json.loads(DEFAULT_CODEX_STABILITY_PROFILE_PATH.read_text(encoding="utf-8"))
    source["scenario"]["target_revision"] = "0" * 40
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(source), encoding="utf-8")

    profile = load_codex_stability_profile(path)
    with pytest.raises(CodexStabilityProfileError, match="target revision"):
        validate_profile_against_scenario(profile)

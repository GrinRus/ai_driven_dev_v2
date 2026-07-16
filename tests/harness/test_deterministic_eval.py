from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from aidd.harness.deterministic_eval import (
    DeterministicEvalInputError,
    DeterministicEvalRequest,
    execute_deterministic_eval,
    validate_deterministic_scenario,
)
from aidd.harness.runner import HarnessVerificationError
from aidd.harness.scenarios import ScenarioRepoSource, load_scenario

REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_SCENARIO = REPO_ROOT / "harness/scenarios/smoke/plan-stage-minimal-fixture.yaml"


def test_execute_deterministic_eval_persists_failed_verification_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fail_verification(**_kwargs: object) -> object:
        raise HarnessVerificationError("injected verification failure")

    monkeypatch.setattr(
        "aidd.harness.deterministic_eval.run_verification_steps",
        _fail_verification,
    )

    result = execute_deterministic_eval(
        DeterministicEvalRequest(
            scenario_path=SMOKE_SCENARIO,
            workspace_root=tmp_path / ".aidd",
        )
    )

    assert result.status == "fail"
    assert result.bundle_root.is_dir()
    assert result.verdict_path.is_file()
    assert (result.bundle_root / "setup-transcript.json").is_file()
    assert (result.bundle_root / "run-transcript.json").is_file()
    assert (result.bundle_root / "verify-transcript.json").is_file()
    assert (result.bundle_root / "teardown-transcript.json").is_file()


def test_validate_deterministic_scenario_rejects_remote_repository() -> None:
    scenario = load_scenario(SMOKE_SCENARIO)
    remote = replace(
        scenario,
        repo=ScenarioRepoSource(
            url="https://github.com/example/project.git",
            default_branch="main",
            revision=None,
        ),
    )

    with pytest.raises(
        DeterministicEvalInputError,
        match="local fixture repository",
    ):
        validate_deterministic_scenario(
            scenario_path=SMOKE_SCENARIO,
            scenario=remote,
        )


def test_validate_deterministic_scenario_rejects_provider_only_target() -> None:
    scenario = load_scenario(SMOKE_SCENARIO)
    provider_only = replace(
        scenario,
        runtime_targets=("codex",),
        run=replace(scenario.run, runtime_targets=("codex",)),
    )

    with pytest.raises(
        DeterministicEvalInputError,
        match="must allow the `generic-cli` runtime",
    ):
        validate_deterministic_scenario(
            scenario_path=SMOKE_SCENARIO,
            scenario=provider_only,
        )

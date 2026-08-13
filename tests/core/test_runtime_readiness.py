from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from aidd.config import AiddConfig, load_config
from aidd.core.runtime_launch_history import RuntimeLaunchOutcome
from aidd.core.runtime_readiness import (
    RuntimeAuthenticationStatus,
    RuntimeCapabilityProbeReport,
    RuntimeReadinessItem,
    RuntimeReadinessProbeReport,
    RuntimeReadinessView,
    resolve_runtime_readiness,
    runtime_config_identity,
)

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def _config(tmp_path: Path, *, extra: str = "") -> AiddConfig:
    path = tmp_path / "aidd.toml"
    path.write_text(
        "\n".join(
            (
                "[runtime.generic_cli]",
                'command = "python -m fixture_runtime"',
                'mode = "adapter-flags"',
                extra,
                "",
            )
        ),
        encoding="utf-8",
    )
    return load_config(path)


def _probe(
    *,
    config_identity: str | None = None,
    observed_at_utc: str | None = None,
    provider_available: bool = True,
    execution_command_available: bool = True,
    authentication_status: RuntimeAuthenticationStatus = "verified",
    supports_permission_policy: bool = True,
) -> RuntimeReadinessProbeReport:
    return RuntimeReadinessProbeReport(
        provider_available=provider_available,
        execution_command_available=execution_command_available,
        provider_version="fixture-runtime",
        provider_command="python",
        authentication_status=authentication_status,
        capabilities=RuntimeCapabilityProbeReport(
            supports_raw_log_stream=True,
            supports_structured_log_stream=True,
            supports_questions=True,
            supports_resume=True,
            supports_subagents=False,
            supports_permission_policy=supports_permission_policy,
            supports_live_decisions=True,
            preferred_transport="subprocess",
        ),
        config_identity=config_identity,
        observed_at_utc=observed_at_utc or "2026-08-13T12:00:00Z",
    )


def _generic_item(view: RuntimeReadinessView) -> RuntimeReadinessItem:
    return next(item for item in view.runtimes if item.runtime_id == "generic-cli")


def test_launch_readiness_projection_is_eligible_and_identity_bound(tmp_path: Path) -> None:
    config = _config(tmp_path)
    identity = runtime_config_identity(
        runtime_id="generic-cli",
        runtime_config=config.runtime_config("generic-cli"),
    )
    item = _generic_item(
        resolve_runtime_readiness(
            config=config,
            probe_reports={"generic-cli": _probe(config_identity=identity)},
            now=NOW,
        )
    )

    assert item.eligible is True
    assert item.disabled_reason is None
    assert item.probe_observed_at_utc == "2026-08-13T12:00:00Z"
    assert item.config_identity == runtime_config_identity(
        runtime_id="generic-cli",
        runtime_config=config.runtime_config("generic-cli"),
    )
    assert len(item.config_identity) == 64


def test_unverified_auth_and_prior_success_do_not_fabricate_failure(tmp_path: Path) -> None:
    config = _config(tmp_path)
    identity = runtime_config_identity(
        runtime_id="generic-cli",
        runtime_config=config.runtime_config("generic-cli"),
    )
    item = _generic_item(
        resolve_runtime_readiness(
            config=config,
            probe_reports={
                "generic-cli": _probe(
                    authentication_status="unverified",
                    config_identity=identity,
                ),
            },
            launch_history={
                "generic-cli": RuntimeLaunchOutcome(
                    runtime_id="generic-cli",
                    outcome="success",
                    recorded_at_utc="2026-08-13T11:00:00Z",
                    run_id="run-1",
                    stage="plan",
                    attempt_number=1,
                    evidence_path="runs/run-1/plan/attempt-0001/runtime-exit.json",
                ),
            },
            now=NOW,
        )
    )

    assert item.authentication.status == "unverified"
    assert item.latest_launch is not None
    assert item.eligible is True


def test_readiness_fails_closed_for_stale_probe_and_config_drift(tmp_path: Path) -> None:
    config = _config(tmp_path)
    stale = _generic_item(
        resolve_runtime_readiness(
            config=config,
            probe_reports={
                "generic-cli": _probe(
                    observed_at_utc="2026-08-13T11:50:00Z",
                )
            },
            now=NOW,
            max_probe_age_seconds=60,
        )
    )
    assert stale.eligible is False
    assert stale.disabled_reason == (
        "Runtime readiness is stale; refresh the probe before launching."
    )

    drift = _generic_item(
        resolve_runtime_readiness(
            config=config,
            probe_reports={
                "generic-cli": _probe(config_identity="f" * 64),
            },
            now=NOW,
        )
    )
    assert drift.eligible is False
    assert drift.disabled_reason == "Runtime configuration changed; refresh readiness."


def test_readiness_reports_auth_command_permission_and_missing_probe_states(tmp_path: Path) -> None:
    config = _config(tmp_path, extra='permission_policy = "brokered"')
    cases = (
        (
            "auth",
            _probe(authentication_status="failed"),
            "Runtime authentication failed.",
        ),
        (
            "command",
            _probe(execution_command_available=False),
            "Runtime execution command is unavailable.",
        ),
        (
            "binary",
            _probe(provider_available=False),
            "Runtime binary is unavailable.",
        ),
        (
            "permission",
            _probe(supports_permission_policy=False),
            "Runtime permission policy is not supported by the adapter.",
        ),
    )
    for _, report, reason in cases:
        item = _generic_item(
            resolve_runtime_readiness(
                config=config,
                probe_reports={"generic-cli": report},
                now=NOW,
            )
        )
        assert item.eligible is False
        assert item.disabled_reason == reason

    missing = _generic_item(
        resolve_runtime_readiness(
            config=config,
            probe_reports={},
            now=NOW,
        )
    )
    assert missing.eligible is False
    assert missing.disabled_reason == "Runtime readiness has not been observed."


def test_readiness_rejects_future_observation_and_negative_probe_age(tmp_path: Path) -> None:
    config = _config(tmp_path)
    item = _generic_item(
        resolve_runtime_readiness(
            config=config,
            probe_reports={
                "generic-cli": _probe(observed_at_utc="2026-08-13T12:01:00Z"),
            },
            now=NOW,
        )
    )
    assert item.eligible is False
    assert item.disabled_reason == "Runtime readiness is stale; refresh the probe before launching."

    try:
        resolve_runtime_readiness(
            config=config,
            probe_reports={},
            now=NOW,
            max_probe_age_seconds=-1,
        )
    except ValueError as exc:
        assert str(exc) == "max_probe_age_seconds must be non-negative."
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("negative probe age must be rejected")

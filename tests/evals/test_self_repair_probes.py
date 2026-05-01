from __future__ import annotations

from aidd.core.stages import STAGES
from aidd.evals.self_repair_probes import (
    SELF_REPAIR_PROBES,
    probes_for_stage,
    validate_probe_catalog,
)


def test_self_repair_probe_catalog_covers_every_stage() -> None:
    validate_probe_catalog()

    stages_with_probes = {probe.stage for probe in SELF_REPAIR_PROBES}
    assert stages_with_probes == set(STAGES)


def test_self_repair_probe_catalog_includes_planned_failure_modes() -> None:
    probe_ids = {probe.probe_id for probe in SELF_REPAIR_PROBES}

    assert "idea-missing-headings" in probe_ids
    assert "idea-placeholder-content" in probe_ids
    assert "idea-blocking-question-mismatch" in probe_ids
    assert "research-missing-citations" in probe_ids
    assert "research-unsupported-claim" in probe_ids
    assert "plan-malformed-repair-brief" in probe_ids
    assert "plan-weak-dependencies" in probe_ids
    assert "plan-validator-status-mismatch" in probe_ids
    assert "review-spec-sign-off-conflict" in probe_ids
    assert "tasklist-bundled-task" in probe_ids
    assert "tasklist-broken-dependency" in probe_ids
    assert "implement-unverifiable-touched-files" in probe_ids
    assert "implement-no-op-without-reason" in probe_ids
    assert "review-approval-with-unresolved-must-fix" in probe_ids
    assert "qa-ready-without-verification-evidence" in probe_ids


def test_probes_for_stage_returns_only_requested_stage() -> None:
    plan_probes = probes_for_stage("plan")

    assert {probe.stage for probe in plan_probes} == {"plan"}
    assert {probe.probe_id for probe in plan_probes} == {
        "plan-malformed-repair-brief",
        "plan-weak-dependencies",
        "plan-validator-status-mismatch",
    }

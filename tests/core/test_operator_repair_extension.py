from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from aidd.core.models.run import RepairExtensionGrant
from aidd.core.operator_repair_extension import resolve_operator_repair_extension_preview
from aidd.core.repair import persist_repair_extension_grant, persist_repair_history_snapshot
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
)
from aidd.validators.models import ValidationFinding
from aidd.validators.reports import render_validator_report


def _prepare_repair_exhausted_run(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        stage="plan",
        status="blocked",
    )
    stage_root = workspace_root / "workitems" / "WI-REPAIR" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    validator = stage_root / "validator-report.md"
    brief = stage_root / "repair-brief.md"
    validator.write_text(
        render_validator_report(
            findings=(
                ValidationFinding(
                    code="SEM-PLACEHOLDER-CONTENT",
                    message="Required evidence is missing.",
                    severity="high",
                ),
            )
        ),
        encoding="utf-8",
    )
    brief.write_text("# Repair Brief\n\n- Add the missing evidence.\n", encoding="utf-8")
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        stage="plan",
        attempt_number=1,
        trigger="repair",
        outcome="failed validation",
        stage_status="failed",
        validator_report_path=validator,
        repair_brief_path=brief,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        stage="plan",
        status="failed",
    )
    return workspace_root, validator, brief


def _grant(*, validator: Path, brief: Path, config: str) -> RepairExtensionGrant:
    return RepairExtensionGrant(
        work_item_id="WI-REPAIR",
        run_id="run-repair",
        stage="plan",
        validator_report_path="workitems/WI-REPAIR/stages/plan/validator-report.md",
        validator_report_sha256=hashlib.sha256(validator.read_bytes()).hexdigest(),
        repair_brief_path="workitems/WI-REPAIR/stages/plan/repair-brief.md",
        repair_brief_sha256=hashlib.sha256(brief.read_bytes()).hexdigest(),
        configuration_identity=config,
        author="operator",
        authorized_at_utc="2026-08-22T00:00:00Z",
        reason="test",
    )


def _preview(workspace_root: Path, **kwargs: object):
    return resolve_operator_repair_extension_preview(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        stage="plan",
        run_id="run-repair",
        current_configuration_identity="cfg-current",
        selected_runner="codex",
        **kwargs,
    )


def test_repair_extension_preview_is_core_owned_and_eligible(tmp_path: Path) -> None:
    workspace_root, _, _ = _prepare_repair_exhausted_run(tmp_path)

    preview = _preview(workspace_root)

    assert preview.eligible is True
    assert preview.disabled_reason is None
    assert preview.selected_runner == "codex"
    assert preview.current_findings
    assert preview.primary_cause == preview.current_findings[0]
    assert preview.automatic_repair_attempts_remaining == 2
    assert preview.manual_grant_used is False


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    (
        ({"active_job": True}, "active"),
        ({"current_configuration_identity": None}, "configuration"),
    ),
)
def test_repair_extension_preview_fails_closed_for_active_or_missing_context(
    tmp_path: Path,
    kwargs: dict[str, object],
    expected: str,
) -> None:
    workspace_root, _, _ = _prepare_repair_exhausted_run(tmp_path)
    if expected == "configuration":
        preview = resolve_operator_repair_extension_preview(
            workspace_root=workspace_root,
            work_item="WI-REPAIR",
            stage="plan",
            run_id="run-repair",
            selected_runner="codex",
            **kwargs,
        )
    else:
        preview = _preview(workspace_root, **kwargs)

    assert preview.eligible is False
    assert preview.disabled_reason
    assert expected in preview.disabled_reason.lower()


def test_repair_extension_preview_reports_manual_grant_and_config_drift(tmp_path: Path) -> None:
    workspace_root, validator, brief = _prepare_repair_exhausted_run(tmp_path)
    grant = _grant(validator=validator, brief=brief, config="cfg-old")
    persist_repair_extension_grant(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        stage="plan",
        grant=grant,
    )

    preview = _preview(workspace_root)

    assert preview.manual_grant_used is True
    assert preview.eligible is False
    assert preview.disabled_reason == (
        "Repair extension configuration drifted from the exhausted attempt."
    )


def test_repair_extension_preview_reports_stale_evidence_before_used_grant(tmp_path: Path) -> None:
    workspace_root, validator, brief = _prepare_repair_exhausted_run(tmp_path)
    persist_repair_extension_grant(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        stage="plan",
        grant=_grant(validator=validator, brief=brief, config="cfg-current"),
    )
    validator.write_text(validator.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")

    preview = _preview(workspace_root)

    assert preview.eligible is False
    assert preview.disabled_reason == (
        "Repair extension evidence is stale; refresh the validator report and repair brief."
    )


def test_repair_extension_preview_blocks_downstream_success_and_manual_reuse(
    tmp_path: Path,
) -> None:
    workspace_root, _, _ = _prepare_repair_exhausted_run(tmp_path)
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        stage="implement",
        status="succeeded",
    )
    downstream = _preview(workspace_root)
    assert downstream.eligible is False
    assert downstream.downstream_succeeded == ("implement",)
    assert "downstream" in (downstream.disabled_reason or "").lower()

    workspace_root, validator, brief = _prepare_repair_exhausted_run(tmp_path / "used")
    persist_repair_extension_grant(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        stage="plan",
        grant=_grant(validator=validator, brief=brief, config="cfg-current"),
    )
    used = _preview(workspace_root)
    assert used.eligible is False
    assert "already used" in (used.disabled_reason or "").lower()


def test_repair_extension_preview_blocks_manual_fix_status(tmp_path: Path) -> None:
    workspace_root, _, _ = _prepare_repair_exhausted_run(tmp_path)
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-REPAIR",
        run_id="run-repair",
        stage="plan",
        status="succeeded",
    )
    (workspace_root / "workitems" / "WI-REPAIR" / "stages" / "plan" / "stage-result.md").write_text(
        "# Stage Result\n\n- `succeeded`\n", encoding="utf-8"
    )

    preview = _preview(workspace_root)

    assert preview.eligible is False
    assert "latest repair-exhausted" in (preview.disabled_reason or "").lower()

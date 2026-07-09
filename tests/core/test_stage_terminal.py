from __future__ import annotations

from pathlib import Path

from aidd.core.stage_terminal import (
    ensure_repair_brief_records_exhausted_budget,
    ensure_stage_result_references_repair_brief,
    exhausted_budget_validation_finding,
    force_stage_result_failed_for_exhausted_budget,
    reconcile_stage_result_after_validation_pass,
    repair_brief_exhausts_terminal_budget,
    strip_stage_result_success_claims_for_validator_findings,
)


def _stage_result_path(workspace_root: Path) -> Path:
    return workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "stage-result.md"


def _write_successful_stage_result(workspace_root: Path) -> Path:
    stage_result_path = _stage_result_path(workspace_root)
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    stage_result_path.write_text(
        "# Stage result\n\n"
        "## Status\n\n"
        "- `succeeded`\n\n"
        "## Validation summary\n\n"
        "- validator report verdict: `pass`\n"
        "- validation `pass` confirmed by runtime-authored text\n",
        encoding="utf-8",
    )
    return stage_result_path


def test_repair_brief_terminal_budget_detection_uses_context_or_document(
    tmp_path: Path,
) -> None:
    repair_brief_path = tmp_path / "repair-brief.md"
    repair_brief_path.write_text(
        "Repair budget status: `repair-budget-final-attempt`.\n",
        encoding="utf-8",
    )

    assert repair_brief_exhausts_terminal_budget(
        repair_brief_path=repair_brief_path,
        repair_context_markdown=None,
    ) is False
    assert repair_brief_exhausts_terminal_budget(
        repair_brief_path=None,
        repair_context_markdown="Repair budget status: `repair-budget-exhausted`.",
    ) is True

    ensure_repair_brief_records_exhausted_budget(repair_brief_path)
    assert "Repair budget status: `repair-budget-exhausted`." in repair_brief_path.read_text(
        encoding="utf-8"
    )


def test_force_stage_result_failed_for_exhausted_budget_rewrites_terminal_claims(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _write_successful_stage_result(workspace_root)

    result_path = force_stage_result_failed_for_exhausted_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    assert result_path == stage_result_path
    stage_result_text = stage_result_path.read_text(encoding="utf-8")
    assert "- `failed`" in stage_result_text
    assert "validator report verdict: `fail`" in stage_result_text
    assert "validation `fail`" in stage_result_text
    assert "Repair budget status: `repair-budget-exhausted`" in stage_result_text


def test_reconcile_stage_result_after_validation_pass_rewrites_stale_failure_claims(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _stage_result_path(workspace_root)
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    stage_result_path.write_text(
        "# Stage result\n\n"
        "## Status\n\n"
        "- Status: `blocked`\n\n"
        "## Validation summary\n\n"
        "- Validator verdict: `fail`\n"
        "- Validator report: `workitems/WI-001/stages/plan/validator-report.md`\n\n"
        "## Terminal state notes\n\n"
        "- Runtime draft stopped before canonical validation was persisted.\n",
        encoding="utf-8",
    )

    result_path = reconcile_stage_result_after_validation_pass(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    assert result_path == stage_result_path
    stage_result_text = stage_result_path.read_text(encoding="utf-8")
    assert "- Status: `succeeded`" in stage_result_text
    assert "- Validator verdict: `pass`" in stage_result_text
    assert "stale runtime draft status/verdict was normalized" in stage_result_text


def test_reconcile_stage_result_after_validation_pass_removes_stale_terminal_note(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _stage_result_path(workspace_root)
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    stage_result_path.write_text(
        "# Stage result\n\n"
        "## Status\n\n"
        "- Status: `failed`\n\n"
        "## Validation summary\n\n"
        "- Validator verdict: `fail`\n"
        "- Validator report: `workitems/WI-001/stages/review/validator-report.md`\n\n"
        "## Terminal state notes\n\n"
        "- Stage ended as `failed` because `review-report.md` rejected the "
        "implementation.\n"
        "- Review status: `rejected`; operator remediation required.\n",
        encoding="utf-8",
    )

    result_path = reconcile_stage_result_after_validation_pass(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    assert result_path == stage_result_path
    stage_result_text = stage_result_path.read_text(encoding="utf-8")
    assert "- Status: `succeeded`" in stage_result_text
    assert "- Validator verdict: `pass`" in stage_result_text
    assert "Stage ended as `failed`" not in stage_result_text
    assert "stale terminal-status text was removed" in stage_result_text
    assert "Review status: `rejected`; operator remediation required." in stage_result_text


def test_reconcile_stage_result_after_validation_pass_does_not_note_clean_result(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _write_successful_stage_result(workspace_root)

    result_path = reconcile_stage_result_after_validation_pass(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    assert result_path == stage_result_path
    stage_result_text = stage_result_path.read_text(encoding="utf-8")
    assert "stale runtime draft status/verdict was normalized" not in stage_result_text


def test_force_stage_result_failed_for_exhausted_budget_creates_missing_result(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"

    stage_result_path = force_stage_result_failed_for_exhausted_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    stage_result_text = stage_result_path.read_text(encoding="utf-8")
    assert "## Status\n\n- `failed`" in stage_result_text
    assert "Repair budget status: `repair-budget-exhausted`" in stage_result_text


def test_strip_success_claims_for_validator_findings_keeps_result_file(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _write_successful_stage_result(workspace_root)

    result_path = strip_stage_result_success_claims_for_validator_findings(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    assert result_path == stage_result_path
    stage_result_text = stage_result_path.read_text(encoding="utf-8")
    assert "- `failed`" in stage_result_text
    assert "validator report verdict: `fail`" in stage_result_text
    assert "canonical aidd validation found open findings" in stage_result_text.lower()


def test_ensure_stage_result_references_repair_brief_appends_trace_note(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _write_successful_stage_result(workspace_root)
    repair_brief_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "repair-brief.md"
    )
    repair_brief_path.write_text("# Repair brief\n", encoding="utf-8")

    result_path = ensure_stage_result_references_repair_brief(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
        repair_brief_path=repair_brief_path,
    )

    assert result_path == stage_result_path
    stage_result_text = stage_result_path.read_text(encoding="utf-8")
    assert (
        "- Repair decision context recorded in "
        "`workitems/WI-001/stages/plan/repair-brief.md`."
    ) in stage_result_text


def test_exhausted_budget_validation_finding_points_at_stage_result(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _write_successful_stage_result(workspace_root)

    finding = exhausted_budget_validation_finding(
        workspace_root=workspace_root,
        stage_result_path=stage_result_path,
    )

    assert finding.code == "CROSS-REPAIR-BUDGET-EXHAUSTED"
    assert finding.severity == "critical"
    assert finding.location is not None
    assert (
        finding.location.workspace_relative_path
        == "workitems/WI-001/stages/plan/stage-result.md"
    )

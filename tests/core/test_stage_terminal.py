from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.models.run import RepairHistoryEntry
from aidd.core.stage_terminal import (
    CanonicalStageResultProjection,
    ensure_repair_brief_records_exhausted_budget,
    ensure_stage_result_references_repair_brief,
    exhausted_budget_validation_finding,
    force_stage_result_failed_for_exhausted_budget,
    normalize_success_stage_result_blockers_if_empty,
    prepare_bootstrap_stage_result_for_validation,
    reconcile_stage_result_after_validation_pass,
    render_stage_result_from_lifecycle_state,
    repair_brief_exhausts_terminal_budget,
    strip_stage_result_success_claims_for_validator_findings,
)
from aidd.core.workspace import STAGE_RESULT_BOOTSTRAP_TEMPLATE


@pytest.mark.parametrize("runtime_suffix", ("", "\nRuntime-authored extra evidence.\n"))
def test_bootstrap_context_projection_is_idempotent_and_preserves_runtime_drafts(
    tmp_path: Path, runtime_suffix: str,
) -> None:
    stage_root = tmp_path / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True)
    context = tmp_path / "workitems" / "WI-001" / "context" / "project-set.md"
    context.parent.mkdir()
    context.write_text("# Project set\n\n| `api` | `services/api` | `primary` |\n")
    stage_result = stage_root / "stage-result.md"
    original = STAGE_RESULT_BOOTSTRAP_TEMPLATE + runtime_suffix
    stage_result.write_text(original)

    recognized = prepare_bootstrap_stage_result_for_validation(
        workspace_root=tmp_path, work_item="WI-001", stage="plan",
    )
    prepared = stage_result.read_text()
    assert recognized is (not runtime_suffix)
    if runtime_suffix:
        assert prepared == original
    else:
        assert "## Project-set evidence" in prepared
        assert "`api` at `services/api`" in prepared
        assert "## Status" not in prepared
        assert "Validator verdict" not in prepared
        assert prepare_bootstrap_stage_result_for_validation(
            workspace_root=tmp_path, work_item="WI-001", stage="plan",
        )
        assert stage_result.read_text() == prepared


def test_render_stage_result_from_lifecycle_state_is_byte_stable_and_replaces_todo() -> None:
    projection = CanonicalStageResultProjection(
        stage="plan",
        work_item="WI-001",
        status="succeeded",
        attempt_number=2,
        attempt_mode="repair",
        attempt_outcome="validated",
        repair_history=(
            RepairHistoryEntry(
                attempt_number=1,
                trigger="initial",
                outcome="failed validation",
                recorded_at_utc="2026-08-21T10:00:00Z",
                validator_report_path="workitems/WI-001/stages/plan/validator-report.md",
                repair_brief_path="workitems/WI-001/stages/plan/repair-brief.md",
            ),
        ),
        validator_verdict="pass",
        validator_report_path="workitems/WI-001/stages/plan/validator-report.md",
        terminal_notes=("Terminal state notes: TODO",),
    )

    first = render_stage_result_from_lifecycle_state(
        projection,
        workspace_root=Path(".aidd"),
    )
    second = render_stage_result_from_lifecycle_state(
        projection,
        workspace_root=Path(".aidd"),
    )

    assert first == second
    assert "Terminal state notes: TODO" not in first
    assert "Attempt `1` (`initial`) -> failed validation." in first
    assert "Attempt `2` (`repair`) -> validated." in first
    assert "Validator verdict: pass" in first
    assert "workitems/WI-001/stages/plan/validator-report.md" in first
    assert "Advance to the immediate canonical `review-spec` stage." in first


@pytest.mark.parametrize(
    ("status", "expected"),
    (("succeeded", "succeeded"), ("failed", "failed")),
)
def test_render_stage_result_from_lifecycle_state_emits_one_status_marker(
    status: str,
    expected: str,
) -> None:
    markdown = render_stage_result_from_lifecycle_state(
        CanonicalStageResultProjection(
            stage="review",
            work_item="WI-001",
            status=status,
            attempt_number=1,
        ),
        workspace_root=Path(".aidd"),
    )

    status_body = markdown.split("## Status\n\n", 1)[1].split("\n## Produced outputs", 1)[0]
    assert status_body == f"- Status: `{expected}`\n"
    assert f"- `{expected}`" not in status_body


@pytest.mark.parametrize(
    ("lifecycle_status", "expected_status", "budget", "expected_text"),
    (
        ("succeeded", "succeeded", None, "Validator verdict: pass"),
        ("failed", "failed", None, "needs operator action"),
        ("blocked", "blocked", None, "blocking question"),
        ("repair-needed", "failed", "repair-budget-available", "bounded repair"),
        (
            "failed",
            "failed",
            "repair-budget-exhausted",
            "no automatic repair remains",
        ),
    ),
)
def test_render_stage_result_from_lifecycle_state_maps_state_matrix(
    lifecycle_status: str,
    expected_status: str,
    budget: str | None,
    expected_text: str,
) -> None:
    markdown = render_stage_result_from_lifecycle_state(
        CanonicalStageResultProjection(
            stage="plan",
            work_item="WI-001",
            status=lifecycle_status,
            attempt_number=1,
            attempt_outcome="blocked" if lifecycle_status == "blocked" else "failed",
            validator_verdict=(
                "pass"
                if lifecycle_status == "succeeded"
                else "blocked"
                if lifecycle_status == "blocked"
                else "fail"
            ),
            validator_report_path="workitems/WI-001/stages/plan/validator-report.md",
            blockers=("Blocking question `Q1` remains unresolved.",)
            if lifecycle_status == "blocked"
            else (),
            repair_budget_status=budget,
        ),
        workspace_root=Path(".aidd"),
    )

    assert f"- Status: `{expected_status}`" in markdown
    assert expected_text in markdown


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
    assert "- Status: `failed`" in stage_result_text
    assert stage_result_text.count("- Status:") == 1
    assert "validator report verdict: `fail`" in stage_result_text
    assert "validation `fail`" in stage_result_text
    assert "Repair budget status: `repair-budget-exhausted`" in stage_result_text


def test_force_stage_result_failed_canonicalizes_conflicting_status_markers(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _stage_result_path(workspace_root)
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    stage_result_path.write_text(
        "# Stage Result\n\n"
        "## Attempt history\n\n"
        "- Attempt `1` (`initial`) -> failed validation.\n\n"
        "## Status\n\n"
        "- Status: `succeeded`\n"
        "- `failed`\n"
        "- Status: `blocked`\n\n"
        "## Terminal state notes\n\n"
        "- Preserve this historical note.\n",
        encoding="utf-8",
    )

    force_stage_result_failed_for_exhausted_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    reconciled = stage_result_path.read_text(encoding="utf-8")
    status_body = reconciled.split("## Status\n\n", 1)[1].split(
        "\n## Terminal state notes", 1
    )[0]
    assert status_body == "- Status: `failed`\n"
    assert "Attempt `1` (`initial`) -> failed validation." in reconciled
    assert "Preserve this historical note." in reconciled


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


def test_reconcile_stage_result_after_validation_pass_normalizes_success_blockers(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _stage_result_path(workspace_root)
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    stage_result_path.write_text(
        "# Stage Result\n\n"
        "## Status\n\n- Status: `succeeded`\n\n"
        "## Validation summary\n\n- Validator verdict: `pass`\n\n"
        "## Blockers\n\nNo blockers.\n",
        encoding="utf-8",
    )

    reconcile_stage_result_after_validation_pass(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )

    assert "## Blockers\n\n- none\n" in stage_result_path.read_text(encoding="utf-8")


def test_normalize_success_stage_result_blockers_if_empty_repairs_prose(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _stage_result_path(workspace_root)
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    stage_result_path.write_text(
        "# Stage Result\n\n"
        "## Status\n\n- Status: `succeeded`\n\n"
        "## Blockers\n\nNo blockers.\n",
        encoding="utf-8",
    )

    assert normalize_success_stage_result_blockers_if_empty(stage_result_path) is True
    assert "## Blockers\n\n- none\n" in stage_result_path.read_text(encoding="utf-8")


def test_normalize_success_stage_result_blockers_if_empty_preserves_concrete_blocker(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    stage_result_path = _stage_result_path(workspace_root)
    stage_result_path.parent.mkdir(parents=True, exist_ok=True)
    original = (
        "# Stage Result\n\n"
        "## Status\n\n- Status: `succeeded`\n\n"
        "## Blockers\n\n- unresolved blocking question `Q1`.\n"
    )
    stage_result_path.write_text(original, encoding="utf-8")

    assert normalize_success_stage_result_blockers_if_empty(stage_result_path) is False
    assert stage_result_path.read_text(encoding="utf-8") == original


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
    assert "## Status\n\n- Status: `failed`" in stage_result_text
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
    assert "- Status: `failed`" in stage_result_text
    assert stage_result_text.count("- Status:") == 1
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

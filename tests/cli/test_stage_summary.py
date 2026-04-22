from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
)

runner = CliRunner()


def test_stage_summary_reports_final_state_runtime_and_attempt_count(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    now = datetime.now(UTC).replace(microsecond=0)
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"

    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="claude-code",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status="failed",
        changed_at_utc=now + timedelta(minutes=5),
    )
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "validator-report.md").write_text(
        (
            "# Validator Report\n\n"
            "## Result\n\n"
            "- Verdict: `fail`\n"
            "- Repair required for progression: yes\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "repair-brief.md").write_text(
        "# Repair brief\n\n- Fix missing sections.\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "summary",
            "plan",
            "--work-item",
            "WI-001",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code == 0
    assert "Stage summary: plan / WI-001" in result.stdout
    assert "run id" in result.stdout
    assert "run-001" in result.stdout
    assert "runtime" in result.stdout
    assert "claude-code" in result.stdout
    assert "final state" in result.stdout
    assert "failed" in result.stdout
    assert "attempt count" in result.stdout
    assert "2" in result.stdout
    assert "validator pass count" in result.stdout
    assert "0" in result.stdout
    assert "validator fail count" in result.stdout
    assert "1" in result.stdout
    assert "validator report" in result.stdout
    assert "workitems/WI-001/stages/plan/validator-report.md" in result.stdout
    assert "log artifacts" in result.stdout
    assert "reports/runs/WI-001/run-001/stages/plan/attempts/" in result.stdout
    assert "document artifacts" in result.stdout
    assert "workitems/WI-001/stages/plan/stage-result.md" in result.stdout
    assert "repair outputs" in result.stdout
    assert "workitems/WI-001/stages/plan/repair-brief.md" in result.stdout


def test_stage_summary_rejects_missing_runs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    result = runner.invoke(
        app,
        [
            "stage",
            "summary",
            "plan",
            "--work-item",
            "WI-404",
            "--root",
            str(workspace_root),
        ],
    )

    assert result.exit_code != 0
    assert "No runs found for work item 'WI-404'." in result.output

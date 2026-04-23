from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

from typer.testing import CliRunner

from aidd.cli.main import app
from aidd.core.workspace import WorkspaceBootstrapService

runner = CliRunner()


def _write_required_stage_inputs(*, workspace_root: Path, work_item: str) -> None:
    context_root = workspace_root / "workitems" / work_item / "context"
    context_root.mkdir(parents=True, exist_ok=True)
    (context_root / "intake.md").write_text(
        "# Intake\n\nShip runtime-agnostic execution.\n",
        encoding="utf-8",
    )
    (context_root / "user-request.md").write_text(
        "# User request\n\nNeed reproducible stage output validation.\n",
        encoding="utf-8",
    )


def _write_runtime_writer_script(path: Path) -> None:
    script = dedent(
        """
        import os
        from pathlib import Path

        workspace_root = Path(os.environ["AIDD_WORKSPACE_ROOT"])
        work_item = os.environ["AIDD_WORK_ITEM"]
        stage = os.environ["AIDD_STAGE"]
        stage_root = workspace_root / "workitems" / work_item / "stages" / stage
        stage_root.mkdir(parents=True, exist_ok=True)

        (stage_root / "idea-brief.md").write_text(
            "# Idea Brief\\n\\n"
            "## Problem statement\\n\\nNeed governed workflow portability.\\n\\n"
            "## Desired outcome\\n\\nPass deterministic validator gates.\\n\\n"
            "## Constraints\\n\\n- Keep Markdown as contract surface.\\n\\n"
            "## Open questions\\n\\n- none\\n",
            encoding="utf-8",
        )
        (stage_root / "stage-result.md").write_text(
            "# Stage\\n\\nidea\\n\\n"
            "## Attempt history\\n\\n- Attempt `1` (`initial`) -> succeeded.\\n\\n"
            "## Status\\n\\n- `succeeded`\\n\\n"
            "## Produced outputs\\n\\n"
            "- `workitems/WI-001/stages/idea/idea-brief.md`\\n"
            "- `workitems/WI-001/stages/idea/stage-result.md`\\n"
            "- `workitems/WI-001/stages/idea/validator-report.md`\\n"
            "- `workitems/WI-001/stages/idea/repair-brief.md`\\n"
            "- `workitems/WI-001/stages/idea/questions.md`\\n"
            "- `workitems/WI-001/stages/idea/answers.md`\\n\\n"
            "## Validation summary\\n\\n- Validator verdict: `pass`.\\n\\n"
            "## Blockers\\n\\n- none\\n\\n"
            "## Next actions\\n\\n- Advance to `research`.\\n\\n"
            "## Terminal state notes\\n\\n- `repair-brief.md` kept.\\n",
            encoding="utf-8",
        )
        (stage_root / "validator-report.md").write_text(
            "# Validator Report\\n\\n"
            "## Summary\\n\\n- Total issues: 0\\n- Blocking issues: no\\n"
            "- Affected documents: none\\n- Dominant failure categories: none\\n\\n"
            "## Structural checks\\n\\n- none\\n\\n"
            "## Semantic checks\\n\\n- none\\n\\n"
            "## Cross-document checks\\n\\n- none\\n\\n"
            "## Result\\n\\n- Verdict: `pass`\\n- Repair required for progression: no\\n",
            encoding="utf-8",
        )
        (stage_root / "repair-brief.md").write_text(
            "# Failed checks\\n\\n- none\\n\\n"
            "# Required corrections\\n\\n- none\\n\\n"
            "# Relevant upstream docs\\n\\n- none\\n\\n"
            "Repair attempt context: attempt `1` of max `3`; "
            "remaining retries after this attempt: `2`.\\n",
            encoding="utf-8",
        )
        (stage_root / "questions.md").write_text(
            "# Questions\\n\\n- none\\n", encoding="utf-8"
        )
        (stage_root / "answers.md").write_text(
            "# Answers\\n\\n- none\\n", encoding="utf-8"
        )
        print("workflow-stage-complete")
        """
    )
    path.write_text(script, encoding="utf-8")


def _write_config(path: Path, *, runtime_writer: Path, workspace_root: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "[workspace]",
                f"root = \"{workspace_root.as_posix()}\"",
                "",
                "[runtime.generic_cli]",
                f"command = \"{sys.executable} {runtime_writer.as_posix()}\"",
                "",
                "[runtime.claude_code]",
                "command = \"claude\"",
                "",
                "[runtime.codex]",
                "command = \"codex\"",
                "",
                "[runtime.opencode]",
                "command = \"opencode\"",
                "",
                "[logging]",
                "mode = \"both\"",
                "",
                "[repair]",
                "max_attempts = 2",
                "",
            )
        ),
        encoding="utf-8",
    )


def test_run_executes_workflow_window_to_target_stage(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    WorkspaceBootstrapService(root=workspace_root).bootstrap_work_item(work_item="WI-001")
    _write_required_stage_inputs(workspace_root=workspace_root, work_item="WI-001")
    runtime_writer = tmp_path / "runtime_writer.py"
    _write_runtime_writer_script(runtime_writer)
    config_path = tmp_path / "aidd.toml"
    _write_config(config_path, runtime_writer=runtime_writer, workspace_root=workspace_root)

    result = runner.invoke(
        app,
        [
            "run",
            "--work-item",
            "WI-001",
            "--runtime",
            "generic-cli",
            "--stage-start",
            "idea",
            "--stage-target",
            "idea",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0
    assert "AIDD run: run_id=" in result.stdout
    assert "final_state=succeeded" in result.stdout
    assert "Executed stages: 1" in result.stdout
    assert "- idea: state=succeeded attempts=1 action=advance" in result.stdout

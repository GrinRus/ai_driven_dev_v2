from __future__ import annotations

import json
from pathlib import Path

from aidd.harness.live_e2e_black_box_reports import (
    write_flow_report,
    write_json_markdown_bundle,
)


def test_flow_report_rendering_is_stable(tmp_path: Path) -> None:
    path = write_flow_report(
        path=tmp_path / "flow-report.md",
        scenario_id="scenario",
        runtime_id="generic-cli",
        run_id="run-1",
        work_item="WI-1",
        state={"status": "pass", "next_action": "finish"},
        steps=[
            {
                "step_index": 1,
                "action": "run-stage",
                "stage": "idea",
                "plan": "Run idea.",
                "classification": "pass",
                "decision": "Continue.",
                "commands": [{"command": ["aidd", "stage", "run"], "exit_code": 0}],
            }
        ],
    )

    assert path.read_text(encoding="utf-8") == (
        "# Black-Box Live E2E Flow Report\n"
        "\n"
        "## Run\n"
        "- Scenario: `scenario`\n"
        "- Runtime: `generic-cli`\n"
        "- Run ID: `run-1`\n"
        "- Work item: `WI-1`\n"
        "- Status: `pass`\n"
        "- Next action: `finish`\n"
        "\n"
        "## Steps\n"
        "\n"
        "### 1. run-stage\n"
        "- Stage: `idea`\n"
        "- Plan: Run idea.\n"
        "- Classification: `pass`\n"
        "- Decision: Continue.\n"
        "- Command: `aidd stage run` exit=`0`\n"
    )


def test_json_markdown_bundle_is_published_without_temporary_residue(
    tmp_path: Path,
) -> None:
    json_path, markdown_path = write_json_markdown_bundle(
        json_path=tmp_path / "summary.json",
        markdown_path=tmp_path / "summary.md",
        payload={"schema_version": 1, "status": "pass"},
        markdown="# Summary\n\n- Status: `pass`\n",
    )

    assert json.loads(json_path.read_text(encoding="utf-8"))["status"] == "pass"
    assert markdown_path.read_text(encoding="utf-8") == "# Summary\n\n- Status: `pass`\n"
    assert not list(tmp_path.glob(".*.tmp"))

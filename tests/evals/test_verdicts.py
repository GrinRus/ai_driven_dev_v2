from __future__ import annotations

from pathlib import Path

import pytest

from aidd.evals.verdicts import (
    VERDICT_STATUSES,
    HarnessOutcome,
    build_scenario_verdict,
    map_harness_outcome_to_verdict_status,
    render_scenario_verdict_markdown,
    write_scenario_verdict_markdown,
)


def test_build_scenario_verdict_uses_declared_model_fields() -> None:
    verdict = build_scenario_verdict(
        scenario_id="AIDD-LIVE-001",
        run_id="eval-run-001",
        runtime_id="generic-cli",
        status="pass",
        summary="Scenario completed without validation or verification issues.",
        created_at_utc="2026-04-22T09:00:00Z",
        artifact_links=("reports/evals/eval-run-001/runtime.log",),
        first_failure_note=None,
        verification_summary="Verification commands completed with exit code 0.",
    )

    assert verdict.scenario_id == "AIDD-LIVE-001"
    assert verdict.run_id == "eval-run-001"
    assert verdict.runtime_id == "generic-cli"
    assert verdict.status == "pass"
    assert verdict.summary.startswith("Scenario completed")
    assert verdict.created_at_utc == "2026-04-22T09:00:00Z"
    assert verdict.artifact_links == ("reports/evals/eval-run-001/runtime.log",)
    assert verdict.first_failure_note is None
    assert verdict.verification_summary == "Verification commands completed with exit code 0."


@pytest.mark.parametrize("status", VERDICT_STATUSES)
def test_build_scenario_verdict_accepts_all_supported_statuses(status: str) -> None:
    verdict = build_scenario_verdict(
        scenario_id="AIDD-LIVE-002",
        run_id="eval-run-002",
        runtime_id="generic-cli",
        status=status,
        summary="Terminal status accepted by verdict model.",
        created_at_utc="2026-04-22T09:05:00Z",
    )
    assert verdict.status == status


def test_build_scenario_verdict_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="status must be one of"):
        build_scenario_verdict(
            scenario_id="AIDD-LIVE-003",
            run_id="eval-run-003",
            runtime_id="generic-cli",
            status="document_fail",
            summary="Invalid status for verdict artifact.",
            created_at_utc="2026-04-22T09:10:00Z",
        )


def test_build_scenario_verdict_rejects_blank_artifact_link() -> None:
    with pytest.raises(ValueError, match="artifact_links must contain only non-empty values"):
        build_scenario_verdict(
            scenario_id="AIDD-LIVE-003A",
            run_id="eval-run-003A",
            runtime_id="generic-cli",
            status="fail",
            summary="Invalid artifact links.",
            artifact_links=("reports/evals/eval-run-003A/runtime.log", "   "),
            created_at_utc="2026-04-22T09:11:00Z",
        )


def test_render_scenario_verdict_markdown_uses_stable_layout() -> None:
    verdict = build_scenario_verdict(
        scenario_id="AIDD-LIVE-004",
        run_id="eval-run-004",
        runtime_id="generic-cli",
        status="blocked",
        summary="Run paused because additional user input was required.",
        created_at_utc="2026-04-22T09:15:00Z",
        artifact_links=(
            "reports/evals/eval-run-004/runtime.log",
            "reports/evals/eval-run-004/validator-report.md",
        ),
        first_failure_note="Validation was blocked waiting for user clarification.",
        verification_summary="Verification steps skipped because run terminated as blocked.",
    )

    markdown = render_scenario_verdict_markdown(verdict)

    assert markdown.startswith("# Verdict\n\n## Run\n")
    assert "- Scenario ID: `AIDD-LIVE-004`" in markdown
    assert "- Run ID: `eval-run-004`" in markdown
    assert "- Runtime ID: `generic-cli`" in markdown
    assert "- Created At (UTC): `2026-04-22T09:15:00Z`" in markdown
    assert "## Outcome" in markdown
    assert "- Status: `blocked`" in markdown
    assert "## Evidence" in markdown
    assert "- Artifact: `reports/evals/eval-run-004/runtime.log`" in markdown
    assert "- Artifact: `reports/evals/eval-run-004/validator-report.md`" in markdown
    assert "## Analysis" in markdown
    assert (
        "- First Failure Note: Validation was blocked waiting for user clarification."
        in markdown
    )
    assert (
        "- Verification Summary: Verification steps skipped because run terminated as blocked."
        in markdown
    )
    assert markdown.endswith("\n")


def test_write_scenario_verdict_markdown_persists_file(tmp_path: Path) -> None:
    verdict = build_scenario_verdict(
        scenario_id="AIDD-LIVE-005",
        run_id="eval-run-005",
        runtime_id="generic-cli",
        status="infra-fail",
        summary="Infrastructure error prevented scenario completion.",
        created_at_utc="2026-04-22T09:20:00Z",
        artifact_links=("reports/evals/eval-run-005/runtime.log",),
        first_failure_note="Repository checkout failed before run execution started.",
        verification_summary="Verification did not execute because scenario setup failed.",
    )
    verdict_path = tmp_path / "reports" / "evals" / "eval-run-005" / "verdict.md"

    written_path = write_scenario_verdict_markdown(path=verdict_path, verdict=verdict)

    assert written_path == verdict_path
    content = verdict_path.read_text(encoding="utf-8")
    assert "# Verdict" in content
    assert "- Status: `infra-fail`" in content
    assert "Infrastructure error prevented scenario completion." in content
    assert "- Artifact: `reports/evals/eval-run-005/runtime.log`" in content
    assert "Repository checkout failed before run execution started." in content
    assert "Verification did not execute because scenario setup failed." in content


@pytest.mark.parametrize(
    ("outcome", "expected_status"),
    [
        (
            HarnessOutcome(
                aidd_exit_code=0,
                verification_failed=False,
                blocked_by_questions=False,
                infrastructure_failure=False,
            ),
            "pass",
        ),
        (
            HarnessOutcome(
                aidd_exit_code=2,
                verification_failed=False,
                blocked_by_questions=False,
                infrastructure_failure=False,
            ),
            "fail",
        ),
        (
            HarnessOutcome(
                aidd_exit_code=0,
                verification_failed=True,
                blocked_by_questions=False,
                infrastructure_failure=False,
            ),
            "fail",
        ),
        (
            HarnessOutcome(
                aidd_exit_code=0,
                verification_failed=False,
                blocked_by_questions=True,
                infrastructure_failure=False,
            ),
            "blocked",
        ),
        (
            HarnessOutcome(
                aidd_exit_code=0,
                verification_failed=False,
                blocked_by_questions=True,
                infrastructure_failure=True,
            ),
            "infra-fail",
        ),
    ],
)
def test_map_harness_outcome_to_verdict_status(
    outcome: HarnessOutcome,
    expected_status: str,
) -> None:
    assert map_harness_outcome_to_verdict_status(outcome) == expected_status

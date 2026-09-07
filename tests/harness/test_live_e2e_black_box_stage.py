from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from aidd.harness.live_e2e_black_box_stage import (
    StageLoopDependencies,
    classify_stage_run,
    inspection_reports_unresolved_questions,
    run_stage_loop,
)
from aidd.harness.live_e2e_black_box_steps import BlackBoxCommandResult
from aidd.harness.runner import HarnessCommandTranscript


def _result(
    *,
    command: tuple[str, ...] = ("aidd", "stage", "run"),
    stdout: str = "",
    stderr: str = "",
    exit_code: int = 0,
    no_progress: bool = False,
) -> BlackBoxCommandResult:
    return BlackBoxCommandResult(
        command=command,
        transcript=HarnessCommandTranscript(
            command=" ".join(command),
            exit_code=exit_code,
            stdout_text=stdout,
            stderr_text=stderr,
            duration_seconds=0.01,
        ),
        no_progress=no_progress,
    )


@pytest.mark.parametrize(
    ("result", "expected"),
    (
        (_result(), "pass"),
        (_result(exit_code=1), "fail"),
        (_result(stdout="blocking questions are unresolved"), "blocked"),
        (_result(no_progress=True), "infra-fail"),
    ),
)
def test_classify_stage_run_preserves_terminal_categories(
    result: BlackBoxCommandResult,
    expected: str,
) -> None:
    assert classify_stage_run(result) == expected


def test_inspection_questions_only_use_stage_questions_command() -> None:
    blocked_questions = _result(
        command=("aidd", "stage", "questions"),
        stdout="pending-blocking question",
    )
    unrelated_output = _result(stdout="pending-blocking question")

    assert inspection_reports_unresolved_questions((blocked_questions,)) is True
    assert inspection_reports_unresolved_questions((unrelated_output,)) is False


@dataclass
class _Context:
    bundle_root: Path


def test_run_stage_loop_preserves_stage_order_and_remediation_routing(tmp_path: Path) -> None:
    context = _Context(bundle_root=tmp_path)
    calls: list[tuple[str, str]] = []
    stages = iter(("idea", "research", "plan"))

    def quality_review_gate(_ctx: _Context) -> None:
        return None

    def first_incomplete_stage(_ctx: _Context) -> str | None:
        return next(stages, None)

    def stale_downstream_stages(_bundle_root: Path) -> tuple[str, ...]:
        return ("research",)

    def run_remediation(_ctx: _Context, stage: str) -> str:
        calls.append(("remediation", stage))
        return "pass"

    def run_stage_and_inspect(_ctx: _Context, stage: str) -> str:
        calls.append(("fresh", stage))
        return "pass"

    dependencies = StageLoopDependencies(
        quality_review_gate=quality_review_gate,
        first_incomplete_stage=first_incomplete_stage,
        stale_downstream_stages=stale_downstream_stages,
        run_remediation_rerun_stage=run_remediation,
        run_stage_and_inspect=run_stage_and_inspect,
    )

    assert run_stage_loop(context, dependencies=dependencies) == "pass"
    assert calls == [("fresh", "idea"), ("remediation", "research"), ("fresh", "plan")]


def test_run_stage_loop_stops_at_quality_gate(tmp_path: Path) -> None:
    context = _Context(bundle_root=tmp_path)
    calls: list[str] = []

    def quality_review_gate(_ctx: _Context) -> str:
        return "awaiting-quality-review"

    def first_incomplete_stage(_ctx: _Context) -> str:
        calls.append("first-incomplete")
        return "idea"

    dependencies = StageLoopDependencies(
        quality_review_gate=quality_review_gate,
        first_incomplete_stage=first_incomplete_stage,
        stale_downstream_stages=lambda _root: (),
        run_remediation_rerun_stage=lambda _ctx, _stage: "pass",
        run_stage_and_inspect=lambda _ctx, _stage: "pass",
    )

    assert run_stage_loop(context, dependencies=dependencies) == "awaiting-quality-review"
    assert calls == []

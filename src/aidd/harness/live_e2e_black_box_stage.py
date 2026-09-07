from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from aidd.harness.live_e2e_black_box_steps import BlackBoxCommandResult, StepClassification


class StageContext(Protocol):
    bundle_root: Path


def classify_stage_run(result: BlackBoxCommandResult) -> StepClassification:
    """Classify a public stage command before post-stage inspection."""
    if result.no_progress:
        return "infra-fail"
    output = f"{result.stdout_text}\n{result.stderr_text}".lower()
    if (
        "blocking questions are unresolved" in output
        or "action=wait state=blocked" in output
        or "runtime approval is waiting for operator" in output
    ):
        return "blocked"
    if result.exit_code == 0:
        return "pass"
    return "fail"


def inspection_reports_unresolved_questions(
    results: tuple[BlackBoxCommandResult, ...],
) -> bool:
    """Detect blocking questions only from the public stage-questions command."""
    for result in results:
        if not any(
            result.command[index : index + 2] == ("stage", "questions")
            for index in range(len(result.command) - 1)
        ):
            continue
        output = f"{result.stdout_text}\n{result.stderr_text}".lower()
        if (
            "blocking questions are unresolved" in output
            or "pending-blocking" in output
            or "action=wait state=blocked" in output
        ):
            return True
    return False


@dataclass(frozen=True, slots=True)
class StageLoopDependencies[StageContextT: StageContext]:
    """Runtime-neutral callbacks used by the public stage-loop coordinator."""

    quality_review_gate: Callable[[StageContextT], StepClassification | None]
    first_incomplete_stage: Callable[[StageContextT], str | None]
    stale_downstream_stages: Callable[[Path], tuple[str, ...]]
    run_remediation_rerun_stage: Callable[[StageContextT, str], StepClassification]
    run_stage_and_inspect: Callable[[StageContextT, str], StepClassification]


def run_stage_loop[StageContextT: StageContext](
    ctx: StageContextT,
    *,
    dependencies: StageLoopDependencies[StageContextT],
) -> StepClassification:
    """Advance the public stage loop until a terminal or operator state is reached."""
    while True:
        quality_gate = dependencies.quality_review_gate(ctx)
        if quality_gate is not None:
            return quality_gate
        stage = dependencies.first_incomplete_stage(ctx)
        if stage is None:
            return "pass"
        if stage in dependencies.stale_downstream_stages(ctx.bundle_root):
            classification = dependencies.run_remediation_rerun_stage(ctx, stage)
        else:
            classification = dependencies.run_stage_and_inspect(ctx, stage)
        if classification != "pass":
            return classification


__all__ = [
    "StageLoopDependencies",
    "StageContext",
    "StepClassification",
    "classify_stage_run",
    "inspection_reports_unresolved_questions",
    "run_stage_loop",
]

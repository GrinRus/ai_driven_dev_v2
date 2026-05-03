from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer
from rich.table import Table

from aidd.cli.run_lookup import resolve_stage_result_summary
from aidd.cli.support import _path_summary, console
from aidd.core.interview import (
    load_answers_document,
    load_questions_document,
    resolved_question_ids,
    stage_has_unresolved_blocking_questions,
)
from aidd.core.stages import STAGES, is_valid_stage


@dataclass(frozen=True, slots=True)
class StageQuestionsOptions:
    stage: str
    work_item: str
    root: Path


@dataclass(frozen=True, slots=True)
class StageSummaryOptions:
    stage: str
    work_item: str
    root: Path
    run_id: str | None


def _validate_stage_name(stage: str) -> None:
    if not is_valid_stage(stage):
        raise typer.BadParameter(
            f"Unknown stage '{stage}'. Expected one of: {', '.join(STAGES)}"
        )


def show_stage_questions(options: StageQuestionsOptions) -> None:
    _validate_stage_name(options.stage)

    questions = load_questions_document(
        workspace_root=options.root,
        work_item=options.work_item,
        stage=options.stage,
    )
    if not questions:
        console.print("No stage questions recorded.")
        return

    resolved_ids: set[str] = set()
    answers_path = (
        options.root
        / "workitems"
        / options.work_item
        / "stages"
        / options.stage
        / "answers.md"
    )
    if answers_path.exists():
        resolved_ids = set(
            resolved_question_ids(
                answers=load_answers_document(
                    workspace_root=options.root,
                    work_item=options.work_item,
                    stage=options.stage,
                )
            )
        )

    table = Table(title=f"Stage questions: {options.stage} / {options.work_item}")
    table.add_column("Question id")
    table.add_column("Policy")
    table.add_column("Status")
    table.add_column("Text")
    for question in questions:
        if question.question_id in resolved_ids:
            status = "resolved"
        elif question.policy.value == "blocking":
            status = "pending-blocking"
        else:
            status = "pending-non-blocking"
        table.add_row(question.question_id, question.policy.value, status, question.text)
    console.print(table)

    if stage_has_unresolved_blocking_questions(
        workspace_root=options.root,
        work_item=options.work_item,
        stage=options.stage,
    ):
        console.print(
            "Blocking questions are unresolved. Add `[resolved]` answers in "
            f"`{answers_path.as_posix()}` before progressing this stage."
        )
        return

    console.print("No unresolved blocking questions. Stage can proceed if other checks pass.")


def show_stage_summary(options: StageSummaryOptions) -> None:
    _validate_stage_name(options.stage)

    try:
        summary = resolve_stage_result_summary(
            workspace_root=options.root,
            work_item=options.work_item,
            stage=options.stage,
            run_id=options.run_id,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    table = Table(title=f"Stage summary: {options.stage} / {options.work_item}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("run id", summary.run_id)
    table.add_row("runtime", summary.runtime_id)
    table.add_row("final state", summary.final_state)
    table.add_row("attempt count", str(summary.attempt_count))
    table.add_row("validator pass count", str(summary.validator_pass_count))
    table.add_row("validator fail count", str(summary.validator_fail_count))
    table.add_row("validator report", summary.validator_report_path)
    table.add_row("log artifacts", _path_summary(summary.log_artifact_paths))
    table.add_row("document artifacts", _path_summary(summary.document_artifact_paths))
    table.add_row("repair outputs", _path_summary(summary.repair_output_paths))
    console.print(table)

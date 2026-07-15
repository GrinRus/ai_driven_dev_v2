from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path

from aidd.core.implementation_service import AggregateFinalizationOutcome
from aidd.core.run_store import persist_stage_status
from aidd.core.stage_outputs import publish_stage_outputs_after_validation_pass
from aidd.core.state_machine import StageState
from aidd.core.task_execution import (
    TaskFinalizationContext,
    load_task_execution_plan,
    render_aggregate_implementation_report,
)
from aidd.core.workspace import stage_root as workspace_stage_root
from aidd.validators.reports import write_validator_report
from aidd.validators.semantic import validate_semantic_outputs


def _copy_finalization_artifacts(stage_root: Path, attempt_path: Path) -> None:
    for name in ("implementation-report.md", "validator-report.md", "stage-result.md"):
        source = stage_root / name
        if source.exists():
            shutil.copy2(source, attempt_path / name)


def aggregate_finalization_port(
    *, workspace_root: Path, work_item: str, run_id: str
) -> Callable[[TaskFinalizationContext], AggregateFinalizationOutcome]:
    def _finalize(context: TaskFinalizationContext) -> AggregateFinalizationOutcome:
        stage_root = workspace_stage_root(
            root=workspace_root,
            work_item=work_item,
            stage="implement",
        )
        diagnostics_path = context.attempt_path / "publication-diagnostics.json"
        try:
            plan = load_task_execution_plan(
                workspace_root=workspace_root,
                work_item=work_item,
            )
            report = render_aggregate_implementation_report(
                plan=plan,
                ledger=context.ledger,
                workspace_root=workspace_root,
            )
            (stage_root / "implementation-report.md").write_text(report, encoding="utf-8")
            findings = validate_semantic_outputs(
                stage="implement",
                work_item=work_item,
                workspace_root=workspace_root,
            )
            write_validator_report(
                path=stage_root / "validator-report.md",
                findings=findings,
            )
            _copy_finalization_artifacts(stage_root, context.attempt_path)
            if findings:
                raise ValueError("Aggregate implementation report failed validation.")
            publish_stage_outputs_after_validation_pass(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage="implement",
            )
            persist_stage_status(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage="implement",
                status=StageState.SUCCEEDED.value,
            )
            diagnostics_path.write_text(
                json.dumps({"status": "succeeded"}, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return AggregateFinalizationOutcome(succeeded=True, published=True)
        except Exception as exc:
            blocker = str(exc) or exc.__class__.__name__
            diagnostics_path.write_text(
                json.dumps(
                    {"status": "failed", "error": blocker},
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            _copy_finalization_artifacts(stage_root, context.attempt_path)
            persist_stage_status(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage="implement",
                status=StageState.FAILED.value,
            )
            raise

    return _finalize


__all__ = ["aggregate_finalization_port"]

from __future__ import annotations

import ast
from pathlib import Path

from aidd.harness import live_e2e_black_box_frontend as frontend
from aidd.harness import live_e2e_black_box_orchestration as orchestration
from aidd.harness import live_e2e_black_box_reports as reports
from aidd.harness import live_e2e_black_box_stage as stage
from aidd.harness import live_e2e_black_box_steps as steps


def test_orchestration_reexports_canonical_steps_process_surface() -> None:
    assert orchestration.BlackBoxCommandResult is steps.BlackBoxCommandResult
    assert orchestration.LiveE2EInterrupted is steps.LiveE2EInterrupted
    assert orchestration._run_black_box_command is steps._run_black_box_command
    assert orchestration._terminate_process is steps._terminate_process


def test_orchestration_does_not_define_canonical_process_helpers() -> None:
    source_path = Path(orchestration.__file__)
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    defined_names = {
        node.name
        for node in module.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
    }

    assert "BlackBoxCommandResult" not in defined_names
    assert "LiveE2EInterrupted" not in defined_names
    assert "_run_black_box_command" not in defined_names
    assert "_terminate_process" not in defined_names


def test_orchestration_uses_reports_owned_serialization_helpers() -> None:
    assert orchestration._write_json is reports._write_json
    assert orchestration._write_text_atomic is reports._write_text_atomic
    assert orchestration._write_step_transcript is reports._write_step_transcript


def test_harness_does_not_import_core_stage_status_persistence() -> None:
    harness_root = Path(orchestration.__file__).parent
    violations: list[str] = []
    for source_path in harness_root.glob("*.py"):
        module = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != "aidd.core.run_store":
                continue
            if any(alias.name == "persist_stage_status" for alias in node.names):
                violations.append(source_path.name)

    assert violations == []


def test_orchestration_reexports_canonical_stage_decisions() -> None:
    assert orchestration._classify_stage_run is stage.classify_stage_run
    assert (
        orchestration._inspection_reports_unresolved_questions
        is stage.inspection_reports_unresolved_questions
    )


def test_orchestration_delegates_stage_loop_to_stage_module() -> None:
    source_path = Path(orchestration.__file__)
    source = source_path.read_text(encoding="utf-8")

    assert "return _stage_run_stage_loop(" in source
    assert "run_stage_loop" in stage.__dict__


def test_orchestration_reexports_canonical_frontend_probe_surface() -> None:
    assert orchestration._http_probe is frontend.http_probe
    assert orchestration._http_post_json is frontend.http_post_json
    assert orchestration._frontend_probe_targets is frontend.frontend_probe_targets
    assert (
        orchestration._frontend_probe_semantic_failure
        is frontend.frontend_probe_semantic_failure
    )
    assert (
        orchestration._frontend_operator_surface_checks
        is frontend.frontend_operator_surface_checks
    )


def test_orchestration_uses_one_frontend_probe_owner() -> None:
    source_path = Path(orchestration.__file__)
    source = source_path.read_text(encoding="utf-8")

    assert "_frontend_probe_targets = _frontend_probe_targets_extracted" in source
    assert (
        "_frontend_probe_semantic_failure = _frontend_probe_semantic_failure_extracted"
        in source
    )
    assert (
        "_frontend_operator_surface_checks = _frontend_operator_surface_checks_extracted"
        in source
    )

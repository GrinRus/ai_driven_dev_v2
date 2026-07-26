from __future__ import annotations

import ast
from pathlib import Path

from aidd.harness import live_e2e_black_box_orchestration as orchestration
from aidd.harness import live_e2e_black_box_reports as reports
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

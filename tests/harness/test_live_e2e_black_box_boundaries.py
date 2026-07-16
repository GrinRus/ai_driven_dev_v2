from __future__ import annotations

import ast
from pathlib import Path

from aidd.harness import live_e2e_black_box_orchestration as orchestration
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

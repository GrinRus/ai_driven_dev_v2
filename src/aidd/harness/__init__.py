"""Harness helpers."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aidd.harness.eval_runner import EvalScenarioRunResult, run_eval_scenario

__all__ = ["EvalScenarioRunResult", "run_eval_scenario"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        eval_runner = importlib.import_module("aidd.harness.eval_runner")
        return getattr(eval_runner, name)
    raise AttributeError(f"module 'aidd.harness' has no attribute {name!r}")

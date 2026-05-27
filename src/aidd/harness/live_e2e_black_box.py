from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from aidd.harness import live_e2e_black_box_orchestration as _orchestration
from aidd.harness.eval_preparation import derive_run_id
from aidd.harness.install_artifact import prepare_local_wheel_install
from aidd.harness.live_e2e_black_box_orchestration import (
    BlackBoxLiveE2EResult,
    _harness_environment,
    _implementation_verification_evidence_shape,
)
from aidd.harness.live_e2e_black_box_steps import BlackBoxCommandResult


def _sync_monkeypatchable_dependencies() -> None:
    orchestration = cast(Any, _orchestration)
    orchestration.derive_run_id = derive_run_id
    orchestration.prepare_local_wheel_install = prepare_local_wheel_install


def run_black_box_live_e2e(
    *,
    scenario_path: Path,
    runtime_id: str,
    work_root: Path | None = None,
    report_root: Path = Path(".aidd/reports/evals"),
    run_id: str | None = None,
) -> BlackBoxLiveE2EResult:
    _sync_monkeypatchable_dependencies()
    return _orchestration.run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id=runtime_id,
        work_root=work_root,
        report_root=report_root,
        run_id=run_id,
    )


def main(argv: Sequence[str] | None = None) -> int:
    _sync_monkeypatchable_dependencies()
    return _orchestration.main(argv)


__all__ = [
    "BlackBoxCommandResult",
    "BlackBoxLiveE2EResult",
    "_harness_environment",
    "_implementation_verification_evidence_shape",
    "derive_run_id",
    "main",
    "prepare_local_wheel_install",
    "run_black_box_live_e2e",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aidd.core.resources import ResourceLayout
    from aidd.evals.log_analysis import FailureBoundarySelection
    from aidd.evals.verdicts import VerdictStatus
    from aidd.harness.install_artifact import HarnessInstallResult
    from aidd.harness.repo_prep import PreparedRepository, PreparedWorkingCopy
    from aidd.harness.result_bundle import ResultBundleLayout
    from aidd.harness.runner import (
        HarnessAiddRunResult,
        HarnessQualityResult,
        HarnessSetupResult,
        HarnessTeardownResult,
        HarnessVerificationResult,
    )
    from aidd.harness.scenarios import Scenario, ScenarioAuthoredTask


@dataclass(frozen=True, slots=True)
class EvalScenarioRunResult:
    scenario_id: str
    run_id: str
    runtime_id: str
    status: VerdictStatus
    bundle_root: Path
    verdict_path: Path
    summary_path: Path
    quality_gate: str
    quality_verdict: str
    quality_report_path: Path
    feature_selection_path: Path
    first_failure_boundary: FailureBoundarySelection
    first_failure_note: str | None


@dataclass(frozen=True, slots=True)
class EvalRunPreparation:
    scenario_path: Path
    scenario: Scenario
    run_id: str
    runtime_id: str
    workspace_root: Path
    source_repository_root: Path | None
    layout: ResultBundleLayout
    cache_root: Path
    live_scenario: bool
    published_package_spec: str | None
    resource_layout: ResourceLayout
    aidd_command: tuple[str, ...] | None
    work_item: str
    selected_task: ScenarioAuthoredTask | None
    feature_selection_payload: dict[str, object]
    teardown_commands: tuple[str, ...]


@dataclass(slots=True)
class EvalExecutionState:
    prep_error: BaseException | None = None
    install_error: BaseException | None = None
    setup_error: BaseException | None = None
    run_error: BaseException | None = None
    verification_error: BaseException | None = None
    quality_error: BaseException | None = None
    teardown_error: BaseException | None = None
    prepared_repository: PreparedRepository | None = None
    prepared_working_copy: PreparedWorkingCopy | None = None
    install_result: HarnessInstallResult | None = None
    setup_result: HarnessSetupResult | None = None
    aidd_run_result: HarnessAiddRunResult | None = None
    verification_result: HarnessVerificationResult | None = None
    quality_result: HarnessQualityResult | None = None
    teardown_result: HarnessTeardownResult | None = None
    live_runtime_config_path: Path | None = None


@dataclass(frozen=True, slots=True)
class EvalClassification:
    status: VerdictStatus
    summary: str
    blocked_by_questions: bool
    infrastructure_failure: bool
    verification_failed: bool


@dataclass(frozen=True, slots=True)
class EvalReportPersistenceContext:
    prep: EvalRunPreparation
    state: EvalExecutionState
    classification: EvalClassification
    started: float


@dataclass(frozen=True, slots=True)
class EvalRuntimeLogSourceContext:
    prep: EvalRunPreparation
    state: EvalExecutionState


__all__ = [
    "EvalClassification",
    "EvalExecutionState",
    "EvalReportPersistenceContext",
    "EvalRunPreparation",
    "EvalRuntimeLogSourceContext",
    "EvalScenarioRunResult",
]

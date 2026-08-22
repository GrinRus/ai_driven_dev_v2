"""Provider-free scenarios for the one-shot repair-extension recovery protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from aidd.core.models.run import RepairExtensionGrant
from aidd.core.repair import (
    RepairExtensionPreflightResult,
    ValidatorReportFinding,
    evaluate_stage_repair_counter,
    persist_repair_history_snapshot,
    preflight_repair_extension,
)
from aidd.core.run_store import (
    create_run_manifest,
    load_attempt_artifact_index,
    load_stage_metadata,
    persist_stage_status,
    write_attempt_artifact_index,
)
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.state_machine import StageState
from aidd.core.workspace import stage_root
from aidd.validators.models import ValidationFinding
from aidd.validators.reports import render_validator_report

REPAIR_EXTENSION_SCENARIO_SCHEMA_VERSION = 1
DEFAULT_REPAIR_EXTENSION_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "w43-e5-s1-t2-repair-extension"
)
_SCENARIO_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]+$")


class RepairExtensionScenarioError(ValueError):
    """Raised when a repair-extension scenario or evidence record is unsafe."""


@dataclass(frozen=True, slots=True)
class RepairExtensionScenarioDefinition:
    scenario_id: str
    expected_action: str
    expected_terminal: str


@dataclass(frozen=True, slots=True)
class RepairExtensionScenarioResult:
    scenario_id: str
    action: str
    terminal_state: str
    disabled_reason: str | None
    grant_count: int
    grant_content: dict[str, object] | None
    attempt_modes: tuple[str | None, ...]
    automatic_repair_attempts_used: int
    automatic_repair_attempts_max: int
    repair_history_triggers: tuple[str, ...]
    report_lineage: tuple[str, ...]
    raw_evidence: tuple[str, ...]
    automatic_loop_scheduled: bool
    downstream_artifacts_unchanged: bool
    request_change_separate: bool
    immutable_history: bool
    semantic_omissions: tuple[str, ...]
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RepairExtensionSuiteReport:
    schema_version: int
    suite_id: str
    scenarios: tuple[RepairExtensionScenarioResult, ...]

    @property
    def all_passed(self) -> bool:
        return bool(self.scenarios) and all(item.passed for item in self.scenarios)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "suite_id": self.suite_id,
            "all_passed": self.all_passed,
            "scenarios": [item.to_dict() for item in self.scenarios],
        }


def _required_string(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RepairExtensionScenarioError(f"{context} must be a non-empty string.")
    return value.strip()


def load_repair_extension_scenarios(
    root: Path = DEFAULT_REPAIR_EXTENSION_FIXTURE_ROOT,
) -> tuple[str, tuple[RepairExtensionScenarioDefinition, ...]]:
    manifest_path = root / "repair-extension-scenarios.json"
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RepairExtensionScenarioError(
            f"Unable to load repair-extension manifest: {manifest_path}"
        ) from error
    if (
        not isinstance(raw, dict)
        or raw.get("schema_version") != REPAIR_EXTENSION_SCENARIO_SCHEMA_VERSION
    ):
        raise RepairExtensionScenarioError(
            "Unsupported repair-extension scenario schema version."
        )
    source = raw.get("source")
    if not isinstance(source, dict) or source.get("credentials_removed") is not True:
        raise RepairExtensionScenarioError("Repair-extension scenarios must be provider-free.")
    suite_id = _required_string(raw.get("suite_id"), context="manifest.suite_id")
    raw_scenarios = raw.get("scenarios")
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        raise RepairExtensionScenarioError("manifest.scenarios must be a non-empty list.")
    definitions: list[RepairExtensionScenarioDefinition] = []
    for index, item in enumerate(raw_scenarios):
        if not isinstance(item, dict):
            raise RepairExtensionScenarioError(f"scenarios[{index}] must be an object.")
        scenario_id = _required_string(
            item.get("scenario_id"), context=f"scenarios[{index}].scenario_id"
        )
        if _SCENARIO_ID_PATTERN.fullmatch(scenario_id) is None:
            raise RepairExtensionScenarioError(f"scenarios[{index}].scenario_id is not stable.")
        definitions.append(
            RepairExtensionScenarioDefinition(
                scenario_id=scenario_id,
                expected_action=_required_string(
                    item.get("expected_action"), context=f"scenarios[{index}].expected_action"
                ),
                expected_terminal=_required_string(
                    item.get("expected_terminal"), context=f"scenarios[{index}].expected_terminal"
                ),
            )
        )
    ids = [item.scenario_id for item in definitions]
    if len(ids) != len(set(ids)):
        raise RepairExtensionScenarioError("Repair-extension scenario ids must be unique.")
    return suite_id, tuple(definitions)


def _finding() -> ValidatorReportFinding:
    return ValidatorReportFinding(
        code="SEM-PLACEHOLDER-CONTENT",
        severity="high",
        message="Replace the placeholder content.",
        source_path="workitems/WI-REPAIR-EXTENSION/stages/plan/plan.md",
    )


def _prepare_exhausted_workspace(root: Path) -> tuple[Path, RepairExtensionGrant, Path]:
    workspace_root = root / ".aidd"
    work_item = "WI-REPAIR-EXTENSION"
    run_id = "run-repair-extension"
    stage = "plan"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target=stage,
        config_snapshot={"configuration_identity": "fixture:repair-extension-v1"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=StageState.FAILED.value,
    )
    stage_root_path = stage_root(workspace_root, work_item, stage)
    stage_root_path.mkdir(parents=True, exist_ok=True)
    validator_report_path = stage_root_path / "validator-report.md"
    repair_brief_path = stage_root_path / "repair-brief.md"
    validator_report_path.write_text(
        render_validator_report(
            (
                ValidationFinding(
                    code="SEM-PLACEHOLDER-CONTENT",
                    message="Replace the placeholder content.",
                ),
            )
        ),
        encoding="utf-8",
    )
    repair_brief_path.write_text(
        "# Repair brief\n\nRepair budget status: `repair-budget-exhausted`.\n",
        encoding="utf-8",
    )
    for attempt_number, mode in enumerate(("initial", "repair", "repair"), start=1):
        write_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
            attempt_mode=mode,
        )
        persist_repair_history_snapshot(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=attempt_number,
            trigger=mode,
            outcome="failed validation",
            stage_status=StageState.FAILED.value,
            validator_report_path=validator_report_path,
            repair_brief_path=repair_brief_path,
        )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=StageState.FAILED.value,
    )
    grant = RepairExtensionGrant(
        work_item_id=work_item,
        run_id=run_id,
        stage=stage,
        validator_report_path=workspace_relative_path(workspace_root, validator_report_path),
        validator_report_sha256=hashlib.sha256(validator_report_path.read_bytes()).hexdigest(),
        repair_brief_path=workspace_relative_path(workspace_root, repair_brief_path),
        repair_brief_sha256=hashlib.sha256(repair_brief_path.read_bytes()).hexdigest(),
        configuration_identity="fixture:repair-extension-v1",
        author="provider-free-fixture",
        authorized_at_utc="2026-08-22T00:00:00Z",
        reason="One bounded correction after automatic exhaustion.",
    )
    downstream = root / "downstream-qa.md"
    downstream.write_text("fresh downstream artifact\n", encoding="utf-8")
    return workspace_root, grant, downstream


def _reopen(
    workspace_root: Path,
    grant: RepairExtensionGrant,
    *,
    findings: tuple[ValidatorReportFinding, ...] = (_finding(),),
    succeeded_downstream: tuple[str, ...] = (),
) -> RepairExtensionPreflightResult:
    return preflight_repair_extension(
        workspace_root=workspace_root,
        grant=grant,
        current_configuration_identity="fixture:repair-extension-v1",
        latest_stage_status="repair-exhausted",
        latest_attempt_mode="repair",
        revalidation_findings=findings,
        succeeded_downstream=succeeded_downstream,
        prior_stage_artifacts=("workitems/WI-REPAIR-EXTENSION/context/request.md",),
    )


def _record_extension_attempt(
    workspace_root: Path,
    grant: RepairExtensionGrant,
    *,
    status: str,
    outcome: str,
) -> None:
    attempt_number = 4
    write_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=grant.work_item_id,
        run_id=grant.run_id,
        stage=grant.stage,
        attempt_number=attempt_number,
        attempt_mode="repair-extension",
    )
    stage_root_path = stage_root(workspace_root, grant.work_item_id, grant.stage)
    if status == StageState.SUCCEEDED.value:
        report_path = stage_root_path / "repair-extension-validator-report.md"
        report_path.write_text(render_validator_report(()), encoding="utf-8")
    else:
        report_path = stage_root_path / "validator-report.md"
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item=grant.work_item_id,
        run_id=grant.run_id,
        stage=grant.stage,
        attempt_number=attempt_number,
        trigger="repair-extension",
        outcome=outcome,
        stage_status=status,
        validator_report_path=report_path,
        repair_brief_path=stage_root_path / "repair-extension-brief.md",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=grant.work_item_id,
        run_id=grant.run_id,
        stage=grant.stage,
        status=status,
    )


def _attempt_modes(workspace_root: Path, grant: RepairExtensionGrant) -> tuple[str | None, ...]:
    modes: list[str | None] = []
    for attempt_number in range(1, 5):
        index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=grant.work_item_id,
            run_id=grant.run_id,
            stage=grant.stage,
            attempt_number=attempt_number,
        )
        modes.append(None if index is None else index.attempt_mode)
    return tuple(modes)


def _report_lineage(workspace_root: Path, grant: RepairExtensionGrant) -> tuple[str, ...]:
    stage_root_path = stage_root(workspace_root, grant.work_item_id, grant.stage)
    candidates = (
        "validator-report.md",
        "repair-brief.md",
        "repair-extension-brief.md",
        "repair-extension-validator-report.md",
        "stage-result.md",
    )
    return tuple(
        workspace_relative_path(workspace_root, stage_root_path / name)
        for name in candidates
        if (stage_root_path / name).is_file()
    )


def _raw_evidence(workspace_root: Path, grant: RepairExtensionGrant) -> tuple[str, ...]:
    stage_root_path = stage_root(workspace_root, grant.work_item_id, grant.stage)
    evidence = [
        workspace_relative_path(workspace_root, stage_root_path / "stage-result.md"),
        workspace_relative_path(workspace_root, stage_root_path / "validator-report.md"),
    ]
    for attempt_number in range(1, 5):
        index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=grant.work_item_id,
            run_id=grant.run_id,
            stage=grant.stage,
            attempt_number=attempt_number,
        )
        if index is not None:
            evidence.append(
                workspace_relative_path(
                    workspace_root,
                    stage_root_path
                    / "attempts"
                    / f"attempt-{attempt_number:04d}"
                    / "artifact-index.json",
                )
            )
    return tuple(evidence)


def _request_change_action_is_separate() -> bool:
    source_path = Path(__file__).resolve().parents[2] / "aidd/cli/static/operator-stage-cockpit.js"
    try:
        source = source_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return (
        'data-recovery-action="repair-extension"' in source
        and 'data-recovery-action="request-change"' in source
        and "Run one more repair" in source
        and "Request Change" in source
    )


def _run_one(
    definition: RepairExtensionScenarioDefinition,
) -> RepairExtensionScenarioResult:
    with tempfile.TemporaryDirectory(prefix="aidd-repair-extension-") as directory:
        workspace_root, grant, downstream = _prepare_exhausted_workspace(Path(directory))
        scenario_id = definition.scenario_id
        action = "blocked"
        disabled_reason: str | None = None
        immutable_history = True
        request_change_separate = (
            _request_change_action_is_separate()
            if scenario_id == "request-change-separation"
            else False
        )
        baseline_attempt = (
            workspace_root
            / "reports/runs/WI-REPAIR-EXTENSION/run-repair-extension/stages/plan/attempts"
            / "attempt-0001/artifact-index.json"
        ).read_bytes()
        if scenario_id == "extension-success":
            preflight = _reopen(workspace_root, grant)
            action = preflight.action
            _record_extension_attempt(
                workspace_root,
                grant,
                status=StageState.SUCCEEDED.value,
                outcome="succeeded after one explicitly authorized extension",
            )
        elif scenario_id == "extension-repeated-failure":
            preflight = _reopen(workspace_root, grant)
            action = preflight.action
            _record_extension_attempt(
                workspace_root,
                grant,
                status=StageState.FAILED.value,
                outcome="failed validation after one explicitly authorized extension",
            )
        elif scenario_id == "manual-fix-prevalidation":
            preflight = _reopen(workspace_root, grant, findings=())
            action = preflight.action
        elif scenario_id == "stale-evidence":
            stage_root_path = stage_root(workspace_root, grant.work_item_id, grant.stage)
            (stage_root_path / "validator-report.md").write_text(
                (stage_root_path / "validator-report.md").read_text(encoding="utf-8")
                + "\nchanged after grant\n",
                encoding="utf-8",
            )
            preflight = _reopen(workspace_root, grant)
            action = preflight.action
            disabled_reason = preflight.eligibility.disabled_reason
        elif scenario_id == "downstream-success":
            preflight = _reopen(workspace_root, grant, succeeded_downstream=("qa",))
            action = preflight.action
            disabled_reason = preflight.eligibility.disabled_reason
        elif scenario_id in {"second-grant", "request-change-separation"}:
            first = _reopen(workspace_root, grant)
            if first.action != "reopened":
                raise RepairExtensionScenarioError(
                    "Initial extension grant did not reopen the stage."
                )
            second = _reopen(workspace_root, grant, findings=())
            action = second.action
            disabled_reason = second.eligibility.disabled_reason
        elif scenario_id == "immutable-history":
            preflight = _reopen(workspace_root, grant)
            action = preflight.action
            _record_extension_attempt(
                workspace_root,
                grant,
                status=StageState.FAILED.value,
                outcome="failed validation after one explicitly authorized extension",
            )
        else:
            raise RepairExtensionScenarioError(f"No runner for {scenario_id!r}.")

        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=grant.work_item_id,
            run_id=grant.run_id,
            stage=grant.stage,
        )
        if metadata is None:
            raise RepairExtensionScenarioError("Scenario lost stage metadata.")
        counter = evaluate_stage_repair_counter(
            workspace_root=workspace_root,
            work_item=grant.work_item_id,
            run_id=grant.run_id,
            stage=grant.stage,
        )
        modes = _attempt_modes(workspace_root, grant)
        if scenario_id in {"extension-success", "extension-repeated-failure", "immutable-history"}:
            immutable_history = (
                baseline_attempt
                == (
                    workspace_root
                    / "reports/runs/WI-REPAIR-EXTENSION/run-repair-extension/stages/plan/attempts"
                    / "attempt-0001/artifact-index.json"
                ).read_bytes()
            )
        downstream_unchanged = (
            downstream.read_text(encoding="utf-8") == "fresh downstream artifact\n"
        )
        grant_content = (
            metadata.repair_extension_grant.to_dict()
            if metadata.repair_extension_grant
            else None
        )
        grant_count = int(metadata.repair_extension_grant is not None)
        report_lineage = _report_lineage(workspace_root, grant)
        raw_evidence = _raw_evidence(workspace_root, grant)
        automatic_loop_scheduled = len(modes) > 4
        triggers = tuple(entry.trigger for entry in metadata.repair_history)
        result = RepairExtensionScenarioResult(
            scenario_id=scenario_id,
            action=action,
            terminal_state=metadata.status,
            disabled_reason=disabled_reason,
            grant_count=grant_count,
            grant_content=grant_content,
            attempt_modes=modes,
            automatic_repair_attempts_used=counter.repair_attempts_used,
            automatic_repair_attempts_max=counter.max_repair_attempts,
            repair_history_triggers=triggers,
            report_lineage=report_lineage,
            raw_evidence=raw_evidence,
            automatic_loop_scheduled=automatic_loop_scheduled,
            downstream_artifacts_unchanged=downstream_unchanged,
            request_change_separate=request_change_separate,
            immutable_history=immutable_history,
            semantic_omissions=(),
            passed=False,
        )
        omissions: list[str] = []
        if action != definition.expected_action:
            omissions.append("action")
        if metadata.status != definition.expected_terminal:
            omissions.append("terminal_state")
        if not report_lineage:
            omissions.append("report_lineage")
        if not raw_evidence:
            omissions.append("raw_evidence")
        if grant_count > 1:
            omissions.append("grant_count")
        if counter.repair_attempts_used != 2 or counter.max_repair_attempts != 2:
            omissions.append("automatic_budget")
        if automatic_loop_scheduled:
            omissions.append("automatic_loop")
        if not downstream_unchanged:
            omissions.append("downstream_artifacts")
        if scenario_id == "request-change-separation" and not request_change_separate:
            omissions.append("request_change_separation")
        if scenario_id == "immutable-history" and not immutable_history:
            omissions.append("immutable_history")
        if scenario_id == "second-grant" and grant_count != 1:
            omissions.append("second_grant")
        if action == "blocked" and not (disabled_reason or "").strip():
            omissions.append("disabled_reason")
        return RepairExtensionScenarioResult(
            scenario_id=result.scenario_id,
            action=result.action,
            terminal_state=result.terminal_state,
            disabled_reason=result.disabled_reason,
            grant_count=result.grant_count,
            grant_content=result.grant_content,
            attempt_modes=result.attempt_modes,
            automatic_repair_attempts_used=result.automatic_repair_attempts_used,
            automatic_repair_attempts_max=result.automatic_repair_attempts_max,
            repair_history_triggers=result.repair_history_triggers,
            report_lineage=result.report_lineage,
            raw_evidence=result.raw_evidence,
            automatic_loop_scheduled=result.automatic_loop_scheduled,
            downstream_artifacts_unchanged=result.downstream_artifacts_unchanged,
            request_change_separate=result.request_change_separate,
            immutable_history=result.immutable_history,
            semantic_omissions=tuple(dict.fromkeys(omissions)),
            passed=not omissions,
        )


def run_repair_extension_scenarios(
    *, root: Path = DEFAULT_REPAIR_EXTENSION_FIXTURE_ROOT
) -> RepairExtensionSuiteReport:
    suite_id, definitions = load_repair_extension_scenarios(root)
    return RepairExtensionSuiteReport(
        schema_version=REPAIR_EXTENSION_SCENARIO_SCHEMA_VERSION,
        suite_id=suite_id,
        scenarios=tuple(_run_one(definition) for definition in definitions),
    )


def write_repair_extension_report(report: RepairExtensionSuiteReport, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_repair_extension_scenarios()
    if args.output is not None:
        write_repair_extension_report(report, args.output)
    return 0 if report.all_passed else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())


__all__ = [
    "DEFAULT_REPAIR_EXTENSION_FIXTURE_ROOT",
    "REPAIR_EXTENSION_SCENARIO_SCHEMA_VERSION",
    "RepairExtensionScenarioDefinition",
    "RepairExtensionScenarioError",
    "RepairExtensionScenarioResult",
    "RepairExtensionSuiteReport",
    "load_repair_extension_scenarios",
    "run_repair_extension_scenarios",
    "write_repair_extension_report",
]

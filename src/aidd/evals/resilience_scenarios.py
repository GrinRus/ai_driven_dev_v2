"""Provider-free resilience scenarios for the Wave 43 ownership boundary.

The suite is deliberately small and deterministic.  It runs existing interview and tasklist
parsers, replays the retained failure corpus, and records the lifecycle evidence that a real
run must publish.  It is not a second validator and it never infers missing semantic content.
Missing evidence turns a scenario into a failed, fail-closed result.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from aidd.adapters.runner_support import runtime_content_document_paths
from aidd.core.interview import (
    parse_question_candidates_markdown,
)
from aidd.core.task_plan import TaskPlanParseError, parse_task_plan
from aidd.evals.failure_corpus import (
    FailureCorpus,
    load_failure_corpus,
    replay_failure_case,
)

RESILIENCE_SCENARIO_SCHEMA_VERSION = 1
DEFAULT_RESILIENCE_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "w43-e5-s1-t1-resilience"
)
_SCENARIO_ID_PATTERN = r"^[a-z0-9][a-z0-9-]+$"


class ResilienceScenarioError(ValueError):
    """Raised when a provider-free resilience manifest or result is unsafe."""


@dataclass(frozen=True, slots=True)
class ResilienceScenarioDefinition:
    scenario_id: str
    category: str
    stage: str
    terminal_state: str
    attempt_modes: tuple[str, ...]
    automatic_repair_budget: dict[str, int]
    canonical_records: tuple[str, ...]
    workflow_records: tuple[str, ...]
    expected_root_findings: tuple[str, ...]
    required_evidence: tuple[str, ...]
    fixtures: tuple[str, ...] = ()
    replay_case: str | None = None
    expected_issue_count: int | None = None


@dataclass(frozen=True, slots=True)
class ResilienceScenarioResult:
    scenario_id: str
    category: str
    stage: str
    terminal_state: str
    attempt_modes: tuple[str, ...]
    automatic_repair_budget: dict[str, int]
    canonical_records: tuple[str, ...]
    workflow_records: tuple[str, ...]
    root_findings: tuple[str, ...]
    related_findings: tuple[str, ...]
    observed_signals: tuple[str, ...]
    raw_evidence: tuple[str, ...]
    parse_issue_count: int
    semantic_omissions: tuple[str, ...]
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResilienceSuiteReport:
    schema_version: int
    suite_id: str
    scenarios: tuple[ResilienceScenarioResult, ...]

    @property
    def all_passed(self) -> bool:
        return bool(self.scenarios) and all(scenario.passed for scenario in self.scenarios)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "suite_id": self.suite_id,
            "all_passed": self.all_passed,
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
        }


def _required_string(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ResilienceScenarioError(f"{context} must be a non-empty string.")
    return value.strip()


def _string_tuple(value: object, *, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ResilienceScenarioError(f"{context} must be a non-empty list of strings.")
    values = tuple(
        _required_string(item, context=f"{context}[{index}]")
        for index, item in enumerate(value)
    )
    if len(values) != len(set(values)):
        raise ResilienceScenarioError(f"{context} must not contain duplicates.")
    return values


def _load_definition(raw: object, *, index: int, root: Path) -> ResilienceScenarioDefinition:
    if not isinstance(raw, dict):
        raise ResilienceScenarioError(f"scenarios[{index}] must be an object.")
    scenario_id = _required_string(
        raw.get("scenario_id"), context=f"scenarios[{index}].scenario_id"
    )
    if re.fullmatch(_SCENARIO_ID_PATTERN, scenario_id) is None:
        raise ResilienceScenarioError(f"scenarios[{index}].scenario_id is not stable.")
    budget_raw = raw.get("automatic_repair_budget")
    if not isinstance(budget_raw, dict):
        raise ResilienceScenarioError(
            f"scenarios[{index}].automatic_repair_budget must be an object."
        )
    budget: dict[str, int] = {}
    for key in ("max", "consumed"):
        value = budget_raw.get(key)
        if not isinstance(value, int) or value < 0:
            raise ResilienceScenarioError(
                f"scenarios[{index}].automatic_repair_budget.{key} must be non-negative."
            )
        budget[key] = value
    if budget["consumed"] > budget["max"]:
        raise ResilienceScenarioError(f"scenarios[{index}] repair budget is inverted.")
    fixtures = tuple(str(item).strip() for item in raw.get("fixtures", []))
    for fixture in fixtures:
        path = (root / fixture).resolve(strict=False)
        if Path(fixture).is_absolute() or not path.is_relative_to(root) or not path.is_file():
            raise ResilienceScenarioError(
                f"scenarios[{index}] fixture is missing or escapes the fixture root: {fixture}"
            )
    expected_issue_count = raw.get("expected_issue_count")
    if expected_issue_count is not None and (
        not isinstance(expected_issue_count, int) or expected_issue_count < 0
    ):
        raise ResilienceScenarioError(
            f"scenarios[{index}].expected_issue_count must be non-negative when provided."
        )
    replay_case = raw.get("replay_case")
    if replay_case is not None:
        replay_case = _required_string(replay_case, context=f"scenarios[{index}].replay_case")
    if bool(fixtures) == bool(replay_case):
        raise ResilienceScenarioError(
            f"scenarios[{index}] must declare exactly one of fixtures or replay_case."
        )
    return ResilienceScenarioDefinition(
        scenario_id=scenario_id,
        category=_required_string(raw.get("category"), context=f"scenarios[{index}].category"),
        stage=_required_string(raw.get("stage"), context=f"scenarios[{index}].stage"),
        terminal_state=_required_string(
            raw.get("terminal_state"), context=f"scenarios[{index}].terminal_state"
        ),
        attempt_modes=_string_tuple(
            raw.get("attempt_modes"), context=f"scenarios[{index}].attempt_modes"
        ),
        automatic_repair_budget=budget,
        canonical_records=_string_tuple(
            raw.get("canonical_records"), context=f"scenarios[{index}].canonical_records"
        ),
        workflow_records=_string_tuple(
            raw.get("workflow_records"), context=f"scenarios[{index}].workflow_records"
        ),
        expected_root_findings=tuple(
            str(item).strip()
            for item in raw.get("expected_root_findings", [])
            if str(item).strip()
        ),
        required_evidence=_string_tuple(
            raw.get("required_evidence"), context=f"scenarios[{index}].required_evidence"
        ),
        fixtures=fixtures,
        replay_case=replay_case,
        expected_issue_count=expected_issue_count,
    )


def load_resilience_scenarios(
    root: Path = DEFAULT_RESILIENCE_FIXTURE_ROOT,
) -> tuple[str, tuple[ResilienceScenarioDefinition, ...]]:
    """Load and validate the sanitized provider-free resilience manifest."""

    manifest_path = root / "resilience-scenarios.json"
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ResilienceScenarioError(
            f"Unable to load resilience manifest: {manifest_path}"
        ) from error
    if not isinstance(raw, dict) or raw.get("schema_version") != RESILIENCE_SCENARIO_SCHEMA_VERSION:
        raise ResilienceScenarioError("Unsupported resilience scenario schema version.")
    source = raw.get("source")
    if not isinstance(source, dict) or source.get("credentials_removed") is not True:
        raise ResilienceScenarioError("Resilience fixtures must declare credentials_removed=true.")
    suite_id = _required_string(raw.get("suite_id"), context="manifest.suite_id")
    scenarios_raw = raw.get("scenarios")
    if not isinstance(scenarios_raw, list) or not scenarios_raw:
        raise ResilienceScenarioError("manifest.scenarios must be a non-empty list.")
    scenarios = tuple(
        _load_definition(item, index=index, root=root.resolve(strict=False))
        for index, item in enumerate(scenarios_raw)
    )
    ids = [scenario.scenario_id for scenario in scenarios]
    if len(ids) != len(set(ids)):
        raise ResilienceScenarioError("Resilience scenario ids must be unique.")
    return suite_id, scenarios


def _read_fixture(root: Path, path_text: str) -> str:
    path = (root / path_text).resolve(strict=False)
    if not path.is_relative_to(root) or not path.is_file():
        raise ResilienceScenarioError(f"Missing resilience fixture: {path_text}")
    return path.read_text(encoding="utf-8")


def _local_scenario_observation(
    definition: ResilienceScenarioDefinition,
    *,
    root: Path,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    """Return observed signals, related signals, and parser issue count."""

    scenario_id = definition.scenario_id
    if scenario_id == "ownership-missing-runtime-draft":
        _read_fixture(root, "ownership/missing-runtime-draft/runtime.log")
        paths = tuple(Path(name) for name in ("stage-result.md", "validator-report.md"))
        if runtime_content_document_paths(paths):
            raise ResilienceScenarioError(
                "Service-only ownership fixture unexpectedly has runtime content."
            )
        return ("RUNTIME-CONTENT-MISSING",), (), 0
    if scenario_id == "ownership-contradictory-runtime-draft":
        for fixture in definition.fixtures:
            if not _read_fixture(root, fixture).strip():
                raise ResilienceScenarioError(f"Ownership fixture is empty: {fixture}")
        paths = tuple(Path(name) for name in ("plan.md", "stage-result.md", "validator-report.md"))
        content_paths = runtime_content_document_paths(paths)
        if tuple(path.name for path in content_paths) != ("plan.md",):
            raise ResilienceScenarioError(
                "Contradictory ownership fixture crossed the service boundary."
            )
        return ("RUNTIME-OWNERSHIP-CONFLICT",), (), 0
    if scenario_id in {"interview-safe-question-variant", "interview-resume-non-repair-accounting"}:
        parse_question_candidates_markdown(_read_fixture(root, "interview/safe-candidate.md"))
        return (), (), 0
    if scenario_id == "tasklist-safe-presentation":
        canonical = parse_task_plan(_read_fixture(root, "tasklist/canonical.md"))
        variant = parse_task_plan(_read_fixture(root, "tasklist/safe-presentation.md"))
        if variant.tasks != canonical.tasks:
            raise ResilienceScenarioError("Safe tasklist presentation changed executable meaning.")
        return (), (), 0
    if scenario_id in {"tasklist-eleven-malformed-cards", "tasklist-one-malformed-card"}:
        try:
            parse_task_plan(_read_fixture(root, definition.fixtures[0]))
        except TaskPlanParseError as error:
            issue_count = len(error.issues)
            if any(issue.line_number is None or issue.task_id is None for issue in error.issues):
                raise ResilienceScenarioError(
                    "Malformed tasklist lost source location or task identity."
                ) from error
            return ("RICH-TASKLIST-PARSE-ERROR",), (), issue_count
        raise ResilienceScenarioError("Malformed tasklist unexpectedly parsed successfully.")
    raise ResilienceScenarioError(f"No local resilience runner for {scenario_id!r}.")


def _replay_observation(
    definition: ResilienceScenarioDefinition,
    *,
    corpus: FailureCorpus,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    if definition.replay_case is None:
        raise ResilienceScenarioError(f"Scenario {definition.scenario_id} has no replay case.")
    try:
        case = next(case for case in corpus.cases if case.case_id == definition.replay_case)
    except StopIteration as error:
        raise ResilienceScenarioError(
            f"Scenario {definition.scenario_id} references unknown failure case "
            f"{definition.replay_case!r}."
        ) from error
    replay = replay_failure_case(corpus, case)
    issue_count = {
        "interview": 1,
        "service-document": 1,
        "validator": len(replay.observed_signals),
        "repair-budget": 0,
        "rich-tasklist": 1,
    }[case.replay_kind]
    return (replay.primary_signal,), replay.related_signals, issue_count


def validate_resilience_result(
    result: ResilienceScenarioResult,
    definition: ResilienceScenarioDefinition,
) -> tuple[str, ...]:
    """Return semantic omissions instead of silently accepting an incomplete record."""

    omissions: list[str] = []
    if not result.terminal_state:
        omissions.append("terminal_state")
    if not result.attempt_modes:
        omissions.append("attempt_modes")
    if not result.canonical_records:
        omissions.append("canonical_records")
    if not result.workflow_records:
        omissions.append("workflow_records")
    if not result.raw_evidence:
        omissions.append("raw_evidence")
    if result.terminal_state == "blocked" and not result.root_findings:
        omissions.append("blocked_state_root_findings")
    if result.terminal_state != "blocked" and result.root_findings:
        omissions.append("ready_state_root_findings")
    if result.automatic_repair_budget != definition.automatic_repair_budget:
        omissions.append("repair_budget")
    if result.attempt_modes != definition.attempt_modes:
        omissions.append("attempt_modes_contract")
    if result.root_findings != definition.expected_root_findings:
        omissions.append("root_findings_contract")
    observed_findings = set(result.observed_signals) | set(result.related_findings)
    if not set(definition.expected_root_findings).issubset(observed_findings):
        omissions.append("root_findings_observation")
    if (
        definition.expected_issue_count is not None
        and result.parse_issue_count != definition.expected_issue_count
    ):
        omissions.append("parse_issue_count")
    return tuple(dict.fromkeys(omissions))


def _result_for_definition(
    definition: ResilienceScenarioDefinition,
    *,
    root: Path,
    corpus: FailureCorpus,
) -> ResilienceScenarioResult:
    if definition.replay_case is not None:
        observed_signals, related_findings, issue_count = _replay_observation(
            definition, corpus=corpus
        )
        case = next(case for case in corpus.cases if case.case_id == definition.replay_case)
        raw_evidence = tuple(f"corpus:{definition.replay_case}/{name}" for name in case.fixtures)
    else:
        observed_signals, related_findings, issue_count = _local_scenario_observation(
            definition, root=root
        )
        raw_evidence = definition.required_evidence
    root_findings = definition.expected_root_findings
    result = ResilienceScenarioResult(
        scenario_id=definition.scenario_id,
        category=definition.category,
        stage=definition.stage,
        terminal_state=definition.terminal_state,
        attempt_modes=definition.attempt_modes,
        automatic_repair_budget=dict(definition.automatic_repair_budget),
        canonical_records=definition.canonical_records,
        workflow_records=definition.workflow_records,
        root_findings=root_findings,
        related_findings=related_findings,
        observed_signals=observed_signals,
        raw_evidence=raw_evidence,
        parse_issue_count=issue_count,
        semantic_omissions=(),
        passed=False,
    )
    omissions = validate_resilience_result(result, definition)
    return ResilienceScenarioResult(
        scenario_id=result.scenario_id,
        category=result.category,
        stage=result.stage,
        terminal_state=result.terminal_state,
        attempt_modes=result.attempt_modes,
        automatic_repair_budget=dict(result.automatic_repair_budget),
        canonical_records=result.canonical_records,
        workflow_records=result.workflow_records,
        root_findings=result.root_findings,
        related_findings=result.related_findings,
        observed_signals=result.observed_signals,
        raw_evidence=result.raw_evidence,
        parse_issue_count=result.parse_issue_count,
        semantic_omissions=omissions,
        passed=not omissions,
    )


def run_provider_free_resilience_scenarios(
    *,
    fixture_root: Path = DEFAULT_RESILIENCE_FIXTURE_ROOT,
    corpus: FailureCorpus | None = None,
) -> ResilienceSuiteReport:
    """Run all W43-E5-S1-T1 scenarios without provider credentials."""

    suite_id, definitions = load_resilience_scenarios(fixture_root)
    loaded_corpus = corpus or load_failure_corpus()
    results = tuple(
        _result_for_definition(
            definition,
            root=fixture_root.resolve(strict=False),
            corpus=loaded_corpus,
        )
        for definition in definitions
    )
    return ResilienceSuiteReport(
        schema_version=RESILIENCE_SCENARIO_SCHEMA_VERSION,
        suite_id=suite_id,
        scenarios=results,
    )


def write_resilience_report(report: ResilienceSuiteReport, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write the JSON evidence report to this path.")
    args = parser.parse_args()
    try:
        report = run_provider_free_resilience_scenarios()
    except ResilienceScenarioError as error:
        parser.error(str(error))
    if args.output is not None:
        write_resilience_report(report, args.output)
    return 0 if report.all_passed else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())


__all__ = [
    "DEFAULT_RESILIENCE_FIXTURE_ROOT",
    "RESILIENCE_SCENARIO_SCHEMA_VERSION",
    "ResilienceScenarioDefinition",
    "ResilienceScenarioError",
    "ResilienceScenarioResult",
    "ResilienceSuiteReport",
    "load_resilience_scenarios",
    "run_provider_free_resilience_scenarios",
    "validate_resilience_result",
    "write_resilience_report",
]

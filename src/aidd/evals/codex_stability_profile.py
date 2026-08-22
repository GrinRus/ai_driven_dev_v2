"""Codex-only stability profile and repetition evidence contract.

This module defines the durable comparison shape for the Wave 43 Codex lane.  It does not
launch a provider and it does not grade model quality.  T2 uses the profile to validate every
fresh repetition against the same pinned scenario, runtime configuration, metric vocabulary,
and evidence inventory.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from aidd.harness.scenarios import Scenario, load_scenario

CODEX_STABILITY_PROFILE_SCHEMA_VERSION = 1
DEFAULT_CODEX_STABILITY_PROFILE_ROOT = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "w43-e5-s2-t1-codex-stability"
)
DEFAULT_CODEX_STABILITY_PROFILE_PATH = (
    DEFAULT_CODEX_STABILITY_PROFILE_ROOT / "codex-stability-profile.json"
)
DEFAULT_CODEX_STABILITY_SCENARIO_PATH = (
    Path(__file__).resolve().parents[3]
    / "harness"
    / "scenarios"
    / "live"
    / "hono-non-error-throw-handling.yaml"
)

CodexMetricKind = Literal["rate", "ratio"]
CodexMetricDirection = Literal["higher-is-better", "lower-is-better"]
CodexRepetitionStatus = Literal["pass", "fail", "blocked", "infra-fail"]

CODEX_STABILITY_METRIC_IDS: tuple[str, ...] = (
    "initial-pass-rate",
    "first-repair-recovery",
    "exhaustion",
    "findings-per-root-cause",
    "false-budget-consumption",
    "interview-resume",
    "tasklist-compliance",
    "extension-success",
    "intervention-rate",
)

CODEX_STABILITY_REQUIRED_ARTIFACTS: tuple[str, ...] = (
    "harness-metadata.json",
    "install-transcript.json",
    "feature-selection.json",
    "flow-state.json",
    "stage-audits/<stage-run-id>.json",
    "runtime.log",
    "stage-timing.json",
    "log-analysis.md",
    "repair-history.md",
    "task-flow-checkpoint.json",
    "task-flow-checkpoint.md",
    "target-workspace-evidence.json",
    "verify-transcript.json",
    "grader.json",
    "verdict.md",
)

CODEX_STABILITY_CONDITIONAL_ARTIFACTS: tuple[str, ...] = (
    "runtime.jsonl",
    "events.jsonl",
    "questions.md",
    "answers.md",
    "frontend-checkpoints.json",
    "frontend-checkpoints.md",
)

CODEX_STABILITY_REQUIRED_EVIDENCE_FIELDS: tuple[str, ...] = (
    "scenario_id",
    "run_id",
    "runtime_id",
    "target_revision",
    "config_identity",
    "stage_scope",
    "attempts",
    "evidence_links",
    "first_failure_boundary",
    "metrics",
)

_STABLE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]+$")
_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_STATUSES = {"pass", "fail", "blocked", "infra-fail"}


class CodexStabilityProfileError(ValueError):
    """Raised when a stability profile or repetition evidence is unsafe."""


@dataclass(frozen=True, slots=True)
class CodexMetricDefinition:
    metric_id: str
    kind: CodexMetricKind
    direction: CodexMetricDirection
    description: str
    numerator: str
    denominator: str
    source_artifacts: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CodexEvidenceSchema:
    required_artifacts: tuple[str, ...]
    conditional_artifacts: tuple[str, ...]
    required_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CodexStabilityProfile:
    schema_version: int
    profile_id: str
    scenario_id: str
    scenario_path: str
    runtime_id: str
    representative_task_id: str
    work_item: str
    target_repository: str
    target_revision: str
    stage_start: str
    stage_end: str
    execution_mode: str
    command_source: str
    model: str
    reasoning_effort: str
    config_identity: str
    prompt_pack_root: str
    minimum_repetitions: int
    metrics: tuple[CodexMetricDefinition, ...]
    evidence_schema: CodexEvidenceSchema

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "profile_id": self.profile_id,
            "scenario": {
                "id": self.scenario_id,
                "path": self.scenario_path,
                "runtime_id": self.runtime_id,
                "representative_task_id": self.representative_task_id,
                "work_item": self.work_item,
                "target_repository": self.target_repository,
                "target_revision": self.target_revision,
                "stage_start": self.stage_start,
                "stage_end": self.stage_end,
            },
            "runtime_config": {
                "execution_mode": self.execution_mode,
                "command_source": self.command_source,
                "model": self.model,
                "reasoning_effort": self.reasoning_effort,
                "config_identity": self.config_identity,
                "prompt_pack_root": self.prompt_pack_root,
            },
            "repetitions": {"minimum": self.minimum_repetitions},
            "metrics": [metric.to_dict() for metric in self.metrics],
            "evidence_schema": self.evidence_schema.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class CodexRepetitionEvidence:
    schema_version: int
    repetition_id: str
    scenario_id: str
    run_id: str
    runtime_id: str
    target_revision: str
    config_identity: str
    status: CodexRepetitionStatus
    stage_scope: tuple[str, str]
    attempts: tuple[dict[str, object], ...]
    evidence_links: tuple[str, ...]
    first_failure_boundary: dict[str, str]
    metrics: dict[str, dict[str, float]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _required_string(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CodexStabilityProfileError(f"{context} must be a non-empty string.")
    return value.strip()


def _string_tuple(value: object, *, context: str, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CodexStabilityProfileError(f"{context} must be a list of strings.")
    if not allow_empty and not value:
        raise CodexStabilityProfileError(f"{context} must be non-empty.")
    normalized = tuple(
        _required_string(item, context=f"{context}[{index}]")
        for index, item in enumerate(value)
    )
    if len(normalized) != len(set(normalized)):
        raise CodexStabilityProfileError(f"{context} must not contain duplicates.")
    return normalized


def _stable_id(value: object, *, context: str) -> str:
    normalized = _required_string(value, context=context)
    if _STABLE_ID_PATTERN.fullmatch(normalized) is None:
        raise CodexStabilityProfileError(f"{context} must be a stable lowercase id.")
    return normalized


def _revision(value: object, *, context: str) -> str:
    normalized = _required_string(value, context=context).lower()
    if _REVISION_PATTERN.fullmatch(normalized) is None:
        raise CodexStabilityProfileError(f"{context} must be a 40-character lowercase SHA.")
    return normalized


def _metric_definition(raw: object, *, index: int) -> CodexMetricDefinition:
    context = f"metrics[{index}]"
    if not isinstance(raw, dict):
        raise CodexStabilityProfileError(f"{context} must be an object.")
    metric_id = _stable_id(raw.get("metric_id"), context=f"{context}.metric_id")
    kind = _required_string(raw.get("kind"), context=f"{context}.kind")
    direction = _required_string(raw.get("direction"), context=f"{context}.direction")
    if kind not in {"rate", "ratio"}:
        raise CodexStabilityProfileError(f"{context}.kind is unsupported: {kind!r}.")
    if direction not in {"higher-is-better", "lower-is-better"}:
        raise CodexStabilityProfileError(f"{context}.direction is unsupported: {direction!r}.")
    return CodexMetricDefinition(
        metric_id=metric_id,
        kind=kind,  # type: ignore[arg-type]
        direction=direction,  # type: ignore[arg-type]
        description=_required_string(raw.get("description"), context=f"{context}.description"),
        numerator=_required_string(raw.get("numerator"), context=f"{context}.numerator"),
        denominator=_required_string(raw.get("denominator"), context=f"{context}.denominator"),
        source_artifacts=_string_tuple(
            raw.get("source_artifacts"), context=f"{context}.source_artifacts"
        ),
    )


def _evidence_schema(raw: object) -> CodexEvidenceSchema:
    if not isinstance(raw, dict):
        raise CodexStabilityProfileError("evidence_schema must be an object.")
    required_artifacts = _string_tuple(
        raw.get("required_artifacts"), context="evidence_schema.required_artifacts"
    )
    conditional_artifacts = _string_tuple(
        raw.get("conditional_artifacts"),
        context="evidence_schema.conditional_artifacts",
        allow_empty=True,
    )
    required_fields = _string_tuple(
        raw.get("required_fields"), context="evidence_schema.required_fields"
    )
    if not set(CODEX_STABILITY_REQUIRED_ARTIFACTS).issubset(required_artifacts):
        raise CodexStabilityProfileError(
            "evidence_schema.required_artifacts must include the canonical Codex inventory."
        )
    if not set(CODEX_STABILITY_REQUIRED_EVIDENCE_FIELDS).issubset(required_fields):
        raise CodexStabilityProfileError(
            "evidence_schema.required_fields must include the canonical repetition fields."
        )
    overlap = set(required_artifacts) & set(conditional_artifacts)
    if overlap:
        raise CodexStabilityProfileError(
            "evidence_schema cannot classify an artifact as both required and conditional: "
            + ", ".join(sorted(overlap))
        )
    return CodexEvidenceSchema(
        required_artifacts=required_artifacts,
        conditional_artifacts=conditional_artifacts,
        required_fields=required_fields,
    )


def _parse_profile(raw: object) -> CodexStabilityProfile:
    if not isinstance(raw, dict):
        raise CodexStabilityProfileError("Codex stability profile must be an object.")
    if raw.get("schema_version") != CODEX_STABILITY_PROFILE_SCHEMA_VERSION:
        raise CodexStabilityProfileError(
            "Unsupported Codex stability profile schema version: "
            f"{raw.get('schema_version')!r}."
        )
    scenario = raw.get("scenario")
    runtime_config = raw.get("runtime_config")
    repetitions = raw.get("repetitions")
    if not isinstance(scenario, dict):
        raise CodexStabilityProfileError("scenario must be an object.")
    if not isinstance(runtime_config, dict):
        raise CodexStabilityProfileError("runtime_config must be an object.")
    if not isinstance(repetitions, dict):
        raise CodexStabilityProfileError("repetitions must be an object.")
    minimum_repetitions = repetitions.get("minimum")
    if not isinstance(minimum_repetitions, int) or minimum_repetitions < 3:
        raise CodexStabilityProfileError("repetitions.minimum must be at least 3.")
    metrics_raw = raw.get("metrics")
    if not isinstance(metrics_raw, list) or not metrics_raw:
        raise CodexStabilityProfileError("metrics must be a non-empty list.")
    metrics = tuple(_metric_definition(item, index=index) for index, item in enumerate(metrics_raw))
    metric_ids = tuple(metric.metric_id for metric in metrics)
    if metric_ids != CODEX_STABILITY_METRIC_IDS:
        raise CodexStabilityProfileError(
            "metrics must use the canonical ordered ids: "
            + ", ".join(CODEX_STABILITY_METRIC_IDS)
        )
    return CodexStabilityProfile(
        schema_version=CODEX_STABILITY_PROFILE_SCHEMA_VERSION,
        profile_id=_stable_id(raw.get("profile_id"), context="profile_id"),
        scenario_id=_required_string(scenario.get("id"), context="scenario.id"),
        scenario_path=_required_string(scenario.get("path"), context="scenario.path"),
        runtime_id=_required_string(scenario.get("runtime_id"), context="scenario.runtime_id"),
        representative_task_id=_required_string(
            scenario.get("representative_task_id"), context="scenario.representative_task_id"
        ),
        work_item=_required_string(scenario.get("work_item"), context="scenario.work_item"),
        target_repository=_required_string(
            scenario.get("target_repository"), context="scenario.target_repository"
        ),
        target_revision=_revision(
            scenario.get("target_revision"), context="scenario.target_revision"
        ),
        stage_start=_required_string(scenario.get("stage_start"), context="scenario.stage_start"),
        stage_end=_required_string(scenario.get("stage_end"), context="scenario.stage_end"),
        execution_mode=_required_string(
            runtime_config.get("execution_mode"), context="runtime_config.execution_mode"
        ),
        command_source=_required_string(
            runtime_config.get("command_source"), context="runtime_config.command_source"
        ),
        model=_required_string(runtime_config.get("model"), context="runtime_config.model"),
        reasoning_effort=_required_string(
            runtime_config.get("reasoning_effort"), context="runtime_config.reasoning_effort"
        ),
        config_identity=_stable_id(
            runtime_config.get("config_identity"), context="runtime_config.config_identity"
        ),
        prompt_pack_root=_required_string(
            runtime_config.get("prompt_pack_root"), context="runtime_config.prompt_pack_root"
        ),
        minimum_repetitions=minimum_repetitions,
        metrics=metrics,
        evidence_schema=_evidence_schema(raw.get("evidence_schema")),
    )


def validate_codex_stability_profile(profile: CodexStabilityProfile) -> None:
    """Validate invariants that do not require loading the live scenario manifest."""

    if profile.runtime_id != "codex":
        raise CodexStabilityProfileError("Codex stability profiles must use runtime_id `codex`.")
    if profile.stage_start != "idea" or profile.stage_end != "qa":
        raise CodexStabilityProfileError(
            "Codex stability profiles must cover the full idea -> qa flow."
        )
    if profile.execution_mode != "native":
        raise CodexStabilityProfileError("Codex stability profiles must use native execution mode.")
    if profile.command_source != "native":
        raise CodexStabilityProfileError(
            "Codex stability profiles must use the native command source."
        )
    if not profile.target_repository.startswith("https://"):
        raise CodexStabilityProfileError("target_repository must be an HTTPS repository URL.")
    if not profile.scenario_path.endswith(".yaml") or Path(profile.scenario_path).is_absolute():
        raise CodexStabilityProfileError("scenario.path must be a repository-relative YAML path.")
    if profile.minimum_repetitions < 3:
        raise CodexStabilityProfileError("minimum_repetitions must be at least 3.")
    metric_sources = {
        artifact for metric in profile.metrics for artifact in metric.source_artifacts
    }
    if not metric_sources.issubset(
        set(profile.evidence_schema.required_artifacts)
        | set(profile.evidence_schema.conditional_artifacts)
    ):
        raise CodexStabilityProfileError(
            "Every metric source artifact must be declared by the evidence schema."
        )


def load_codex_stability_profile(
    path: Path = DEFAULT_CODEX_STABILITY_PROFILE_PATH,
) -> CodexStabilityProfile:
    """Load and validate the tracked Codex stability profile manifest."""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CodexStabilityProfileError(
            f"Unable to load Codex stability profile: {path}"
        ) from error
    profile = _parse_profile(raw)
    validate_codex_stability_profile(profile)
    return profile


def validate_profile_against_scenario(
    profile: CodexStabilityProfile,
    scenario_path: Path = DEFAULT_CODEX_STABILITY_SCENARIO_PATH,
) -> Scenario:
    """Verify that the profile remains pinned to the selected maintained scenario."""

    try:
        scenario = load_scenario(
            scenario_path, runtime_id=profile.runtime_id, workspace_root=Path(".aidd")
        )
    except (OSError, ValueError) as error:
        raise CodexStabilityProfileError(
            f"Unable to load profile scenario {scenario_path.as_posix()}: {error}"
        ) from error
    if not scenario.is_live:
        raise CodexStabilityProfileError("Codex stability profiles require a live scenario.")
    if scenario.scenario_id != profile.scenario_id:
        raise CodexStabilityProfileError(
            f"Profile scenario id {profile.scenario_id!r} does not match "
            f"{scenario.scenario_id!r}."
        )
    if profile.runtime_id not in scenario.runtime_targets:
        raise CodexStabilityProfileError("Profile runtime is not allowed by the scenario.")
    if scenario.repo.revision != profile.target_revision:
        raise CodexStabilityProfileError("Profile target revision does not match the scenario pin.")
    if scenario.repo.url != profile.target_repository:
        raise CodexStabilityProfileError("Profile target repository does not match the scenario.")
    if (
        scenario.run.stage_start != profile.stage_start
        or scenario.run.stage_end != profile.stage_end
    ):
        raise CodexStabilityProfileError("Profile stage scope does not match the scenario.")
    if scenario.feature_source is None or scenario.feature_source.mode != "authored-task-pool":
        raise CodexStabilityProfileError("Profile scenario must use an authored task pool.")
    if not scenario.feature_source.tasks:
        raise CodexStabilityProfileError("Profile scenario must declare a representative task.")
    if scenario.feature_source.tasks[0].task_id != profile.representative_task_id:
        raise CodexStabilityProfileError(
            "Profile representative task must match the first-listed authored task."
        )
    return scenario


def _metric_observations(
    raw: object,
    *,
    profile: CodexStabilityProfile,
) -> dict[str, dict[str, float]]:
    if not isinstance(raw, dict):
        raise CodexStabilityProfileError("metrics must be an object in repetition evidence.")
    if tuple(raw) != CODEX_STABILITY_METRIC_IDS:
        raise CodexStabilityProfileError(
            "repetition evidence metrics must use the canonical ordered ids."
        )
    observations: dict[str, dict[str, float]] = {}
    for definition in profile.metrics:
        payload = raw.get(definition.metric_id)
        if not isinstance(payload, dict):
            raise CodexStabilityProfileError(
                f"metrics.{definition.metric_id} must be an object."
            )
        numerator = payload.get("numerator")
        denominator = payload.get("denominator")
        value = payload.get("value")
        if not all(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            for item in (numerator, denominator, value)
        ):
            raise CodexStabilityProfileError(
                f"metrics.{definition.metric_id} numerator, denominator, and value must be numbers."
            )
        assert isinstance(numerator, (int, float)) and not isinstance(numerator, bool)
        assert isinstance(denominator, (int, float)) and not isinstance(denominator, bool)
        assert isinstance(value, (int, float)) and not isinstance(value, bool)
        numeric_values = (float(numerator), float(denominator), float(value))
        if not all(math.isfinite(item) and item >= 0 for item in numeric_values):
            raise CodexStabilityProfileError(
                f"metrics.{definition.metric_id} values must be finite and non-negative."
            )
        if numeric_values[1] <= 0:
            raise CodexStabilityProfileError(
                f"metrics.{definition.metric_id}.denominator must be positive."
            )
        if definition.kind == "rate" and not 0 <= numeric_values[2] <= 1:
            raise CodexStabilityProfileError(
                f"metrics.{definition.metric_id}.value must be between 0 and 1 for a rate."
            )
        expected = numeric_values[0] / numeric_values[1]
        if not math.isclose(numeric_values[2], expected, rel_tol=1e-9, abs_tol=1e-9):
            raise CodexStabilityProfileError(
                f"metrics.{definition.metric_id}.value must equal numerator / denominator."
            )
        observations[definition.metric_id] = {
            "numerator": numeric_values[0],
            "denominator": numeric_values[1],
            "value": numeric_values[2],
        }
    return observations


def validate_repetition_evidence(
    profile: CodexStabilityProfile,
    raw: object,
) -> CodexRepetitionEvidence:
    """Validate one future repetition against the profile-owned evidence schema."""

    if not isinstance(raw, dict):
        raise CodexStabilityProfileError("repetition evidence must be an object.")
    if raw.get("schema_version") != profile.schema_version:
        raise CodexStabilityProfileError(
            "repetition evidence schema version does not match profile."
        )
    repetition_id = _stable_id(raw.get("repetition_id"), context="repetition_id")
    scenario_id = _required_string(raw.get("scenario_id"), context="scenario_id")
    run_id = _required_string(raw.get("run_id"), context="run_id")
    runtime_id = _required_string(raw.get("runtime_id"), context="runtime_id")
    target_revision = _revision(raw.get("target_revision"), context="target_revision")
    config_identity = _stable_id(raw.get("config_identity"), context="config_identity")
    status = _required_string(raw.get("status"), context="status")
    stage_scope = raw.get("stage_scope")
    attempts = raw.get("attempts")
    evidence_links = raw.get("evidence_links")
    boundary = raw.get("first_failure_boundary")
    if status not in _ALLOWED_STATUSES:
        raise CodexStabilityProfileError(f"status is unsupported: {status!r}.")
    if scenario_id != profile.scenario_id or runtime_id != profile.runtime_id:
        raise CodexStabilityProfileError(
            "repetition evidence scenario/runtime does not match profile."
        )
    if target_revision != profile.target_revision or config_identity != profile.config_identity:
        raise CodexStabilityProfileError("repetition evidence pin does not match profile.")
    if (
        not isinstance(stage_scope, list)
        or len(stage_scope) != 2
        or tuple(stage_scope) != (profile.stage_start, profile.stage_end)
    ):
        raise CodexStabilityProfileError(
            "stage_scope must match the profile's idea -> qa scope."
        )
    if not isinstance(attempts, list) or not attempts or not all(
        isinstance(item, dict) for item in attempts
    ):
        raise CodexStabilityProfileError("attempts must be a non-empty list of objects.")
    if not isinstance(evidence_links, list) or not evidence_links:
        raise CodexStabilityProfileError("evidence_links must be a non-empty list.")
    normalized_links = _string_tuple(evidence_links, context="evidence_links")
    missing_artifacts = tuple(
        artifact
        for artifact in profile.evidence_schema.required_artifacts
        if not any(
            (
                link == artifact
                if "<" not in artifact
                else link.startswith(artifact.split("<", 1)[0])
                and link.endswith(artifact.split(">", 1)[1])
            )
            for link in normalized_links
        )
    )
    if missing_artifacts:
        raise CodexStabilityProfileError(
            "evidence_links is missing required artifacts: " + ", ".join(missing_artifacts)
        )
    if not isinstance(boundary, dict):
        raise CodexStabilityProfileError("first_failure_boundary must be an object.")
    normalized_boundary = {
        key: _required_string(boundary.get(key), context=f"first_failure_boundary.{key}")
        for key in ("category", "signal", "source")
    }
    metrics = _metric_observations(raw.get("metrics"), profile=profile)
    return CodexRepetitionEvidence(
        schema_version=profile.schema_version,
        repetition_id=repetition_id,
        scenario_id=scenario_id,
        run_id=run_id,
        runtime_id=runtime_id,
        target_revision=target_revision,
        config_identity=config_identity,
        status=status,  # type: ignore[arg-type]
        stage_scope=(profile.stage_start, profile.stage_end),
        attempts=tuple(dict(item) for item in attempts),
        evidence_links=normalized_links,
        first_failure_boundary=normalized_boundary,
        metrics=metrics,
    )


__all__ = [
    "CODEX_STABILITY_CONDITIONAL_ARTIFACTS",
    "CODEX_STABILITY_METRIC_IDS",
    "CODEX_STABILITY_PROFILE_SCHEMA_VERSION",
    "CODEX_STABILITY_REQUIRED_ARTIFACTS",
    "CODEX_STABILITY_REQUIRED_EVIDENCE_FIELDS",
    "CodexEvidenceSchema",
    "CodexMetricDefinition",
    "CodexRepetitionEvidence",
    "CodexRepetitionStatus",
    "CodexStabilityProfile",
    "CodexStabilityProfileError",
    "DEFAULT_CODEX_STABILITY_PROFILE_PATH",
    "DEFAULT_CODEX_STABILITY_PROFILE_ROOT",
    "DEFAULT_CODEX_STABILITY_SCENARIO_PATH",
    "load_codex_stability_profile",
    "validate_codex_stability_profile",
    "validate_profile_against_scenario",
    "validate_repetition_evidence",
]

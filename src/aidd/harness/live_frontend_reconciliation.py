from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

FrontendProbeClassification = Literal["pass", "fail", "skipped"]
FrontendReconciliationStatus = Literal[
    "provisional-pass",
    "provisional-fail",
    "superseded-transition",
    "confirmed-fail",
]
EffectiveFrontendClassification = Literal["pass", "fail", "skipped"]


@dataclass(frozen=True, slots=True)
class FrontendCheckpointReconciliation:
    running_observed: bool
    running_classification: FrontendProbeClassification
    post_stage_classification: FrontendProbeClassification
    durable_stage_status: str | None
    stage_classification: str
    running_status: FrontendReconciliationStatus | None
    post_stage_status: FrontendReconciliationStatus
    effective_classification: EffectiveFrontendClassification
    decisive_reason: str

    def to_payload(self) -> dict[str, object]:
        return {
            "running_observed": self.running_observed,
            "running_classification": self.running_classification,
            "post_stage_classification": self.post_stage_classification,
            "durable_stage_status": self.durable_stage_status,
            "stage_classification": self.stage_classification,
            "running_status": self.running_status,
            "post_stage_status": self.post_stage_status,
            "effective_classification": self.effective_classification,
            "decisive_reason": self.decisive_reason,
        }


def normalize_frontend_probe_classification(
    classification: str,
) -> FrontendProbeClassification:
    if classification in {"pass", "fail", "skipped"}:
        return cast(FrontendProbeClassification, classification)
    return "fail"


def provisional_frontend_status(
    *,
    phase: str,
    classification: FrontendProbeClassification,
) -> FrontendReconciliationStatus:
    if phase != "running-stage":
        if classification == "fail":
            return "confirmed-fail"
        if classification == "skipped":
            return "superseded-transition"
        return "provisional-pass"
    if classification == "fail":
        return "provisional-fail"
    if classification == "skipped":
        return "superseded-transition"
    return "provisional-pass"


def reconcile_frontend_checkpoints(
    *,
    running_observed: bool,
    running_classification: FrontendProbeClassification,
    post_stage_classification: FrontendProbeClassification,
    durable_stage_status: str | None,
    stage_classification: str,
) -> FrontendCheckpointReconciliation:
    post_status = provisional_frontend_status(
        phase="post-stage",
        classification=post_stage_classification,
    )
    if post_stage_classification == "fail":
        return FrontendCheckpointReconciliation(
            running_observed=running_observed,
            running_classification=running_classification,
            post_stage_classification=post_stage_classification,
            durable_stage_status=durable_stage_status,
            stage_classification=stage_classification,
            running_status=("confirmed-fail" if running_observed else None),
            post_stage_status="confirmed-fail",
            effective_classification="fail",
            decisive_reason=(
                "The post-stage checkpoint confirmed that the frontend outage persisted "
                "after durable stage completion."
            ),
        )

    if (
        running_observed
        and running_classification == "fail"
        and post_stage_classification == "pass"
    ):
        if stage_classification == "pass" and durable_stage_status == "succeeded":
            return FrontendCheckpointReconciliation(
                running_observed=True,
                running_classification=running_classification,
                post_stage_classification=post_stage_classification,
                durable_stage_status=durable_stage_status,
                stage_classification=stage_classification,
                running_status="superseded-transition",
                post_stage_status=post_status,
                effective_classification="pass",
                decisive_reason=(
                    "The provisional running-stage failure was superseded by durable "
                    "stage success and a passing post-stage checkpoint."
                ),
            )
        return FrontendCheckpointReconciliation(
            running_observed=True,
            running_classification=running_classification,
            post_stage_classification=post_stage_classification,
            durable_stage_status=durable_stage_status,
            stage_classification=stage_classification,
            running_status="provisional-fail",
            post_stage_status=post_status,
            effective_classification="fail",
            decisive_reason=(
                "A passing post-stage probe cannot supersede the running-stage failure "
                "without matching durable stage success."
            ),
        )

    if post_stage_classification == "pass":
        running_status: FrontendReconciliationStatus | None = None
        if running_observed:
            running_status = (
                "superseded-transition"
                if running_classification == "skipped"
                else "provisional-pass"
            )
        return FrontendCheckpointReconciliation(
            running_observed=running_observed,
            running_classification=running_classification,
            post_stage_classification=post_stage_classification,
            durable_stage_status=durable_stage_status,
            stage_classification=stage_classification,
            running_status=running_status,
            post_stage_status=post_status,
            effective_classification="pass",
            decisive_reason=(
                "The post-stage checkpoint passed after the durable stage transition."
            ),
        )

    if running_observed and running_classification == "fail":
        return FrontendCheckpointReconciliation(
            running_observed=True,
            running_classification=running_classification,
            post_stage_classification=post_stage_classification,
            durable_stage_status=durable_stage_status,
            stage_classification=stage_classification,
            running_status="provisional-fail",
            post_stage_status=post_status,
            effective_classification="fail",
            decisive_reason=(
                "The provisional running-stage failure was not followed by a decisive "
                "post-stage checkpoint."
            ),
        )

    effective: EffectiveFrontendClassification = (
        "pass"
        if running_observed and running_classification == "pass"
        else "skipped"
    )
    return FrontendCheckpointReconciliation(
        running_observed=running_observed,
        running_classification=running_classification,
        post_stage_classification=post_stage_classification,
        durable_stage_status=durable_stage_status,
        stage_classification=stage_classification,
        running_status=("provisional-pass" if effective == "pass" else None),
        post_stage_status=post_status,
        effective_classification=effective,
        decisive_reason=(
            "No decisive post-stage frontend failure was observed."
        ),
    )


def apply_frontend_checkpoint_reconciliation(
    *,
    checkpoint_payload: dict[str, object],
    flow_steps: list[dict[str, Any]],
    stage: str,
    stage_run_id: str,
    reconciled_at_utc: str,
    reconciliation: FrontendCheckpointReconciliation,
) -> dict[str, object]:
    raw_checkpoints = checkpoint_payload.get("checkpoints")
    checkpoints = raw_checkpoints if isinstance(raw_checkpoints, list) else []
    if not isinstance(raw_checkpoints, list):
        checkpoint_payload["checkpoints"] = checkpoints
    running_checkpoint: dict[str, object] | None = None
    post_stage_checkpoint: dict[str, object] | None = None
    for raw_checkpoint in reversed(checkpoints):
        if (
            not isinstance(raw_checkpoint, dict)
            or raw_checkpoint.get("stage") != stage
            or raw_checkpoint.get("stage_run_id") != stage_run_id
        ):
            continue
        phase = raw_checkpoint.get("phase")
        if phase == "post-stage" and post_stage_checkpoint is None:
            post_stage_checkpoint = cast(dict[str, object], raw_checkpoint)
        elif phase == "running-stage" and running_checkpoint is None:
            running_checkpoint = cast(dict[str, object], raw_checkpoint)
        if post_stage_checkpoint is not None and (
            running_checkpoint is not None or not reconciliation.running_observed
        ):
            break

    reconciliation_payload = {
        "schema_version": 1,
        "stage": stage,
        "stage_run_id": stage_run_id,
        "reconciled_at_utc": reconciled_at_utc,
        **reconciliation.to_payload(),
    }
    if running_checkpoint is not None and reconciliation.running_status is not None:
        running_checkpoint["reconciliation_status"] = reconciliation.running_status
        running_checkpoint["reconciled_at_utc"] = reconciled_at_utc
        running_checkpoint["effective_classification"] = (
            reconciliation.effective_classification
        )
    if post_stage_checkpoint is not None:
        post_stage_checkpoint["reconciliation_status"] = (
            reconciliation.post_stage_status
        )
        post_stage_checkpoint["reconciled_at_utc"] = reconciled_at_utc
        post_stage_checkpoint["effective_classification"] = (
            reconciliation.effective_classification
        )

    raw_reconciliations = checkpoint_payload.get("reconciliations")
    reconciliations = (
        raw_reconciliations if isinstance(raw_reconciliations, list) else []
    )
    if not isinstance(raw_reconciliations, list):
        checkpoint_payload["reconciliations"] = reconciliations
    reconciliations.append(reconciliation_payload)

    statuses = {
        "frontend-running-stage-checkpoint": reconciliation.running_status,
        "frontend-checkpoint": reconciliation.post_stage_status,
    }
    for action, status in statuses.items():
        if status is None:
            continue
        step = next(
            (
                candidate
                for candidate in reversed(flow_steps)
                if candidate.get("action") == action
                and candidate.get("stage") == stage
            ),
            None,
        )
        if step is None:
            continue
        raw_details = step.get("details")
        details = (
            dict(cast(dict[str, object], raw_details))
            if isinstance(raw_details, dict)
            else {}
        )
        details["reconciliation_status"] = status
        details["effective_classification"] = reconciliation.effective_classification
        details["frontend_reconciliation"] = reconciliation_payload
        step["details"] = details
    return reconciliation_payload


def is_nondecisive_provisional_frontend_step(step: dict[str, Any]) -> bool:
    if step.get("action") != "frontend-running-stage-checkpoint":
        return False
    raw_details = step.get("details")
    if not isinstance(raw_details, dict):
        return False
    return raw_details.get("reconciliation_status") in {
        "provisional-pass",
        "provisional-fail",
        "superseded-transition",
    }


__all__ = [
    "EffectiveFrontendClassification",
    "FrontendCheckpointReconciliation",
    "FrontendProbeClassification",
    "FrontendReconciliationStatus",
    "apply_frontend_checkpoint_reconciliation",
    "is_nondecisive_provisional_frontend_step",
    "normalize_frontend_probe_classification",
    "provisional_frontend_status",
    "reconcile_frontend_checkpoints",
]

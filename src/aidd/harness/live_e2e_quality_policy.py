from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

QualityFlowDecision = Literal[
    "continue",
    "continue-with-risk",
    "stop-not-counted",
    "operator-intervention",
    "request-remediation",
]
QualityPolicyAction = Literal["continue", "await-review", "stop", "remediate"]
QualityFindingDisposition = Literal["must-fix", "accepted-risk", "advisory"]


@dataclass(frozen=True, slots=True)
class QualityFindingInput:
    finding_id: str
    disposition: QualityFindingDisposition


@dataclass(frozen=True, slots=True)
class StageQualityAuditInput:
    stage: str
    stage_run_id: str
    audit_exists: bool
    flow_decision: QualityFlowDecision | None
    remediation_already_handled: bool = False
    findings: tuple[QualityFindingInput, ...] = ()


@dataclass(frozen=True, slots=True)
class QualityPolicyDecision:
    verdict: Literal["acceptable", "conditional", "rejected", "incomplete"]
    progression: bool
    action: QualityPolicyAction
    reason: str
    stage: str | None = None
    stage_run_id: str | None = None


def evaluate_quality_policy(
    audits: tuple[StageQualityAuditInput, ...],
) -> QualityPolicyDecision:
    for audit in audits:
        if not audit.audit_exists:
            return _decision_for(
                audit,
                verdict="incomplete",
                action="await-review",
                reason="stage quality audit file is missing",
            )
        if audit.flow_decision is None:
            return _decision_for(
                audit,
                verdict="incomplete",
                action="await-review",
                reason="stage quality audit is missing a valid Flow decision",
            )
        if any(finding.disposition == "must-fix" for finding in audit.findings):
            return _decision_for(
                audit,
                verdict="rejected",
                action="await-review",
                reason="stage quality audit contains an active must-fix finding",
            )
        if audit.flow_decision == "stop-not-counted":
            return _decision_for(
                audit,
                verdict="rejected",
                action="stop",
                reason="launching operator-agent stage audit chose stop-not-counted",
            )
        if audit.flow_decision == "operator-intervention":
            return _decision_for(
                audit,
                verdict="conditional",
                action="await-review",
                reason="stage quality audit requested operator intervention",
            )
        if audit.flow_decision == "request-remediation":
            if audit.remediation_already_handled:
                continue
            return _decision_for(
                audit,
                verdict="rejected",
                action="remediate",
                reason="stage quality audit requested remediation",
            )

    accepted_risks = any(
        finding.disposition == "accepted-risk"
        for audit in audits
        for finding in audit.findings
    )
    conditional = accepted_risks or any(
        audit.flow_decision == "continue-with-risk" for audit in audits
    )
    return QualityPolicyDecision(
        verdict="conditional" if conditional else "acceptable",
        progression=True,
        action="continue",
        reason=(
            "all stage quality audits permit conditional progression"
            if conditional
            else "all stage quality audits permit progression"
        ),
    )


def _decision_for(
    audit: StageQualityAuditInput,
    *,
    verdict: Literal["acceptable", "conditional", "rejected", "incomplete"],
    action: QualityPolicyAction,
    reason: str,
) -> QualityPolicyDecision:
    return QualityPolicyDecision(
        verdict=verdict,
        progression=action == "continue",
        action=action,
        reason=reason,
        stage=audit.stage,
        stage_run_id=audit.stage_run_id,
    )


__all__ = [
    "QualityFlowDecision",
    "QualityFindingInput",
    "QualityPolicyDecision",
    "StageQualityAuditInput",
    "evaluate_quality_policy",
]

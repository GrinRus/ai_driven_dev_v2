from __future__ import annotations

import ast
from pathlib import Path

import pytest

from aidd.harness import live_e2e_quality_policy
from aidd.harness.live_e2e_quality_policy import (
    QualityFindingInput,
    StageQualityAuditInput,
    evaluate_quality_policy,
)


@pytest.mark.parametrize(
    ("audit", "action", "verdict", "progression"),
    [
        (
            StageQualityAuditInput("idea", "stage-1", False, None),
            "await-review",
            "incomplete",
            False,
        ),
        (
            StageQualityAuditInput("idea", "stage-1", True, None),
            "await-review",
            "incomplete",
            False,
        ),
        (
            StageQualityAuditInput("review", "stage-6", True, "stop-not-counted"),
            "stop",
            "rejected",
            False,
        ),
        (
            StageQualityAuditInput("review", "stage-6", True, "operator-intervention"),
            "await-review",
            "conditional",
            False,
        ),
        (
            StageQualityAuditInput("review", "stage-6", True, "request-remediation"),
            "remediate",
            "rejected",
            False,
        ),
        (
            StageQualityAuditInput("qa", "stage-7", True, "continue"),
            "continue",
            "acceptable",
            True,
        ),
        (
            StageQualityAuditInput(
                "qa",
                "stage-7",
                True,
                "continue-with-risk",
                findings=(QualityFindingInput("RV-1", "accepted-risk"),),
            ),
            "continue",
            "conditional",
            True,
        ),
    ],
)
def test_quality_policy_decision_matrix(
    audit: StageQualityAuditInput,
    action: str,
    verdict: str,
    progression: bool,
) -> None:
    decision = evaluate_quality_policy((audit,))

    assert decision.action == action
    assert decision.verdict == verdict
    assert decision.progression is progression


def test_handled_remediation_allows_progression() -> None:
    decision = evaluate_quality_policy(
        (
            StageQualityAuditInput(
                "review",
                "stage-6",
                True,
                "request-remediation",
                remediation_already_handled=True,
            ),
        )
    )

    assert decision.action == "continue"
    assert decision.progression is True


def test_quality_policy_has_no_impure_dependencies() -> None:
    source_path = Path(live_e2e_quality_policy.__file__)
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in module.body
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".", maxsplit=1)[0]
        for node in module.body
        if isinstance(node, ast.ImportFrom)
    }

    assert imported_roots.isdisjoint({"os", "pathlib", "subprocess", "time", "urllib"})

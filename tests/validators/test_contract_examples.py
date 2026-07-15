from __future__ import annotations

import re
from pathlib import Path

import pytest

from aidd.core.stage_registry import load_stage_manifest, resolve_required_input_documents
from aidd.core.workspace import init_workspace, seed_work_item_context
from aidd.validators.cross_document import validate_cross_document_consistency
from aidd.validators.protocol import parse_validator_report
from aidd.validators.semantic import validate_semantic_outputs
from aidd.validators.structural import (
    validate_required_document_existence,
    validate_required_sections,
)

WORK_ITEM = "WI-EXAMPLE"
EXAMPLES_ROOT = Path("contracts/examples")
SUCCESS_EXAMPLES = {
    "idea": EXAMPLES_ROOT / "idea",
    "research": EXAMPLES_ROOT / "research" / "answered",
    "plan": EXAMPLES_ROOT / "plan" / "valid",
    "review-spec": EXAMPLES_ROOT / "review-spec",
    "tasklist": EXAMPLES_ROOT / "tasklist",
    "implement": EXAMPLES_ROOT / "implement" / "success",
    "review": EXAMPLES_ROOT / "review" / "success",
    "qa": EXAMPLES_ROOT / "qa" / "success",
}
WORK_ITEM_PATTERN = re.compile(r"WI-[A-Z-]+-EXAMPLE")


def _copy_example_document(source: Path, destination: Path) -> None:
    text = WORK_ITEM_PATTERN.sub(WORK_ITEM, source.read_text(encoding="utf-8"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def _materialize_example(
    *,
    tmp_path: Path,
    stage: str,
    example_root: Path,
) -> tuple[Path, Path]:
    workspace_root = tmp_path / ".aidd"
    init_workspace(workspace_root, WORK_ITEM)
    seed_work_item_context(
        root=workspace_root,
        work_item=WORK_ITEM,
        request_text="Validate the canonical contract example.",
        project_root=tmp_path,
    )

    for required_input in resolve_required_input_documents(
        stage=stage,
        work_item=WORK_ITEM,
        workspace_root=workspace_root,
    ):
        if required_input.exists() or required_input.parent.name != "output":
            continue
        upstream_stage = required_input.parent.parent.name
        source = SUCCESS_EXAMPLES[upstream_stage] / required_input.name
        _copy_example_document(source, required_input)

    stage_root = workspace_root / "workitems" / WORK_ITEM / "stages" / stage
    for source in example_root.glob("*.md"):
        _copy_example_document(source, stage_root / source.name)
    return workspace_root, stage_root


def _validate_example(*, workspace_root: Path, stage: str) -> tuple[str, ...]:
    load_stage_manifest(stage=stage)
    findings = (
        *validate_required_document_existence(
            stage=stage,
            work_item=WORK_ITEM,
            workspace_root=workspace_root,
        ),
        *validate_required_sections(
            stage=stage,
            work_item=WORK_ITEM,
            workspace_root=workspace_root,
        ),
        *validate_semantic_outputs(
            stage=stage,
            work_item=WORK_ITEM,
            workspace_root=workspace_root,
        ),
        *validate_cross_document_consistency(
            stage=stage,
            work_item=WORK_ITEM,
            workspace_root=workspace_root,
        ),
    )
    return tuple(finding.code for finding in findings)


@pytest.mark.parametrize(("stage", "example_root"), SUCCESS_EXAMPLES.items())
def test_success_examples_pass_the_full_validator_stack(
    tmp_path: Path,
    stage: str,
    example_root: Path,
) -> None:
    workspace_root, stage_root = _materialize_example(
        tmp_path=tmp_path,
        stage=stage,
        example_root=example_root,
    )

    assert _validate_example(workspace_root=workspace_root, stage=stage) == ()

    report = parse_validator_report(
        (stage_root / "validator-report.md").read_text(encoding="utf-8")
    )
    assert report.verdict == "pass"
    assert report.findings == ()
    total_issues = report.field("total_issues")
    assert total_issues is not None
    assert total_issues.value == "0"


@pytest.mark.parametrize(
    ("stage", "example_root", "expected_codes"),
    (
        (
            "research",
            EXAMPLES_ROOT / "research" / "unresolved",
            ("CROSS-BLOCKING-UNANSWERED",),
        ),
        (
            "plan",
            EXAMPLES_ROOT / "plan" / "invalid",
            (
                "SEM-INCOMPLETE-SECTION",
                "SEM-INCOMPLETE-SECTION",
                "CROSS-BLOCKING-UNANSWERED",
            ),
        ),
        (
            "implement",
            EXAMPLES_ROOT / "implement" / "repair-needed",
            (
                "SEM-INCOMPLETE-EXECUTION-SUMMARY",
                "SEM-INCOMPLETE-EXECUTION-SUMMARY",
                "SEM-MISSING-DIFF-EVIDENCE",
                "SEM-UNVERIFIABLE-CHECK-CLAIM",
            ),
        ),
        (
            "review",
            EXAMPLES_ROOT / "review" / "repair-needed",
            (
                "SEM-INCOMPLETE-SECTION",
                "SEM-INCOMPLETE-SECTION",
                "SEM-INCOMPLETE-SECTION",
                "SEM-UNSUPPORTED-CLAIM",
            ),
        ),
        (
            "qa",
            EXAMPLES_ROOT / "qa" / "repair-needed",
            (
                "SEM-RISK-UNDERREPORT",
                "SEM-RISK-UNDERREPORT",
                "SEM-MISSING-EVIDENCE-REF",
                "SEM-UNSUPPORTED-VERDICT",
            ),
        ),
    ),
)
def test_invalid_and_repair_examples_emit_exact_codes(
    tmp_path: Path,
    stage: str,
    example_root: Path,
    expected_codes: tuple[str, ...],
) -> None:
    workspace_root, stage_root = _materialize_example(
        tmp_path=tmp_path,
        stage=stage,
        example_root=example_root,
    )

    assert _validate_example(workspace_root=workspace_root, stage=stage) == expected_codes

    report = parse_validator_report(
        (stage_root / "validator-report.md").read_text(encoding="utf-8")
    )
    assert report.verdict == "fail"
    assert tuple(finding.code for finding in report.findings) == expected_codes
    total_issues = report.field("total_issues")
    assert total_issues is not None
    assert total_issues.value == str(len(expected_codes))

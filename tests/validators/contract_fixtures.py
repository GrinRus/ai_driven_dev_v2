from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aidd.core.stage_models import StageOutputDiscovery
from aidd.core.stage_outputs import run_structural_validation_after_output_discovery
from aidd.core.stage_registry import (
    resolve_expected_output_documents,
    resolve_required_input_documents,
)
from aidd.core.workspace import init_workspace, seed_work_item_context
from aidd.validators.models import ValidationFinding
from aidd.validators.protocol import ValidatorReportReadModel, parse_validator_report

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

_WORK_ITEM_PATTERN = re.compile(r"WI-[A-Z-]+-EXAMPLE")


@dataclass(frozen=True, slots=True)
class ContractFixtureResult:
    workspace_root: Path
    stage_root: Path
    findings: tuple[ValidationFinding, ...]
    source_report: ValidatorReportReadModel
    generated_report: ValidatorReportReadModel

    @property
    def finding_codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)


def _copy_example_document(source: Path, destination: Path) -> None:
    text = _WORK_ITEM_PATTERN.sub(WORK_ITEM, source.read_text(encoding="utf-8"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def run_contract_fixture(
    *,
    tmp_path: Path,
    stage: str,
    example_root: Path,
) -> ContractFixtureResult:
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
        _copy_example_document(
            SUCCESS_EXAMPLES[upstream_stage] / required_input.name,
            required_input,
        )

    stage_root = workspace_root / "workitems" / WORK_ITEM / "stages" / stage
    for source in example_root.glob("*.md"):
        _copy_example_document(source, stage_root / source.name)

    report_path = stage_root / "validator-report.md"
    source_report = parse_validator_report(report_path.read_text(encoding="utf-8"))
    expected_documents = resolve_expected_output_documents(
        stage=stage,
        work_item=WORK_ITEM,
        workspace_root=workspace_root,
    )
    discovered_documents = tuple(path for path in expected_documents if path.exists())
    validation = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=StageOutputDiscovery(
            stage=stage,
            work_item=WORK_ITEM,
            run_id="run-001",
            attempt_number=1,
            expected_markdown_documents=expected_documents,
            discovered_markdown_documents=discovered_documents,
            missing_markdown_documents=tuple(
                path for path in expected_documents if not path.exists()
            ),
        ),
    )
    generated_report = parse_validator_report(report_path.read_text(encoding="utf-8"))
    return ContractFixtureResult(
        workspace_root=workspace_root,
        stage_root=stage_root,
        findings=validation.findings,
        source_report=source_report,
        generated_report=generated_report,
    )

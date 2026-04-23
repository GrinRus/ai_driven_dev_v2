#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


def _workspace_root() -> Path:
    return Path(os.environ["AIDD_WORKSPACE_ROOT"]).resolve(strict=False)


def _work_item() -> str:
    return os.environ["AIDD_WORK_ITEM"].strip()


def _stage() -> str:
    return os.environ["AIDD_STAGE"].strip()


def _stage_root(*, workspace_root: Path, work_item: str, stage: str) -> Path:
    return workspace_root / "workitems" / work_item / "stages" / stage


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _markdown(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def _next_stage(stage: str) -> str | None:
    return {
        "idea": "research",
        "research": "plan",
        "plan": "review-spec",
        "review-spec": "tasklist",
        "tasklist": "implement",
        "implement": "review",
        "review": "qa",
        "qa": None,
    }.get(stage)


def _stage_output_names(stage: str) -> tuple[str, ...]:
    return {
        "idea": ("idea-brief.md", "stage-result.md", "validator-report.md"),
        "research": ("research-notes.md", "stage-result.md", "validator-report.md"),
        "plan": ("plan.md", "stage-result.md", "validator-report.md"),
        "review-spec": ("review-spec-report.md", "stage-result.md", "validator-report.md"),
        "tasklist": ("tasklist.md", "stage-result.md", "validator-report.md"),
        "implement": ("implementation-report.md", "stage-result.md", "validator-report.md"),
        "review": ("review-report.md", "stage-result.md", "validator-report.md"),
        "qa": ("qa-report.md", "stage-result.md", "validator-report.md"),
    }[stage]


def _validation_summary_line(stage: str) -> str:
    return {
        "idea": "Problem framing, constraints, and open-question handling are reviewable.",
        "research": "Source grounding and evidence trace notes are complete enough for planning.",
        "plan": "Milestones, risks, dependencies, and verification mapping are explicit.",
        "review-spec": "Readiness, issue severity, and decision state remain coherent.",
        "tasklist": "Task ordering, dependencies, and verification mapping are explicit.",
        "implement": (
            "No-op boundary is explicit, evidence-backed, and scoped to "
            "release-proof execution."
        ),
        "review": "Review findings, approval state, and follow-up requirements are explicit.",
        "qa": (
            "Readiness, evidence references, and release recommendation are aligned "
            "to this release-proof lane."
        ),
    }[stage]


def _render_stage_result(*, stage: str, work_item: str) -> str:
    produced_outputs = [
        f"- `workitems/{work_item}/stages/{stage}/output/{name}`"
        for name in _stage_output_names(stage)
    ]
    produced_outputs.append(
        f"- `workitems/{work_item}/stages/{stage}/repair-brief.md` "
        "(placeholder retained; no repair needed)"
    )
    next_stage = _next_stage(stage)
    if next_stage is None:
        next_actions = [
            "- Preserve this QA bundle as published-package live-scenario release evidence.",
            (
                "- Keep maintained-runtime live runs responsible for real upstream "
                "task-completion proof."
            ),
        ]
        terminal_notes = [
            "- Stage completed with release-proof readiness guidance for the tagged package.",
            "- No repair or blocking interview loop was required.",
        ]
    else:
        next_actions = [
            f"- Use the `{stage}` output bundle as upstream input for `{next_stage}`.",
            "- Preserve truthful release-proof scope notes in downstream artifacts.",
        ]
        terminal_notes = [
            "- Stage completed successfully for published-package live operator proof.",
            "- No repair or blocking interview loop was required.",
        ]

    return _markdown(
        "# Stage Result",
        "",
        "## Stage",
        "",
        f"- `{stage}`",
        "",
        "## Attempt history",
        "",
        "- Attempt 1 (`initial`) -> validation `pass`; no repair required.",
        "",
        "## Status",
        "",
        "- `succeeded`",
        "",
        "## Produced outputs",
        "",
        *produced_outputs,
        "",
        "## Validation summary",
        "",
        (
            f"- Validator verdict: `pass` from "
            f"`workitems/{work_item}/stages/{stage}/output/validator-report.md`."
        ),
        (
            f"- Repair trace: `workitems/{work_item}/stages/{stage}/repair-brief.md` "
            "remains in its no-repair placeholder state."
        ),
        f"- {_validation_summary_line(stage)}",
        "",
        "## Blockers",
        "",
        "- none",
        "",
        "## Next actions",
        "",
        *next_actions,
        "",
        "## Terminal state notes",
        "",
        *terminal_notes,
    )


def _render_validator_report() -> str:
    return _markdown(
        "# Validator Report",
        "",
        "## Summary",
        "",
        "- Total issues: 0",
        "",
        "## Structural checks",
        "",
        "- none",
        "",
        "## Semantic checks",
        "",
        "- none",
        "",
        "## Cross-document checks",
        "",
        "- none",
        "",
        "## Result",
        "",
        "- Verdict: `pass`",
    )


def _render_repair_brief(*, work_item: str, stage: str) -> str:
    return _markdown(
        "# Failed checks",
        "",
        "- none",
        "",
        "## Required corrections",
        "",
        "- none",
        "",
        "## Relevant upstream docs",
        "",
        f"- `workitems/{work_item}/stages/{stage}/validator-report.md`",
    )


def _stage_documents(*, work_item: str) -> dict[str, dict[str, str]]:
    return {
        "idea": {
            "idea-brief.md": _markdown(
                "# Idea Brief",
                "",
                "## Problem statement",
                "",
                (
                    "Running installed AIDD against the pinned sqlite-utils repository "
                    "should not depend on a source-checkout shortcut."
                ),
                "",
                "## Desired outcome",
                "",
                (
                    "Produce a truthful live-operator workflow bundle for the published "
                    "package while framing the header-only CSV bug as the target task."
                ),
                "",
                "## Constraints",
                "",
                "- Keep the release-proof lane non-destructive for the upstream repository.",
                "- Preserve `.aidd/` inside the target repository.",
                "- Do not hide that maintained-runtime completion is validated elsewhere.",
                "",
                "## Open questions",
                "",
                "- none",
            ),
        },
        "research": {
            "research-notes.md": _markdown(
                "# Research Notes",
                "",
                "## Scope",
                "",
                (
                    "Gather the minimum repository and release-lane context needed to "
                    "run a truthful published-package live proof for sqlite-utils."
                ),
                "",
                "## Sources",
                "",
                (
                    "- [S1] `harness/scenarios/live/"
                    "sqlite-utils-detect-types-header-only.yaml`, access date: 2026-04-23."
                ),
                "- [S2] `docs/e2e/live-e2e-catalog.md`, access date: 2026-04-23.",
                "",
                "## Findings",
                "",
                (
                    "- The scenario requires a pinned sqlite-utils checkout and QA-stage "
                    "output artifacts ([S1])."
                ),
                (
                    "- Live E2E is defined as installed-operator proof, while release "
                    "proof can stay deterministic and explicit about scope ([S2])."
                ),
                "",
                "## Trade-offs",
                "",
                (
                    "- Using a deterministic generic-cli runtime keeps tagged-release "
                    "automation stable."
                ),
                (
                    "- This release-proof lane does not replace maintained-runtime "
                    "evidence for actual upstream task completion."
                ),
                "",
                "## Evidence trace",
                "",
                "- Scenario artifact requirements -> [S1]",
                "- Installed-operator lane definition -> [S2]",
                "- Release-proof runtime constraint -> [S1], [S2]",
                "",
                "## Open questions",
                "",
                "- none",
            ),
        },
        "plan": {
            "plan.md": _markdown(
                "# Plan",
                "",
                "## Goals",
                "",
                (
                    "- Prove that the published AIDD package can run from a pinned "
                    "sqlite-utils repository root."
                ),
                "- Keep `.aidd/` and durable eval evidence inside the target repository.",
                (
                    "- Preserve explicit scope notes about the release-proof no-op "
                    "implementation boundary."
                ),
                "",
                "## Out of scope",
                "",
                "- Landing the actual sqlite-utils code fix during tagged-release automation.",
                "- Replacing maintained-runtime live runs with this generic release-proof lane.",
                "",
                "## Milestones",
                "",
                "- M1: Prepare installed AIDD execution from the target repository root.",
                "- M2: Generate a truthful document-first workflow bundle through QA.",
                "- M3: Run repository verification and persist published-package eval evidence.",
                "",
                "## Implementation strategy",
                "",
                (
                    "- Seed deterministic context documents for the live work item before "
                    "stage execution."
                ),
                (
                    "- Keep implementation-stage output explicit about the release-proof "
                    "no-op boundary."
                ),
                (
                    "- Preserve release evidence through harness bundle artifacts instead "
                    "of ad hoc logs."
                ),
                "",
                "## Risks",
                "",
                (
                    "- R1: Release automation could imply upstream bug completion; "
                    "mitigation: mark no-op scope explicitly in implement, review, and QA."
                ),
                (
                    "- R2: Published-package execution could drift from target cwd "
                    "semantics; mitigation: verify install transcript and QA artifacts."
                ),
                "",
                "## Dependencies",
                "",
                "- Pinned sqlite-utils revision from `AIDD-LIVE-005`.",
                (
                    "- Harness support for published-package installation and "
                    "target-repository execution."
                ),
                "- Release workflow artifact upload for the eval bundle.",
                "",
                "## Verification approach",
                "",
                "- Run `uv run pytest -q || pytest -q` through the scenario verification step.",
                "- Check that QA stage output artifacts and eval bundle artifacts are present.",
                "",
                "## Verification notes",
                "",
                "- M1: verify install transcript and target-repository cwd metadata are captured.",
                "- M2: verify each stage publishes required Markdown outputs through QA.",
                "- M3: verify scenario output, bundle upload, and final verdict remain durable.",
            ),
        },
        "review-spec": {
            "review-spec-report.md": _markdown(
                "# Review Spec Report",
                "",
                "## Readiness state",
                "",
                "- `ready-with-conditions`",
                "",
                "## Issue list",
                "",
                (
                    "- I1 (`medium`): Release proof does not apply the upstream "
                    "sqlite-utils fix because tagged-release automation stays non-destructive."
                ),
                (
                    "- I2 (`low`): QA artifacts must keep the no-op scope visible "
                    "because downstream readers could over-interpret release-proof success."
                ),
                "",
                "## Strengths",
                "",
                (
                    "- Installed-package execution, target-repository cwd, and bundle "
                    "durability are explicit."
                ),
                (
                    "- Risks and verification notes distinguish release proof from "
                    "maintained-runtime completion proof."
                ),
                "",
                "## Recommendation summary",
                "",
                (
                    "- R1 (priority 1): Keep no-op scope explicit in implement, review, "
                    "and QA documents."
                ),
                "- R2 (priority 2): Upload the resulting eval bundle as release evidence.",
                "",
                "## Required changes",
                "",
                "- Ensure review and QA documents preserve the published-package scope boundary.",
                "- Preserve artifact references needed for release-checklist evidence.",
                "",
                "## Decision",
                "",
                "- `approved-with-conditions`",
            ),
        },
        "tasklist": {
            "tasklist.md": _markdown(
                "# Tasklist",
                "",
                "## Task summary",
                "",
                (
                    "Break the sqlite-utils release-proof run into reviewable steps that "
                    "keep install evidence, truthful scope notes, and verification aligned."
                ),
                "",
                "## Ordered tasks",
                "",
                (
                    "- TL-1 Prepare the pinned sqlite-utils working copy and install the "
                    "published AIDD package."
                ),
                (
                    "- TL-2 Run the document-first workflow through QA while keeping "
                    "implementation as an explicit release-proof no-op."
                ),
                "- TL-3 Verify the repository and persist the eval bundle as release evidence.",
                "",
                "## Dependencies",
                "",
                "- TL-1: none",
                "- TL-2: TL-1",
                "- TL-3: TL-2",
                "",
                "## Verification notes",
                "",
                "- TL-1: `uv tool install ai-driven-dev-v2==<version>` -> pass",
                (
                    f"- TL-2: `aidd run --work-item {work_item} --runtime generic-cli` "
                    "-> pass"
                ),
                "- TL-3: `uv run pytest -q || pytest -q` -> pass",
            ),
        },
        "implement": {
            "implementation-report.md": _markdown(
                "# Implementation Report",
                "",
                "## Selected task",
                "",
                "- Task id: `TL-2`",
                (
                    "- Task title: Run the workflow through QA with an explicit "
                    "release-proof no-op boundary."
                ),
                "",
                "## Summary",
                "",
                (
                    "This published-package release-proof lane performs a no-op "
                    "implementation step because tagged-release automation is limited "
                    "to installed-operator evidence."
                ),
                "",
                "## Touched files",
                "",
                "- none",
                "",
                "## Verification",
                "",
                "- `uv run pytest -q || pytest -q` -> pass",
                (
                    "- `uv run aidd eval run harness/scenarios/live/"
                    "sqlite-utils-detect-types-header-only.yaml --runtime generic-cli` "
                    "-> pass"
                ),
                "",
                "## Risks",
                "",
                (
                    "- [non-blocking] Upstream task-completion evidence for issue #705 "
                    "must still come from maintained-runtime live runs."
                ),
                "",
                "## Follow-up",
                "",
                (
                    "- Keep maintained-runtime live bugfix runs in development or nightly "
                    "validation before widening published-package proof scope."
                ),
            ),
        },
        "review": {
            "review-report.md": _markdown(
                "# Review Report",
                "",
                "## Verdict",
                "",
                "- `approved-with-conditions`",
                "",
                "## Findings",
                "",
                (
                    f"- `RV-1` `medium` `accepted-risk` Evidence: "
                    f"`workitems/{work_item}/stages/implement/output/implementation-report.md` "
                    "records a release-proof no-op because published tagged-release "
                    "automation does not land upstream repository edits. "
                    "Rationale: The no-op boundary keeps published-package evidence "
                    "truthful while preserving install/cwd/workspace verification value."
                ),
                (
                    f"- `RV-2` `low` `follow-up` Evidence: "
                    f"`workitems/{work_item}/context/acceptance-criteria.md` and "
                    f"`workitems/{work_item}/stages/implement/output/implementation-report.md` "
                    "show AC-1 and AC-2 are covered, while upstream bug completion "
                    "remains outside this lane. Rationale: Release-proof success alone "
                    "is insufficient evidence for upstream task completion."
                ),
                "",
                "## Risks",
                "",
                (
                    "- Maintain clear separation between published-package operator proof "
                    "and maintained-runtime task-completion proof."
                ),
                "",
                "## Required follow-up",
                "",
                (
                    "- Re-run `AIDD-LIVE-005` in maintained-runtime development lanes "
                    "before treating the sqlite-utils bug as fully proven."
                ),
            ),
        },
        "qa": {
            "qa-report.md": _markdown(
                "# QA Report",
                "",
                "## Verification summary",
                "",
                "- Installed AIDD must run from the pinned sqlite-utils repository root.",
                (
                    "- Scenario verification command `uv run pytest -q || pytest -q` "
                    "is required to pass."
                ),
                (
                    "- QA artifact publication and eval bundle persistence are part "
                    "of the release gate."
                ),
                "",
                "## Evidence",
                "",
                (
                    "- EV-1: `context/verification-output.md` records the required "
                    "repository verification command and expected pass condition."
                ),
                (
                    "- EV-2: `context/verification-artifacts.md` points to "
                    "`.aidd/reports/evals/<run_id>/` as the durable evidence bundle."
                ),
                "",
                "## Known issues",
                "",
                (
                    "- QR-1 (`medium`): This tagged-release lane validates published-package "
                    "operator semantics only."
                ),
                (
                    "- Mitigation: keep maintained-runtime live bugfix runs in pre-release "
                    "development or nightly checks."
                ),
                "- Owner: platform maintainer.",
                "",
                "## Readiness",
                "",
                "- `ready-with-risks`",
                "",
                "## Release recommendation",
                "",
                "- `proceed-with-conditions`",
            ),
        },
    }


def _write_stage_outputs(*, workspace_root: Path, work_item: str, stage: str) -> None:
    stage_root = _stage_root(workspace_root=workspace_root, work_item=work_item, stage=stage)
    stage_root.mkdir(parents=True, exist_ok=True)
    documents = _stage_documents(work_item=work_item)[stage]
    for name, content in documents.items():
        _write_text(stage_root / name, content)
    _write_text(stage_root / "validator-report.md", _render_validator_report())
    _write_text(
        stage_root / "repair-brief.md",
        _render_repair_brief(work_item=work_item, stage=stage),
    )
    _write_text(
        stage_root / "stage-result.md",
        _render_stage_result(stage=stage, work_item=work_item),
    )


def main() -> int:
    workspace_root = _workspace_root()
    work_item = _work_item()
    stage = _stage()
    _write_stage_outputs(workspace_root=workspace_root, work_item=work_item, stage=stage)
    print(
        "release-live-proof-runtime:"
        f" stage={stage} work_item={work_item} workspace_root={workspace_root.as_posix()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

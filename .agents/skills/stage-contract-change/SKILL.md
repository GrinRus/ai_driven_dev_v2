---
name: stage-contract-change
description: Change AIDD stage/document contracts, validation, or repair with aligned artifact ownership, active prompts, and deterministic regression evidence.
---

# stage-contract-change

Use for an accepted change to stage inputs/outputs or validator/repair semantics.
If the request is a review or proposed design, report the affected surfaces without editing.

## Trace the change

Read the relevant `contracts/stages/` and `contracts/documents/` files, including
[artifact ownership](../../../contracts/documents/ownership-matrix.md), and the accepted
local task. Use [the ownership/check map](../../../docs/agent-development.md) to identify
applicable instructions and affected scenarios.

| Surface | What must agree |
| --- | --- |
| `src/aidd/core/stage_registry.py` | Separate runtime-authored, AIDD-generated, interview/control, and published output projections; published compatibility views do not grant runtime write authority. |
| `src/aidd/core/stage_preparation.py`, `src/aidd/adapters/native_prompt.py` | Actual attempt request, declared context, allowed output paths, and shared native wrapper. |
| `src/aidd/cli/support.py`, `src/aidd/core/repair.py`, `src/aidd/core/stage_runner.py` | Attempt-mode selection, generated repair instructions, bootstrap reconciliation, and canonical lifecycle records; blocked completion needs a controlled blocking question, not unparsed prose. |
| `src/aidd/validators/`, `src/aidd/core/stage_validation.py`, `src/aidd/application/` | Structural/semantic/cross-document validation, lifecycle reconciliation, canonical publication, and repair findings. |
| `prompt-packs/stages/<stage>/` | Active system, run, repair, and intervention instructions; legacy `prompt-packs/<stage>/` files remain compatibility pointers. |
| Contract examples and `harness/scenarios/` | Valid outputs, relevant invalid/repair cases, and observable progression/stop behavior. |

Update the contract before code. AIDD owns canonical `stage-result.md`,
`validator-report.md`, and `repair-brief.md`; the runtime produces substantive
Markdown and follows the interview protocol. Preserve raw unexpected runtime copies
as evidence without treating them as canonical state. Never widen output authority
implicitly or turn runtime-specific flags into core semantics.

## Implement and verify the smallest coherent change

1. Update only the accepted contract variable group, downstream validator/ownership
   behavior, active prompt instructions, and relevant examples/scenario/grader.
2. Check each affected stage in initial, repair, and operator-intervention modes.
   For implementation, include selected-task context, task-local evidence, and aggregate
   finalization when the changed contract touches those paths. Inspect the composed
   runtime request, not just the separate prompt files.
3. Run focused validator/contract tests plus relevant stage preparation/runner and native
   request tests. Useful entrypoints are `tests/core/test_stage_registry.py`,
   `tests/core/test_stage_preparation.py`, `tests/core/test_stage_runner.py`,
   `tests/adapters/test_native_prompt.py`, `tests/test_contract_registry.py`, and
   matching `tests/validators/` cases. Select only the affected tests.
4. Run `tests/test_prompt_quality.py`, `tests/test_docs_consistency.py`, and
   `tests/test_packaging_resources.py` for changed active packs. Review semantic diffs
   before updating `tests/fixtures/active_prompt_pack_hashes.json`; do not refresh
   hashes merely to silence an unexplained mismatch.
5. Inspect deterministic evidence that valid substantive outputs still progress and
   invalid/missing outputs still repair or stop. Keep runtime logs and canonical reports.

Report changed contract behavior, affected stage/mode combinations, scenario/test
results, reviewed prompt hashes, preserved compatibility, and unverified paths.

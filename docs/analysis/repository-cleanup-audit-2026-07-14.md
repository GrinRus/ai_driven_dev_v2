# Repository Cleanup and Refactoring Audit — 2026-07-14

## Executive summary

This incremental audit reviews the repository at
`30cc8d68be9966acad61cb41ded1eaa6b3458911` after Wave 35. It reuses, rather than
duplicates, the findings already mapped from
`docs/analysis/codebase-audit-2026-07-10.md`.

The repository is healthy at the configured baseline: locked sync, Ruff, configured
mypy, documentation consistency, and all `1,358` tests pass. The full suite is slow
(`1,082.10s`) and the review found two new P1 correctness gaps:

1. generic CLI/UI stage and remediation entrypoints can publish one-shot `implement`
   success without the Wave 35 task ledger, dependency loop, task diff/scope evidence,
   or aggregate finalization;
2. Implement Review resolves `allowed-write-scope.md` from a noncanonical stage-local
   path, while validation and task execution use the canonical work-item context path.

The main refactoring issue is an application-layer inversion: task execution,
publication, and finalization policy live in `aidd.cli.task`, and both workflow and UI
import that CLI module. The main cleanup issues are an incomplete black-box harness
split, repeated full-repository task snapshots, deterministic tests that rely on real
sleep/network access, release scripts outside the mypy gate, one obsolete generated
inventory, a dormant documentation dependency extra, and planning documents that had
become a second historical journal.

No production code was changed by this audit. Findings were converted into bounded
roadmap tasks, broad pre-existing tasks were split, Wave 35 was reopened for the P1
correction, and the active backlog was rebuilt as a short execution queue.

## Scope and evidence

The review covered product Python, release scripts, packaged frontend assets, tests,
contracts, prompts, harness/eval modules, architecture/product documents, roadmap, and
backlog. It combined repository and symbol inventories, churn/hotspot review, import and
caller tracing, manual control-flow review, focused reproductions, and the configured
quality gates. Provider-authenticated live execution was not run.

The pre-existing untracked file
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md` was treated as user-owned and excluded
from audit edits.

| Baseline | Result |
| --- | --- |
| Product/test inventory | 56,855 product Python lines; 50,679 test Python lines |
| Symbol index | 310 files; 10,058 symbols; 39,988 references |
| Locked environment | `uv sync --locked --extra dev` passed |
| Configured lint | `uv run --extra dev ruff check .` passed |
| Configured typing | `uv run --extra dev python -m mypy src` passed for 170 files |
| Full test suite | `1,358 passed in 1,082.10s` |
| Documentation consistency | 30 focused checks passed after planning edits |
| Task-execution focus | 34 core/CLI task checks passed |
| Offline package smoke | failed because the test attempted to download `pydantic-core` |
| Release-script typing | two `no-any-return` errors in `scripts/release/preflight.py` |

The largest current hotspots are
`src/aidd/harness/live_e2e_black_box_orchestration.py` (8,663 lines),
`src/aidd/cli/ui.py` (3,392), the packaged next-flow JavaScript (2,911), and the new
task-execution area (`src/aidd/core/task_execution.py` plus `src/aidd/cli/task.py`, 1,533
lines combined). Of the full suite's 30 slowest tests, 28 are in the live black-box
module.

## Confirmed findings

### CORR-01 / ARCH-04 / REF-06 / TEST-07 — task-aware implementation can be bypassed (P1)

The product and architecture contracts require `implement` to execute one
dependency-ready task at a time and publish only after aggregate finalization. The main
workflow honors this through `execute_all_tasks`, but `aidd stage run implement`, stage
interaction, selected-stage UI execution, and UI remediation call the generic stage
runner. That runner can validate, publish, and persist `implement` as succeeded without
loading the task ledger.

Task orchestration also lives in `src/aidd/cli/task.py`: it owns attempt lifecycle,
dependency iteration, aggregate report validation/publication, stage status, and
finalization. `aidd.cli.run` and `aidd.cli.ui` import those CLI functions, contrary to the
documented `CLI/UI -> core` ownership direction. This split ownership is the direct
reason entrypoint behavior drifted.

Mapped work: `W35-E2-S8-T1..T6` first defines all entrypoint/remediation semantics,
moves policy into one typed core service, routes CLI and UI adapters through it, adds a
review/QA defense-in-depth gate, and supplies a provider-free conformance matrix.
`W35-E2-S9` decomposes the service only after parity is restored.

### BUG-13 / ARCH-06 — allowed-write scope has conflicting authorities (P1)

The canonical context resolver maps `context/allowed-write-scope.md` to
`workitems/<id>/context/allowed-write-scope.md`. Semantic evidence and task execution use
that path, but `repository_diff.py` reads
`workitems/<id>/stages/implement/context/allowed-write-scope.md`; the repository-diff
test fixture encodes the same shadow path. A disposable canonical-path reproduction
classified an in-scope change as `unknown`.

Three consumers also implement different backtick/path-prefix grammars, including
different behavior for a bare top-level directory such as `src`.

Mapped work: `W34-E7-S4-T1` introduces one typed parser/resolver/prefix predicate;
`W34-E7-S4-T2..T4` independently migrate validator, task diff, and repository
diff/Implement Review consumers through one parity matrix.

### REF-05 — the completed black-box module split is not authoritative (P2)

The completed Wave 25 evidence says subprocess and report helpers were extracted.
Currently `live_e2e_black_box_reports.py` has no production consumer, its helpers are
duplicated in orchestration, and `live_e2e_black_box_steps.py` contains an older reduced
`BlackBoxCommandResult` plus unused process helpers. The facade re-exports that stale
class while orchestration returns a different class.

This is not a new epic: existing `W34-E5-S4-T2` and `T4` were sharpened to make the
steps/reports modules authoritative, prove public class identity, retain atomic writes,
and delete duplicates.

### PERF-03 — task evidence repeatedly scans and copies the repository (P2)

A successful no-repair task performs at least four full tracked/untracked file
traversal-and-hash passes: baseline, validation, completion snapshot, and completion
diff. Every repair adds another scan. Global attempt evidence is also copied as a tree
and selected files are copied again into the task attempt.

Mapped work: `W35-E2-S10-T1` reuses one immutable repository snapshot per checkpoint;
`T2` fixes the evidence layout/reference contract, and `T3` migrates duplicate payloads
to that selected representation without hard links.

### TEST-04..TEST-06 — deterministic gates have avoidable time/network/type gaps (P2)

- The fake live runtime sleeps `0.75s` in every successful stage, although the delay was
  introduced for running-stage checkpoint coverage. This compounds across most of the
  54 black-box flow tests. `W34-E5-S4-T5` makes delay/barrier behavior opt-in.
- `tests/test_packaging_resources.py` runs an isolated no-cache `uv --with <wheel>`
  subprocess with no timeout. Under `UV_OFFLINE=1` it fails while downloading
  `pydantic-core`. `W34-E5-S3-T6` creates an offline bounded resource smoke; dependency
  resolution remains a release-channel concern.
- Configured mypy, Makefile, CI, release workflow, and README check only `src`.
  `mypy scripts` exposes two strict errors. `W34-E5-S3-T7` fixes them and makes
  `mypy src scripts` canonical.

### DEAD-02 / DEAD-06 / DEAD-07 — removable stale surface (P3)

- The pre-Wave-35 tasklist semantic helpers are no longer called; the canonical task
  plan parser owns the active grammar. Removal was folded into existing
  `W34-E1-S5-T4`, while `W34-E1-S4-T3` now asks only for the missing mixed-ID/coverage
  regression instead of a second parser.
- Root `manifest.txt` is an unconsumed initial-commit inventory containing cache,
  bytecode, and removed-file entries. `W34-E6-S1-T4` removes it. The explicitly marked
  historical `MANIFEST.md` remains.
- The `docs` optional extra retains MkDocs/Material and related lock/config surface, but
  there is no MkDocs configuration, build command, or publishing workflow.
  `W34-E6-S1-T5` removes the dormant extra rather than inventing a new docs product.

### MAINT-01 — automated dependency proposals need reconciliation (P3)

As of 2026-07-14 the repository has ten open Dependabot pull requests, including
updates for dependencies already mapped for removal and retained Python/Actions updates
that need current review. The dated source is the repository's
[Dependabot pull-request list](https://github.com/GrinRus/ai_driven_dev_v2/pulls?q=is%3Apr+is%3Aopen+author%3Aapp%2Fdependabot).

`W34-E6-S2` separates obsolete-proposal closure, retained Python dependency updates,
and GitHub Actions pin updates so each has one dominant verification path.

### PLAN-01 / PLAN-02 / ARCH-07 — planning and architecture drift (P2)

Before reconciliation, backlog contained 31 active items but 435 lines of historical
queue notes, about 85% of the file. Five `Soon` entries were already unblocked, roadmap
did not explicitly mark its current `Next`, and task status/disposition semantics were
ambiguous. A large docs-consistency test asserts completed Wave 26 history rather than
generic queue invariants. Target architecture also describes implemented frontend and
project-set work as planned, embeds completed Wave 29 browser policy, and advertises CLI
log modes not present in `US-06` or the product.

`W34-E8-S1-T1` was completed during this planning pass: backlog is now 114 lines with
one current reconciliation note. `W34-E8-S1-T2/T3` retain status normalization and
generic integrity tests; `W34-E8-S2` owns stable architecture/log wording. Wave 36's
browser decision task was split so documentation policy and dependency/lock changes are
reviewable separately.

## Plan and queue decisions

The roadmap gained 42 local task IDs; one planning cleanup task was completed
immediately and the remainder are accepted work. Existing broad tasks were also split
without replacing their stable IDs:

- validator registry rollout: `W34-E1-S3-T1`, then `T3..T6`, with examples in `T2`;
- process supervisor adoption: shared path `W34-E4-S1-T5`, Codex `T9`, Qwen `T10`;
- identifier adoption: workspace/work item `W34-E7-S2-T2`, run/attempt `T4`,
  overlay/CLI `T5`;
- browser driver decision versus dependency lock: `W36-E2-S1-T1` and `T4`;
- browser draft contract versus implementation: `W36-E6-S2-T1` and `T4`;
- browser CI, release, template, and manual evidence: `W36-E7-S2-T2..T5`.

The active backlog now contains 43 unique local tasks: 7 `Next`, 5 direct successors in
`Soon`, and 31 deliberately deferred entry tasks in `Parking lot`. All queue IDs resolve
to roadmap tasks. Immediate order is:

1. lock the task-aware implementation entrypoint contract (`W35-E2-S8-T1`);
2. establish canonical allowed-write-scope parsing (`W34-E7-S4-T1`);
3. continue the five already-ready Wave 34 correctness/reliability foundations;
4. promote only direct successors into `Soon`; keep Wave 36 behind Wave 34 foundations.

## User-story check

No product user-story edit is required now. The corrective work restores existing
`US-03`, `US-04`, `US-07`, `US-10`, `US-11`, `US-12`, and especially `US-13` behavior;
it does not add a new user capability. `US-06` changes only if a future decision adds
new user-selectable log modes rather than correcting architecture wording to match raw
logs and structured evidence already supported.

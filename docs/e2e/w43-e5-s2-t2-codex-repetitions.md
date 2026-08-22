# Wave 43 Codex repetitions (`W43-E5-S2-T2`)

## Scope

This report covers three fresh `AIDD-LIVE-007` repetitions with the pinned Codex profile from
[`w43-e5-s2-t1-codex-stability-profile.md`](./w43-e5-s2-t1-codex-stability-profile.md).
No Claude runtime, human session, or cross-runtime comparison was launched.

Profile identity:

- runtime: `codex`
- target: `honojs/hono@cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- model: `gpt-5.6-luna`, `reasoning_effort=high`
- scope: `idea -> qa`
- configuration: `codex-live-007-gpt-5-6-luna-high-v1`

## Repetition results

| Repetition | Run | Result | First decisive boundary |
| --- | --- | --- | --- |
| 01 | `eval-live-007-codex-20260822T083432Z` | `infra-fail` | `implement` terminated after runaway repository snapshot serialization while enumerating the prepared dependency tree |
| 02 | `eval-live-007-codex-20260822T090559Z` | `infra-fail` | `research` produced no first runtime event before the bounded stop |
| 03 | `eval-live-007-codex-20260822T091236Z` | `infra-fail` | `research` produced no first runtime event before the bounded stop |

Repetition 01 did complete `idea`, `research`, `plan`, `review-spec`, and `tasklist`; the target
Codex implementation produced the four expected source/test changes and its authored focused
verification passed (`235` Vitest tests and TypeScript). The harness then became CPU/memory
bound while serializing the ignored dependency inventory, so the run was not allowed to claim
review or QA completion. Repetitions 02 and 03 reached `idea` but stalled before a first
`research` runtime event. These are retained as `infra-fail`, not counted as product passes.

The local broad-status workaround used for repetitions 02 and 03 excluded ignored dependency
files from the agent's diagnostic listing; it did not alter the target source or the pinned
scenario. It did not resolve the Codex service stall.

## Metric verdict

The nine profile metrics are structurally recorded in
[`repetitions.json`](../tests/fixtures/w43-e5-s2-t2-codex-stability/repetitions.json), but all
three repetitions are `infra-fail`. Metric numerators/denominators are therefore diagnostic
sentinels and are excluded from a stability claim. The aggregate verdict is **indeterminate —
Codex infrastructure blocked the required clean comparison**. No initial-pass, repair, resume,
tasklist-compliance, or extension-success rate is presented as a product-quality result.

## Evidence inventory

Durable bundles are retained under `.aidd/reports/evals/`:

- `eval-live-007-codex-20260822T083432Z`
- `eval-live-007-codex-20260822T090559Z`
- `eval-live-007-codex-20260822T091236Z`

Each repetition has install/readiness metadata, feature selection, flow state, runtime log,
stage timing, log analysis, repair history, target workspace evidence, verification transcript,
grader, verdict, and a task-flow checkpoint. The checkpoints for the early-stop repetitions
explicitly set finalization and Review eligibility to false.

## Follow-up

`W43-E5-S2-T2` cannot support a Codex stability/regression claim until the Codex service stall
and the broad repository-snapshot memory blow-up are resolved and the same pinned lane can
complete three fresh runs. The parked cross-runtime task (`W43-E5-S2-T3`) remains out of scope.

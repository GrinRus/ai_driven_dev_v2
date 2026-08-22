# Wave 43 Codex Stability Profile

`W43-E5-S2-T1` defines the comparison contract for the Codex-only repetition lane. It is a
profile and evidence validator, not a provider run: no credentials are needed to load it and
no live runtime is launched by this task.

## Pinned profile

- Profile: `w43-e5-s2-codex-stability-v1`
- Scenario: `AIDD-LIVE-007`
- Repository: `https://github.com/honojs/hono`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Authored task: `TASK-LIVE-HONO-NON-ERROR-THROW`
- Work item: `WI-LIVE-HONO-SMOKE`
- Runtime: `codex`, native command and native execution mode
- Model configuration: `gpt-5.6-luna`, `reasoning_effort=high`
- Minimum repetitions: `3`

The machine-readable source is
`tests/fixtures/w43-e5-s2-t1-codex-stability/codex-stability-profile.json`. The loader verifies
that the profile still matches the live manifest's repository pin, first-listed authored task,
full `idea -> qa` scope, and Codex runtime target. A revision or task drift fails closed before
any repetition is compared.

## Metric vocabulary

Every repetition reports the same numerator, denominator, value, direction, and source-artifact
shape. Rates are bounded to `[0, 1]`; ratios may exceed `1` (for example, findings per root
cause). The profile intentionally does not choose a pass threshold; `W43-E5-S2-T2` records
per-metric verdicts after fresh runs.

| Metric | Formula | Direction |
| --- | --- | --- |
| `initial-pass-rate` | initial passes / repetitions | higher is better |
| `first-repair-recovery` | first-repair recoveries / validation failures | higher is better |
| `exhaustion` | exhausted repetitions / repetitions | lower is better |
| `findings-per-root-cause` | located findings / distinct root causes | lower is better |
| `false-budget-consumption` | false-budget attempts / automatic repair attempts | lower is better |
| `interview-resume` | successful resumes / resume attempts | higher is better |
| `tasklist-compliance` | compliant tasklists / tasklist runs | higher is better |
| `extension-success` | successful extensions / eligible extensions | higher is better |
| `intervention-rate` | operator interventions / repetitions | lower is better |

## Evidence contract

Each repetition must retain install/readiness and feature-selection provenance, runtime logs,
stage audits, timing and first-failure analysis, repair history, target verification, the
task-aware checkpoint, and the execution verdict. `runtime.jsonl`, `events.jsonl`, question and
answer documents, and frontend checkpoints are conditional artifacts: they are retained when
the run emits or needs them, but their absence does not create a synthetic success.

The validator requires the same identity fields for every repetition: scenario, run, runtime,
target revision, config identity, stage scope, attempts, evidence links, first decisive boundary,
and all nine metric observations. It accepts `pass`, `fail`, `blocked`, and `infra-fail` so a
missing Codex environment remains an explicit blocker rather than a counted clean repetition.

## Verification and handoff

```bash
uv run --extra dev pytest -q tests/evals/test_codex_stability_profile.py
uv run --extra dev python -m mypy src/aidd/evals/codex_stability_profile.py tests/evals/test_codex_stability_profile.py
```

`W43-E5-S2-T2` must use this profile for at least three fresh Codex repetitions with one pinned
scenario/configuration. It must preserve per-run logs and checkpoints, classify each metric, and
write an aggregate stability/regression or environment-blocked report. This profile does not
authorize a Claude run, a human session, or the parked cross-runtime comparison.

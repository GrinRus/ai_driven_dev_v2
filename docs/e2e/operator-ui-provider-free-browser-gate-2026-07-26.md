# Provider-Free Packaged UI Browser Gate — 2026-07-26

This record contains two failed `provider-free-browser-pass-v1` attempts and the final
accepted rerun for the source-installed Document & Evidence Studio. It contains no provider
credentials, temporary project paths, runtime logs, generated `.aidd/` state, or
human-observation metrics. No product or browser fixture change was made during any gate run.

## Candidate

- Evidence schema: `provider-free-browser-pass-v1`
- AIDD version: `0.1.0a16.dev0`
- Source commit: `5bbe2c94ea4855dceafe1f594a0c816b68e0a516`
- Source tree: `2c04a6618456f2753d664d4b86fd3481c767f37b`
- Browser: `Chromium 149.0.7827.55`
- Fixture family: `browser_tests.state_fixtures` at the source commit above
- Viewports: `320x568, 390x844, 768x1024, 1280x900, 1440x900`
- Network boundary: provider-free, disposable loopback UI only

## Executions

1. The four previously characterized race cases reported `3 passed, 1 failed` in
   `110.05s`. The `320x568` intervention case received an OK response, observed exactly
   one `POST /api/stage/interact`, and found exactly one matching durable request, but
   timed out after five seconds waiting for the matching browser draft to disappear.
2. The complete intervention and terminal families then passed `24/24`
   (`14/14` intervention and `10/10` terminal) in `315.64s`.
3. `uv run --extra dev python scripts/run_packaged_ui_scenarios.py` discovered and
   executed the exact ordered registry `W36-E7-S1-T1..T12`. Eleven journeys passed.
   `W36-E7-S1-T10` reported `13 passed, 1 failed`: the `1440x900` intervention case
   reproduced the same post-success draft-clear timeout after one OK POST and one
   matching durable request. Across the registry families, `78/79` tests passed.
4. `uv run --extra dev pytest -q browser_tests` reported `186 passed, 1 failed` in
   `3630.59s`. The independent `1440x900` History case timed out after 30 seconds in
   initial `page.goto(..., wait_until="networkidle")`, before its durable History
   surface assertion.

The packaged runner's discovered and executed journey ids were byte-for-byte equal:

```text
W36-E7-S1-T1, W36-E7-S1-T2, W36-E7-S1-T3, W36-E7-S1-T4,
W36-E7-S1-T5, W36-E7-S1-T6, W36-E7-S1-T7, W36-E7-S1-T8,
W36-E7-S1-T9, W36-E7-S1-T10, W36-E7-S1-T11, W36-E7-S1-T12
```

Its only failed journey id was `W36-E7-S1-T10`.

## First Decisive Findings

### Intervention draft cleanup

The server-authoritative mutation succeeded before the failure: the response was OK,
the request observer saw one POST, and the canonical request file contained the submitted
text. Only `readOperatorDraft(interventionDraftIdentity()) === null` remained false.
The first decisive boundary is therefore matching browser-draft cleanup after a successful
immutable intervention descriptor/durable winner, not mutation loss or duplicate dispatch.
It reproduced at both the smallest and largest viewports.

### History navigation readiness

The History failure occurred before rendered-history assertions, while global
`networkidle` remained unsatisfied. The first decisive boundary is the test's navigation
synchronization strategy: it does not use the shared bounded server-authoritative
work-item/History surface wait. No evidence implicated retained-run mutation or History
render semantics.

## Diagnostics And Cleanup

- No additional console, page, request, accessibility, geometry, overflow, or cleanup
  failure class appeared in the four-case, family, packaged, or full-suite results.
- The intervention failures preserved exactly-one durable mutation evidence.
- The History failure did not reach the test's final diagnostics assertion.
- Browser pages, contexts, servers, and disposable fixture roots were released by their
  context-managed harnesses; no source-tree browser residue was created.

## Result

- Overall result: `failed`
- Blockers:
  - intervention draft cleanup is not reliably tied to the submitted immutable identity
    after a successful durable mutation;
  - History navigation still relies on global `networkidle` instead of bounded
    server-authoritative surface readiness.
- Next action: implement each blocker as an independent roadmap task, then rerun this
  complete gate from a new clean source commit. `W36-E7-S4-T37` remains blocked.

## Post-T56/T57 Rerun

The gate was restarted from source commit
`cff519bed6bef47b94a645d2deb17d182e214187` and tree
`120a3be1468f13b7983b39d58310ce2dd645029c` after the two original blockers were
implemented independently.

The four-case historical matrix stopped the gate at `2 passed, 2 failed` in `121.25s`.
The `320x568` and `1280x900` intervention cases again observed an OK response, one POST,
one canonical request file, and the correct request text, but the submitted browser draft
was not cleared within the 30-second bounded wait. Per the no-fix `T36` rule, the family,
packaged, and full-suite layers were not run on this invalid candidate.

`T56` removed current-route identity drift and moved matching cleanup ahead of ordinary
job polling, but the UI still has no authoritative request winner in the accepted POST
envelope. Dashboard readback can remain unavailable while the runtime job owns execution,
so cleanup is still coupled to a later asynchronous read. A separate follow-up must make
the already-persisted operator-request identity available at the job-acceptance boundary;
the full `T36` matrix must then restart from another clean commit.

## Accepted Post-T58 Rerun

The complete gate passed from clean source commit
`17213af21607e4c1873dc635b256c11248b107d0` and tree
`601aeb7fd980ece7f4dc938b4b46482914fc52e7` with Chromium `149.0.7827.55`.
The only worktree entry was the pre-existing excluded user snapshot
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`.

1. The exact four-case historical matrix passed `4/4` in `57.23s`.
2. The complete intervention and terminal journey families passed `24/24` in `258.04s`.
3. `uv run --extra dev python scripts/run_packaged_ui_scenarios.py` executed all twelve
   discovered journey IDs with byte-for-byte identical discovered/executed lists,
   `failed_ids=[]`, and `79/79` passing tests. Historical intervention journey
   `W36-E7-S1-T10` passed `14/14`.
4. `uv run --extra dev pytest -q browser_tests` passed `188/188` in `2617.84s`.

All five viewports completed with clean console, page, request, overflow, accessibility,
and bounded process-cleanup diagnostics. The accepted run created no source-tree browser
residue and did not modify the candidate under test.

Final result: `passed`. The exact-SHA readiness task `W36-E7-S4-T37` may now consume
commit `17213af21607e4c1873dc635b256c11248b107d0` as its browser-proven predecessor.

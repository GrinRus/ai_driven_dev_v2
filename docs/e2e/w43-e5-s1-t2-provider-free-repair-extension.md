# W43-E5-S1-T2 provider-free repair-extension scenarios

This deterministic lane proves the one-shot `repair-extension` protocol without provider
credentials. It drives the production core preflight, durable grant, attempt-index, stage-result,
and repair-history paths in temporary workspaces; it does not run a runtime process.

## Run

```bash
uv run --extra dev python -m aidd.evals.repair_extension_scenarios \
  --output .aidd/reports/w43-e5-s1-t2-repair-extension.json
```

The same lane is available as manual deterministic scenario `AIDD-DETERMINISTIC-006` in
`harness/scenarios/deterministic/w43-repair-extension-scenarios.yaml`.

## Coverage

The suite covers eight terminal paths:

- one explicitly authorized extension that succeeds;
- one explicitly authorized extension that fails again;
- manual-fix prevalidation that finalizes without a runtime attempt;
- stale evidence and downstream-success guards;
- second-grant rejection;
- Request Change kept separate from the repair-extension action;
- immutable prior attempt indexes and append-only repair history.

Every result records exact grant content, grant count, attempt modes, automatic repair accounting,
repair-history triggers, report lineage, raw evidence, downstream artifact preservation, and the
automatic-loop verdict. The suite fails closed when a disabled state has no literal reason, more
than one grant exists, an automatic follow-up attempt appears, required lineage/evidence is
missing, or a prior attempt artifact changes.

The original automatic budget remains `2` in every scenario; the fourth attempt is explicitly
`repair-extension` and is never counted as an automatic repair. The suite is provider-free and
does not replace the later Codex repetition lane.
